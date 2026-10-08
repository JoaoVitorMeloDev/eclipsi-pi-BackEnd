import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('SUPABASE_JWT_SECRET', 'test-secret')
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def token():
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': '00000000-0000-0000-0000-000000000001', 'email': 'test@example.com', 'aud': 'authenticated', 'iat': now, 'exp': now + timedelta(minutes=10)}, 'test-secret', algorithm='HS256')


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['success'] is True


def test_protected_endpoint_without_token(client):
    response = client.get('/api/me')
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token(client):
    response = client.get('/api/me', headers={'Authorization': f'Bearer {token()}'})
    assert response.status_code == 200
    assert response.json['user']['email'] == 'test@example.com'

@pytest.mark.parametrize('path', ['/api/v2/doctors', '/api/v2/appointments', '/api/v2/chat/conversations', '/api/v2/quiz/questions', '/api/v2/payments'])
def test_domain_routes_require_authentication(client, path):
    assert client.get(path).status_code == 401
