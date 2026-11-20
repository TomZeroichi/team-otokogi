"""TEAM狭気 - small private shared scorekeeper.

Run: uvicorn app:app --host 0.0.0.0 --port 8000
Data: SQLite file at DATA_DIR/kyoki.sqlite3 (mount a persistent disk in production).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

BASE_DIR = Path(__file__).resolve().parent
MAX_AMOUNT = 100_000_000
SESSION_DAYS = 90
RATE_GUARD = defaultdict(deque)
RATE_LOCK = threading.Lock()


def now_utc():
    return datetime.now(timezone.utc)


def utc_stamp():
    return now_utc().isoformat(timespec="seconds")


def password_hash(pin: str, salt: bytes | None = None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(pin.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + ':' + digest.hex()


def password_check(pin: str, stored: str):
    try:
        salt_hex, stored_hash = stored.split(':', 1)
        digest = hashlib.scrypt(pin.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest, bytes.fromhex(stored_hash))
    except (ValueError, TypeError):
        return False


def guard_rate(ip: str, category: str, max_calls=16, window=15 * 60):
    key = (ip, category)
    current = time.monotonic()
    with RATE_LOCK:
        queue = RATE_GUARD[key]
        while queue and queue[0] < current - window:
            queue.popleft()
        if len(queue) >= max_calls:
            raise HTTPException(429, "試行回数が多すぎます。しばらくしてからお試しください。")
        queue.append(current)


class Identity(BaseModel):
    nickname: str = Field(min_length=1, max_length=24)
    pin: str = Field(pattern=r"^[0-9]{6}$")

    @field_validator('nickname')
    @classmethod
    def clean_name(cls, name: str):
        name = name.strip()
        if not name or any(ord(ch) < 32 for ch in name):
            raise ValueError("名前を入力してください")
        return name


class CreateGroup(Identity):
    name: str = Field(default="TEAM狭気", min_length=1, max_length=40)


class JoinGroup(Identity):
    invite: str = Field(min_length=20, max_length=128)


class ChooseMode(BaseModel):
    mode: Literal["otoko", "normal"]


class RoundData(BaseModel):
    event_date: date
    place: str = Field(default="", max_length=80)
    amount: int = Field(ge=1, le=MAX_AMOUNT)
    participants: list[int] = Field(min_length=2, max_length=60)
    winner_id: int
    loser_id: int
    note: str = Field(default="", max_length=500)
    historical_mode: Literal['otoko', 'normal'] | None = None

    @model_validator(mode='after')
    def check_round(self):
        if len(set(self.participants)) != len(self.participants):
            raise ValueError("参加者が重複しています")
        if self.winner_id == self.loser_id or self.winner_id not in self.participants or self.loser_id not in self.participants:
            raise ValueError("勝者と敗者を参加者から別々に選んでください")
        if self.event_date > date.today() + timedelta(days=1):
            raise ValueError("未来の日付は記録できません")
        return self


def create_app(database_path: str | None = None):
    app = FastAPI(title="TEAM狭気", docs_url=None, redoc_url=None)
    dbfile = Path(database_path) if database_path else Path(os.getenv('DATA_DIR', str(BASE_DIR / 'data'))) / 'kyoki.sqlite3'
    dbfile.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def db():
        con = sqlite3.connect(str(dbfile), timeout=15)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA busy_timeout=10000')
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    with db() as con:
        con.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                invite TEXT NOT NULL UNIQUE,
                next_mode TEXT CHECK(next_mode IS NULL OR next_mode IN ('otoko','normal')),
                next_decider_id INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                nickname TEXT NOT NULL COLLATE NOCASE,
                pin_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','member')),
                created_at TEXT NOT NULL,
                UNIQUE(group_id,nickname)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                event_date TEXT NOT NULL,
                place TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK(amount>0),
                mode TEXT NOT NULL CHECK(mode IN ('otoko','normal')),
                winner_id INTEGER NOT NULL REFERENCES members(id),
                loser_id INTEGER NOT NULL REFERENCES members(id),
                payer_id INTEGER NOT NULL REFERENCES members(id),
                note TEXT NOT NULL,
                is_historical INTEGER NOT NULL DEFAULT 0,
                recorded_by INTEGER NOT NULL REFERENCES members(id),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS round_participants (
                round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
                member_id INTEGER NOT NULL REFERENCES members(id),
                PRIMARY KEY(round_id,member_id)
            );
            CREATE INDEX IF NOT EXISTS idx_round_group ON rounds(group_id,event_date DESC,id DESC);
            CREATE INDEX IF NOT EXISTS idx_member_group ON members(group_id);
        ''')

    def client_ip(req: Request):
        return req.client.host if req.client else 'unknown'

    def add_session(con, response, member_id):
        raw = secrets.token_urlsafe(36)
        expiry = now_utc() + timedelta(days=SESSION_DAYS)
        con.execute('INSERT INTO sessions(token_hash,member_id,expires_at) VALUES (?,?,?)', (
            hashlib.sha256(raw.encode()).hexdigest(), member_id, expiry.isoformat()))
        response.set_cookie('kyoki_session', raw, max_age=SESSION_DAYS*86400, httponly=True,
            secure=os.getenv('COOKIE_SECURE','0') == '1', samesite='lax', path='/')

    def get_actor(con, raw: str | None):
        if not raw:
            raise HTTPException(401, 'ログインしてください')
        row = con.execute('''SELECT m.id, m.group_id, m.nickname, m.role, s.expires_at
            FROM sessions s JOIN members m ON s.member_id=m.id WHERE s.token_hash=?''',
            (hashlib.sha256(raw.encode()).hexdigest(),)).fetchone()
        if not row or row['expires_at'] < utc_stamp():
            raise HTTPException(401, 'ログインの有効期限が切れました')
        return row

    def check_members(con, group_id, ids):
        placeholders = ','.join('?' for _ in ids)
        count = con.execute(f'SELECT count(*) FROM members WHERE group_id=? AND id IN ({placeholders})',
            [group_id, *ids]).fetchone()[0]
        if count != len(ids):
            raise HTTPException(400, '参加者がグループ内に存在しません')

    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @app.get('/')
    def index():
        return FileResponse(BASE_DIR / 'static' / 'index.html', headers={'Cache-Control': 'no-store'})

    @app.get('/health')
    def health():
        return {'ok': True}

    @app.post('/api/groups')
    def create_group(body: CreateGroup, request: Request, response: Response):
        guard_rate(client_ip(request), 'group-create', 8)
        name = body.name.strip()
        if not name:
            raise HTTPException(400, 'グループ名を入力してください')
        invite = secrets.token_urlsafe(24)
        with db() as con:
            cur = con.execute('INSERT INTO groups(name,invite,created_at) VALUES(?,?,?)', (name, invite, utc_stamp()))
            group_id = cur.lastrowid
            cur = con.execute('''INSERT INTO members(group_id,nickname,pin_hash,role,created_at)
                VALUES(?,?,?,?,?)''', (group_id, body.nickname, password_hash(body.pin),'admin',utc_stamp()))
            member_id = cur.lastrowid
            con.execute('UPDATE groups SET next_decider_id=? WHERE id=?',(member_id,group_id))
            add_session(con,response,member_id)
        return {'ok': True, 'invite': invite}

    @app.post('/api/join')
    def join_group(body: JoinGroup, request: Request, response: Response):
        guard_rate(client_ip(request), 'join', 12)
        with db() as con:
            group = con.execute('SELECT * FROM groups WHERE invite=?',(body.invite,)).fetchone()
            if not group:
                raise HTTPException(404,'招待リンクが無効です')
            try:
                cur = con.execute('''INSERT INTO members(group_id,nickname,pin_hash,role,created_at)
                    VALUES(?,?,?,?,?)''',(group['id'],body.nickname,password_hash(body.pin),'member',utc_stamp()))
            except sqlite3.IntegrityError:
                raise HTTPException(409, 'その名前は登録済みです。「ログイン」を選んでください')
            add_session(con,response,cur.lastrowid)
        return {'ok': True}

    @app.post('/api/login')
    def login(body: JoinGroup, request: Request, response: Response):
        guard_rate(client_ip(request), 'login', 10)
        with db() as con:
            row=con.execute('''SELECT m.* FROM members m JOIN groups g ON g.id=m.group_id
                WHERE g.invite=? AND m.nickname=? COLLATE NOCASE''', (body.invite,body.nickname)).fetchone()
            if not row or not password_check(body.pin, row['pin_hash']):
                raise HTTPException(401, '名前または暗証番号が違います')
            add_session(con,response,row['id'])
        return {'ok':True}

    @app.post('/api/logout')
    def logout(response: Response, kyoki_session: Annotated[str | None, Cookie()] = None):
        if kyoki_session:
            with db() as con:
                con.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(kyoki_session.encode()).hexdigest(),))
        response.delete_cookie('kyoki_session',path='/')
        return {'ok':True}

    @app.get('/api/bootstrap')
    def bootstrap(kyoki_session: Annotated[str | None, Cookie()] = None):
        with db() as con:
            actor=get_actor(con,kyoki_session)
            g=con.execute('SELECT * FROM groups WHERE id=?',(actor['group_id'],)).fetchone()
            members=con.execute('SELECT id,nickname,role FROM members WHERE group_id=? ORDER BY id', (actor['group_id'],)).fetchall()
            rounds=con.execute('''SELECT r.* FROM rounds r WHERE group_id=? ORDER BY event_date DESC,id DESC''',(actor['group_id'],)).fetchall()
            pids=con.execute('''SELECT p.round_id,p.member_id FROM round_participants p
                 JOIN rounds r ON r.id=p.round_id WHERE r.group_id=?''',(actor['group_id'],)).fetchall()
            grouped=defaultdict(list)
            for p in pids:
                grouped[p['round_id']].append(p['member_id'])
            return {
                'me': {'id':actor['id'],'nickname':actor['nickname'],'role':actor['role']},
                'group': {'id':g['id'],'name':g['name'],'invite':g['invite'],
                          'next_mode':g['next_mode'],'next_decider_id':g['next_decider_id']},
                'members':[dict(m) for m in members],
                'rounds':[dict(r) | {'participants':grouped[r['id']]} for r in rounds]
            }

    @app.post('/api/choose-mode')
    def choose_mode(body: ChooseMode, kyoki_session: Annotated[str | None, Cookie()] = None):
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            actor=get_actor(con,kyoki_session)
            g=con.execute('SELECT * FROM groups WHERE id=?',(actor['group_id'],)).fetchone()
            if g['next_decider_id'] != actor['id']:
                raise HTTPException(403,'次回ルールは前回の敗者だけが選べます')
            con.execute('UPDATE groups SET next_mode=? WHERE id=?',(body.mode,g['id']))
        return {'ok':True}

    @app.post('/api/rounds')
    def add_round(body: RoundData, kyoki_session: Annotated[str | None, Cookie()] = None):
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            actor=get_actor(con,kyoki_session)
            group=con.execute('SELECT * FROM groups WHERE id=?',(actor['group_id'],)).fetchone()
            hist = body.historical_mode is not None
            if hist and actor['role']!='admin':
                raise HTTPException(403,'過去の履歴を追加できるのは管理者だけです')
            mode = body.historical_mode if hist else group['next_mode']
            if not mode:
                raise HTTPException(409,'前回の敗者が次回ルールを選ぶまで登録できません')
            check_members(con,actor['group_id'],body.participants)
            payer=body.winner_id if mode=='otoko' else body.loser_id
            cur=con.execute('''INSERT INTO rounds(group_id,event_date,place,amount,mode,
                winner_id,loser_id,payer_id,note,is_historical,recorded_by,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(
                actor['group_id'],body.event_date.isoformat(),body.place.strip(),body.amount,
                mode,body.winner_id,body.loser_id,payer,body.note.strip(),int(hist),actor['id'],utc_stamp()))
            con.executemany('INSERT INTO round_participants(round_id,member_id) VALUES (?,?)',
                [(cur.lastrowid,i) for i in body.participants])
            if not hist:
                con.execute('''UPDATE groups SET next_mode=NULL,next_decider_id=? WHERE id=?''',
                    (body.loser_id,actor['group_id']))
        return {'ok':True,'payer_id':payer}

    @app.delete('/api/rounds/{round_id}')
    def delete_round(round_id: int, kyoki_session: Annotated[str | None, Cookie()] = None):
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            actor=get_actor(con,kyoki_session)
            if actor['role']!='admin':
                raise HTTPException(403,'削除できるのは管理者だけです')
            row=con.execute('SELECT * FROM rounds WHERE id=? AND group_id=?',
                (round_id,actor['group_id'])).fetchone()
            if not row:
                raise HTTPException(404,'履歴が見つかりません')
            latest_live=con.execute('''SELECT id FROM rounds WHERE group_id=? AND is_historical=0
                ORDER BY id DESC LIMIT 1''',(actor['group_id'],)).fetchone()
            if not row['is_historical'] and latest_live and latest_live['id'] != round_id:
                raise HTTPException(409,'途中の通常記録は削除できません。最新の記録から削除してください')
            con.execute('DELETE FROM rounds WHERE id=?',(round_id,))
            if not row['is_historical']:
                previous=con.execute('''SELECT loser_id FROM rounds WHERE group_id=? AND is_historical=0
                    ORDER BY id DESC LIMIT 1''',(actor['group_id'],)).fetchone()
                decider=previous['loser_id'] if previous else con.execute('''SELECT id FROM members
                    WHERE group_id=? AND role='admin' ORDER BY id LIMIT 1''',(actor['group_id'],)).fetchone()['id']
                con.execute('UPDATE groups SET next_mode=NULL,next_decider_id=? WHERE id=?',
                    (decider,actor['group_id']))
        return {'ok':True}

    return app


app=create_app()
