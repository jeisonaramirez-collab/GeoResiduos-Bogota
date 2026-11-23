"""Comprobación del flujo de fotografía y de configuración cloud en API compartida."""
import base64
import io
import os
from PIL import Image
from fastapi.testclient import TestClient
from server import app


def test_photo_persists_and_serves_from_database():
    im = Image.new('RGB', (24, 18), (100, 180, 110))
    bio = io.BytesIO()
    im.save(bio, format='PNG')
    photo = 'data:image/png;base64,' + base64.b64encode(bio.getvalue()).decode()
    with TestClient(app) as client:
        token = client.get('/api/session').json()['csrf']
        payload = {
            'description': 'Reporte de imagen para la prueba funcional del sistema',
            'category': 'Residuos mixtos', 'locality': 'Kennedy',
            'date': '2026-11-01', 'lat': 4.63, 'lng': -74.14, 'photo': photo,
        }
        result = client.post('/api/reports', json=payload, headers={'X-CSRF-Token': token})
        assert result.status_code == 201, result.text
        item = result.json()['item']
        assert item['photo'] == f"/api/reports/{item['id']}/photo"
        image_response = client.get(item['photo'])
        assert image_response.status_code == 200
        assert image_response.headers['content-type'].startswith('image/webp')
        with Image.open(io.BytesIO(image_response.content)) as uploaded:
            assert uploaded.size == (24, 18)
        assert any(x['id'] == item['id'] for x in client.get('/api/reports').json()['items'])


def test_cloud_admin_password_from_environment(monkeypatch):
    from security import admin_ready, verify_admin
    monkeypatch.setenv('ADMIN_PASSWORD', 'UnaClaveDePrueba!2026')
    assert admin_ready() is True
    assert verify_admin('UnaClaveDePrueba!2026') is True
    assert verify_admin('ClaveIncorrecta!2026') is False
