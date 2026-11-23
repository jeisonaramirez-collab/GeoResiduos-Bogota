"""Pruebas automatizadas de integración: API y persistencia."""
import os
import tempfile
from pathlib import Path
TEST_DIR = tempfile.mkdtemp(prefix='georesiduos_tests_')
os.environ['GEORESIDUOS_DATA_DIR'] = TEST_DIR
os.environ['GEORESIDUOS_UPLOAD_DIR'] = str(Path(TEST_DIR)/'uploads')
from fastapi.testclient import TestClient
from server import app
from security import create_admin
from storage import SessionLocal, Report
from sqlalchemy import select


def test_api_full_flow():
    create_admin('ContrasenaDemo!123')
    with TestClient(app) as client:
        assert client.get('/api/health').json()['ok']
        token=client.get('/api/session').json()['csrf']
        headers={'X-CSRF-Token':token}
        assert client.get('/api/reports').json()['items']==[]
        payload={'description':'Residuos acumulados junto al parque para prueba académica','category':'Residuos mixtos',
                 'locality':'Kennedy','date':'2026-11-01','lat':4.625,'lng':-74.150}
        assert client.post('/api/reports',json=payload).status_code==403
        r=client.post('/api/reports',json=payload,headers=headers)
        assert r.status_code==201,r.text
        report_id=r.json()['item']['id']
        assert report_id.startswith('RPT-')
        assert client.get('/api/reports').json()['count']==1
        with SessionLocal() as db:
            item=db.scalar(select(Report).where(Report.description==payload['description']))
            assert item and item.locality=='Kennedy'
        assert client.get('/api/reports/'+report_id).status_code==200
        assert client.patch('/api/admin/reports/'+report_id,json={'status':'Cerrado'},headers=headers).status_code==401
        assert client.post('/api/admin/login',json={'password':'mala'},headers=headers).status_code==401
        assert client.post('/api/admin/login',json={'password':'ContrasenaDemo!123'},headers=headers).status_code==200
        change=client.patch('/api/admin/reports/'+report_id,json={'status':'En revisión'},headers=headers)
        assert change.status_code==200,change.text
        assert change.json()['item']['status']=='En revisión'
        assert client.get('/api/admin/audit').json()['items'][0]['new']=='En revisión'
        demo=client.post('/api/admin/seed-demo',headers=headers,json={})
        assert demo.status_code==200 and demo.json()['inserted']==8
        assert client.get('/api/reports').json()['count']==9
        assert client.post('/api/admin/seed-demo',headers=headers,json={}).json()['inserted']==0
        assert client.post('/api/admin/logout',headers=headers,json={}).status_code==200
        assert client.patch('/api/admin/reports/'+report_id,json={'status':'Cerrado'},headers=headers).status_code==401


def test_reject_invalid_coordinates_and_future_date():
    with TestClient(app) as client:
        h={'X-CSRF-Token':client.get('/api/session').json()['csrf']}
        p={'description':'Desechos acumulados cerca de una calle','category':'Residuos mixtos',
           'locality':'Kennedy','date':'2026-11-01','lat':0,'lng':0}
        assert client.post('/api/reports',json=p,headers=h).status_code==422
        p['lat']=4.6;p['lng']=-74.1;p['date']='2099-01-01'
        assert client.post('/api/reports',json=p,headers=h).status_code==422
        p['date']='2026-11-01';p['category']='Clasificacion falsa'
        assert client.post('/api/reports',json=p,headers=h).status_code==422


def test_frontend_is_served():
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        assert 'GeoResiduos' in client.get('/').text
        assert client.get('/static/app.js').status_code==200
