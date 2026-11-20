from pathlib import Path
from fastapi.testclient import TestClient
from app import create_app


def new_app(tmp_path):
    return create_app(str(tmp_path / 'test.sqlite3'))


def create(c):
    res=c.post('/api/groups',json={'name':'TEAM狭気','nickname':'TOM','pin':'123456'})
    assert res.status_code==200,res.text
    return res.json()['invite']


def join(c,invite,name):
    res=c.post('/api/join',json={'invite':invite,'nickname':name,'pin':'777777'})
    assert res.status_code==200,res.text


def test_shared_rule_and_finances(tmp_path):
    app=new_app(tmp_path)
    with TestClient(app) as admin,TestClient(app) as guest,TestClient(app) as stranger:
        invite=create(admin)
        join(guest,invite,'RYU')
        join(stranger,invite,'SORA')
        boot=admin.get('/api/bootstrap').json()
        ida=boot['me']['id']
        idb=next(x['id'] for x in boot['members'] if x['nickname']=='RYU')
        idc=next(x['id'] for x in boot['members'] if x['nickname']=='SORA')
        assert boot['group']['next_decider_id']==ida
        assert stranger.post('/api/choose-mode',json={'mode':'otoko'}).status_code==403
        assert admin.post('/api/choose-mode',json={'mode':'otoko'}).status_code==200
        data=dict(event_date='2026-11-20',place='居酒屋',amount=12000,participants=[ida,idb,idc],winner_id=idb,loser_id=ida,note='')
        assert guest.post('/api/rounds',json=data).status_code==200
        b=guest.get('/api/bootstrap').json()
        assert b['rounds'][0]['payer_id']==idb
        assert b['rounds'][0]['mode']=='otoko'
        assert b['group']['next_decider_id']==ida
        assert b['group']['next_mode'] is None
        assert guest.post('/api/choose-mode',json={'mode':'normal'}).status_code==403
        assert guest.post('/api/rounds',json=data).status_code==409
        assert admin.post('/api/choose-mode',json={'mode':'normal'}).status_code==200
        data.update(amount=9000,winner_id=idb,loser_id=ida)
        assert guest.post('/api/rounds',json=data).status_code==200
        b=admin.get('/api/bootstrap').json()
        assert b['rounds'][0]['payer_id']==ida
        assert b['rounds'][0]['mode']=='normal'
        assert len(b['rounds'])==2
        assert sum(r['amount'] for r in b['rounds'])==21000
        # other group cannot use current group's auth to edit another group
        with TestClient(app) as other:
            inv2=create(other)
            assert inv2!=invite
            assert other.get('/api/bootstrap').json()['rounds']==[]


def test_admin_history_and_delete(tmp_path):
    app=new_app(tmp_path)
    with TestClient(app) as admin, TestClient(app) as guest:
        invite=create(admin)
        join(guest,invite,'A')
        b=admin.get('/api/bootstrap').json()
        owner=b['me']['id']; idb=next(m['id'] for m in b['members'] if m['id']!=owner)
        r={'event_date':'2026-10-05','place':'先月','amount':1000,'participants':[owner,idb],
           'winner_id':owner,'loser_id':idb,'historical_mode':'normal'}
        assert guest.post('/api/rounds',json=r).status_code==403
        assert admin.post('/api/rounds',json=r).status_code==200
        b=admin.get('/api/bootstrap').json()
        assert b['group']['next_decider_id']==owner
        assert b['rounds'][0]['payer_id']==idb
        assert guest.delete('/api/rounds/'+str(b['rounds'][0]['id'])).status_code==403
        assert admin.delete('/api/rounds/'+str(b['rounds'][0]['id'])).status_code==200
        assert admin.get('/api/bootstrap').json()['rounds']==[]
        assert admin.post('/api/choose-mode',json={'mode':'otoko'}).status_code==200
        r.pop('historical_mode');r['event_date']='2026-11-20'
        assert admin.post('/api/rounds',json=r).status_code==200
        b=admin.get('/api/bootstrap').json()
        assert b['group']['next_decider_id']==idb
        # latest record may be deleted by admin, restoring admin as initial chooser
        assert admin.delete('/api/rounds/'+str(b['rounds'][0]['id'])).status_code==200
        assert admin.get('/api/bootstrap').json()['group']['next_decider_id']==owner


def test_passwords_and_validation(tmp_path):
    app=new_app(tmp_path)
    with TestClient(app) as admin,TestClient(app) as guest:
        invite=create(admin)
        join(guest,invite,'A')
        with TestClient(app) as bad:
            assert bad.post('/api/login',json={'invite':invite,'nickname':'A','pin':'111111'}).status_code==401
            assert bad.get('/api/bootstrap').status_code==401
            assert bad.post('/api/join',json={'invite':invite,'nickname':'a','pin':'123456'}).status_code==409
            assert bad.post('/api/join',json={'invite':'not-a-real-token-ever-ever','nickname':'B','pin':'123456'}).status_code==404
            assert bad.post('/api/groups',json={'nickname':'Bad','pin':'12'}).status_code==422
        b=admin.get('/api/bootstrap').json();owner=b['me']['id'];idb=next(m['id'] for m in b['members'] if m['id']!=owner)
        assert admin.post('/api/choose-mode',json={'mode':'otoko'}).status_code==200
        data={'event_date':'2026-11-20','place':'','amount':5000,'participants':[owner,idb], 'winner_id':owner,'loser_id':idb}
        data['participants']=[owner,owner]
        assert admin.post('/api/rounds',json=data).status_code==422
        data['participants']=[owner,idb]
        data['winner_id']=data['loser_id']
        assert admin.post('/api/rounds',json=data).status_code==422
        data['winner_id']=owner
        data['amount']=-1
        assert admin.post('/api/rounds',json=data).status_code==422
        assert admin.post('/api/logout').status_code==200
        assert admin.get('/api/bootstrap').status_code==401
        assert admin.post('/api/login',json={'invite':invite,'nickname':'TOM','pin':'123456'}).status_code==200
        assert admin.get('/api/bootstrap').status_code==200


def test_db_persists_across_instances(tmp_path):
    file=str(tmp_path / 'persistence.sqlite3')
    a=create_app(file)
    with TestClient(a) as c:
        invite=create(c)
    b=create_app(file)
    with TestClient(b) as c:
        r=c.post('/api/login',json={'invite':invite,'nickname':'TOM','pin':'123456'})
        assert r.status_code==200
        assert c.get('/api/bootstrap').json()['group']['name']=='TEAM狭気'
