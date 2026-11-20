/* TEAM狭気 — GitHub Pages preview adapter.
   This is NOT the shared online backend. Demo records stay in THIS browser only. */
(function () {
  'use strict';
  var STORAGE = 'team_otokogi_pages_preview_v1';
  function initialData() {
    return {
      me: {id: 1, nickname: 'サンプルA', role: 'admin'},
      group: {id: 1, name: 'TEAM狭気', invite: 'preview-local-data-only', next_mode: null, next_decider_id: 1},
      members: [
        {id: 1, nickname: 'サンプルA', role: 'admin'},
        {id: 2, nickname: 'サンプルB', role: 'member'},
        {id: 3, nickname: 'サンプルC', role: 'member'},
        {id: 4, nickname: 'サンプルD', role: 'member'}
      ],
      rounds: [
        {id: 3, group_id: 1, event_date: '2026-11-18', place: 'サンプル居酒屋', amount: 12480, mode: 'otoko', winner_id: 2, loser_id: 1, payer_id: 2, note: 'サンプルデータ', is_historical: 0, recorded_by: 1, participants: [1,2,3,4]},
        {id: 2, group_id: 1, event_date: '2026-11-13', place: 'サンプル焼肉', amount: 15600, mode: 'normal', winner_id: 3, loser_id: 4, payer_id: 4, note: 'サンプルデータ', is_historical: 0, recorded_by: 1, participants: [1,2,3,4]},
        {id: 1, group_id: 1, event_date: '2026-11-07', place: 'サンプル会場', amount: 9800, mode: 'otoko', winner_id: 1, loser_id: 3, payer_id: 1, note: 'サンプルデータ', is_historical: 0, recorded_by: 1, participants: [1,2,3]}
      ]
    };
  }
  function read() {
    try {
      var parsed = JSON.parse(localStorage.getItem(STORAGE));
      if (parsed && parsed.me && parsed.group && Array.isArray(parsed.members) && Array.isArray(parsed.rounds)) return parsed;
    } catch (e) {}
    return initialData();
  }
  var db = read();
  function save() { localStorage.setItem(STORAGE, JSON.stringify(db)); }
  function reply(payload, code) {
    return Promise.resolve(new Response(JSON.stringify(payload), {
      status: code || 200, headers: {'Content-Type': 'application/json'}
    }));
  }
  function failure(message, code) { return reply({detail: message}, code || 400); }
  var nativeFetch = window.fetch.bind(window);
  window.fetch = function (input, options) {
    options = options || {};
    var raw = typeof input === 'string' ? input : input.url;
    var pathname = new URL(raw, location.href).pathname;
    if (pathname.indexOf('/api/') !== 0) return nativeFetch(input, options);
    var method = String(options.method || 'GET').toUpperCase();
    var body;
    try { body = options.body ? JSON.parse(options.body) : {}; }
    catch (e) { return failure('入力データが不正です'); }
    if (pathname === '/api/bootstrap' && method === 'GET') return reply(db);
    if (pathname === '/api/choose-mode' && method === 'POST') {
      if (db.me.id !== db.group.next_decider_id) return failure('次回ルールは前回の敗者だけが選べます', 403);
      if (body.mode !== 'otoko' && body.mode !== 'normal') return failure('ルールが不正です');
      db.group.next_mode = body.mode; save(); return reply({ok: true});
    }
    if (pathname === '/api/rounds' && method === 'POST') {
      var ids = Array.isArray(body.participants) ? body.participants.map(Number) : [];
      var w = Number(body.winner_id), l = Number(body.loser_id);
      var amount = Number(body.amount), historical = !!body.historical_mode;
      if (ids.length < 2 || new Set(ids).size !== ids.length || !ids.includes(w) || !ids.includes(l) || w === l) return failure('参加者と勝敗の組み合わせが不正です');
      if (!Number.isSafeInteger(amount) || amount < 1) return failure('会計金額が不正です');
      if (historical && db.me.role !== 'admin') return failure('過去記録は管理者のみ登録できます', 403);
      var mode = historical ? body.historical_mode : db.group.next_mode;
      if (mode !== 'otoko' && mode !== 'normal') return failure('先に次回ルールを決めてください');
      var payer = mode === 'otoko' ? w : l;
      var nextId = db.rounds.reduce(function(v,r) { return Math.max(v,r.id); }, 0) + 1;
      db.rounds.unshift({
        id: nextId, group_id: 1, event_date: body.event_date, place: body.place || '',
        amount: amount, mode: mode, winner_id: w, loser_id: l, payer_id: payer,
        note: body.note || '', is_historical: historical ? 1 : 0, recorded_by: db.me.id,
        created_at: new Date().toISOString(), participants: ids
      });
      db.rounds.sort(function(a,b) { return b.event_date.localeCompare(a.event_date) || b.id - a.id; });
      if (!historical) { db.group.next_decider_id = l; db.group.next_mode = null; }
      save(); return reply({ok: true, payer_id: payer});
    }
    if (pathname.indexOf('/api/rounds/') === 0 && method === 'DELETE') {
      var id = Number(pathname.split('/').pop());
      var round = db.rounds.find(function(r) { return r.id === id; });
      if (!round) return failure('記録が見つかりません', 404);
      if (round.is_historical !== 1) {
        var lives = db.rounds.filter(function(r) { return r.is_historical !== 1; }).sort(function(a,b) { return b.id-a.id; });
        if (lives.length && lives[0].id !== id) return failure('最新の通常記録から削除してください', 409);
      }
      db.rounds = db.rounds.filter(function(r) { return r.id !== id; });
      if (round.is_historical !== 1) {
        var recent = db.rounds.filter(function(r) { return r.is_historical !== 1; }).sort(function(a,b) { return b.id-a.id; })[0];
        db.group.next_decider_id = recent ? recent.loser_id : 1;
        db.group.next_mode = null;
      }
      save(); return reply({ok:true});
    }
    return failure('これは公開UIのプレビューです。メンバー共有・ログインはまだ接続されていません。', 501);
  };
  document.addEventListener('click', function(e) {
    if (e.target.closest('#share-line, #copy-link, #logout')) {
      e.preventDefault(); e.stopImmediatePropagation();
      alert('プレビュー版です。各端末のデータは共有されません。LINE招待と本番ログインはデータベース接続後に利用できます。');
    }
  }, true);
})();