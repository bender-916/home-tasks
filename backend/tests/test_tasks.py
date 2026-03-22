"""
Tests for tasks API endpoints.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import Task


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


class TestTasksAPI:
    """Tests for tasks endpoints."""

    def test_list_tasks_empty(self, client):
        """Test listing tasks when empty."""
        response = client.get('/api/tasks')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0

    def test_create_task(self, client):
        """Test creating a task."""
        response = client.post('/api/tasks', json={
            'name': 'Lavar platos',
            'description': 'Lavar todos los platos',
            'room': 'Cocina',
            'effort_points': 2
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == 'Lavar platos'
        assert data['data']['room'] == 'Cocina'
        assert data['data']['effort_points'] == 2

    def test_create_task_minimal(self, client):
        """Test creating a task with minimal data."""
        response = client.post('/api/tasks', json={'name': 'Simple task'})
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['name'] == 'Simple task'
        assert data['data']['effort_points'] == 1  # default

    def test_create_task_missing_name(self, client):
        """Test creating a task without name."""
        response = client.post('/api/tasks', json={})
        assert response.status_code == 400

    def test_get_task(self, client):
        """Test getting a specific task."""
        create_resp = client.post('/api/tasks', json={'name': 'Test task'})
        task_id = create_resp.get_json()['data']['id']
        
        response = client.get(f'/api/tasks/{task_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Test task'

    def test_filter_tasks_by_room(self, client):
        """Test filtering tasks by room."""
        client.post('/api/tasks', json={'name': 'Task 1', 'room': 'Cocina'})
        client.post('/api/tasks', json={'name': 'Task 2', 'room': 'Salon'})
        
        response = client.get('/api/tasks?room=Cocina')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert data['data'][0]['room'] == 'Cocina'

    def test_update_task(self, client):
        """Test updating a task."""
        create_resp = client.post('/api/tasks', json={'name': 'Original'})
        task_id = create_resp.get_json()['data']['id']
        
        response = client.put(f'/api/tasks/{task_id}', json={
            'name': 'Updated',
            'effort_points': 5
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Updated'
        assert data['data']['effort_points'] == 5

    def test_delete_task(self, client):
        """Test deleting a task."""
        create_resp = client.post('/api/tasks', json={'name': 'ToDelete'})
        task_id = create_resp.get_json()['data']['id']
        
        response = client.delete(f'/api/tasks/{task_id}')
        assert response.status_code == 204
        
        get_resp = client.get(f'/api/tasks/{task_id}')
        assert get_resp.status_code == 404
