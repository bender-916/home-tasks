"""
Tests for persons API endpoints.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import Person


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestPersonsAPI:
    """Tests for persons endpoints."""

    def test_list_persons_empty(self, client):
        """Test listing persons when empty."""
        response = client.get('/api/persons')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []

    def test_create_person(self, client):
        """Test creating a person."""
        response = client.post('/api/persons', json={
            'name': 'Juan',
            'color': '#FF0000'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == 'Juan'
        assert data['data']['color'] == '#FF0000'
        assert data['data']['is_active'] is True

    def test_create_person_missing_name(self, client):
        """Test creating a person without name."""
        response = client.post('/api/persons', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'nombre' in data['error'].lower()

    def test_create_duplicate_person(self, client):
        """Test creating a duplicate person."""
        client.post('/api/persons', json={'name': 'Juan'})
        response = client.post('/api/persons', json={'name': 'Juan'})
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False

    def test_get_person(self, client):
        """Test getting a specific person."""
        create_resp = client.post('/api/persons', json={'name': 'Maria'})
        person_id = create_resp.get_json()['data']['id']
        
        response = client.get(f'/api/persons/{person_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == 'Maria'

    def test_get_nonexistent_person(self, client):
        """Test getting a nonexistent person."""
        response = client.get('/api/persons/999')
        assert response.status_code == 404

    def test_update_person(self, client):
        """Test updating a person."""
        create_resp = client.post('/api/persons', json={'name': 'Pedro'})
        person_id = create_resp.get_json()['data']['id']
        
        response = client.put(f'/api/persons/{person_id}', json={
            'name': 'Pedro Updated',
            'color': '#00FF00'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Pedro Updated'
        assert data['data']['color'] == '#00FF00'

    def test_delete_person(self, client):
        """Test deleting a person."""
        create_resp = client.post('/api/persons', json={'name': 'ToDelete'})
        person_id = create_resp.get_json()['data']['id']
        
        response = client.delete(f'/api/persons/{person_id}')
        assert response.status_code == 204
        
        # Verify deleted
        get_resp = client.get(f'/api/persons/{person_id}')
        assert get_resp.status_code == 404
