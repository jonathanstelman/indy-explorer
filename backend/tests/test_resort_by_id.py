import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models import Resort

FAKE_RESORTS = [
    Resort(
        resort_id='abc-123',
        name='Vail',
        region='West',
        city='Vail',
        state='CO',
        country='USA',
        reservation_status='required',
        indy_page='https://example.com/vail',
    ),
    Resort(
        resort_id='def-456',
        name='Stowe',
        region='Northeast',
        city='Stowe',
        state='VT',
        country='USA',
        reservation_status='none',
        indy_page='https://example.com/stowe',
    ),
]

client = TestClient(app)


def test_get_resort_by_id_returns_resort():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/resorts/abc-123')
    assert response.status_code == 200
    data = response.json()
    assert data['resort_id'] == 'abc-123'
    assert data['name'] == 'Vail'


def test_get_resort_by_id_returns_full_model():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/resorts/def-456')
    assert response.status_code == 200
    data = response.json()
    assert data['resort_id'] == 'def-456'
    assert data['state'] == 'VT'


def test_get_resort_by_id_not_found():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/resorts/nonexistent-uuid')
    assert response.status_code == 404
