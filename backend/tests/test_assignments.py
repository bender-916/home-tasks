"""
Tests for assignments API endpoints.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import Person, Task, Assignment


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


@pytest.fixture
def setup_data(client):
    """Create test persons and tasks."""
    # Create persons
    client.post('/api/persons', json={'name': 'Juan', 'color': '#FF0000'})
    client.post('/api/persons', json={'name': 'Maria', 'color': '#00FF00'})
    
    # Create tasks
    client.post('/api/tasks', json={'name': 'Lavar platos', 'effort_points': 2})
    client.post('/api/tasks', json={'name': 'Sacar basura', 'effort_points': 1})
    client.post('/api/tasks', json={'name': 'Limpiar baño', 'effort_points': 3})


class TestAssignmentsAPI:
    """Tests for assignments endpoints."""

    def test_generate_assignments(self, client, setup_data):
        """Test generating assignments."""
        response = client.post('/api/assignments/generate')
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'assignments' in data['data']
        assert len(data['data']['assignments']) > 0

    def test_generate_without_persons(self, client):
        """Test generating assignments without persons."""
        client.post('/api/tasks', json={'name': 'Task'})
        response = client.post('/api/assignments/generate')
        assert response.status_code == 400

    def test_generate_without_tasks(self, client):
        """Test generating assignments without tasks."""
        client.post('/api/persons', json={'name': 'Person'})
        response = client.post('/api/assignments/generate')
        assert response.status_code == 400

    def test_get_current_assignments(self, client, setup_data):
        """Test getting current assignments."""
        client.post('/api/assignments/generate')
        
        response = client.get('/api/assignments/current')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) > 0

    def test_complete_assignment(self, client, setup_data):
        """Test completing an assignment."""
        gen_resp = client.post('/api/assignments/generate')
        
        # Get an assignment ID
        current = client.get('/api/assignments/current').get_json()
        assignment_id = current['data'][0]['id']
        
        response = client.post(f'/api/assignments/{assignment_id}/complete')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['completed_at'] is not None

    def test_delete_assignment(self, client, setup_data):
        """Test deleting an assignment."""
        client.post('/api/assignments/generate')
        
        current = client.get('/api/assignments/current').get_json()
        assignment_id = current['data'][0]['id']
        
        response = client.delete(f'/api/assignments/{assignment_id}')
        assert response.status_code == 204

    def test_balanced_distribution(self, client, setup_data):
        """Test that assignments are balanced."""
        response = client.post('/api/assignments/generate')
        data = response.get_json()
        
        # Check effort is distributed
        efforts = [a['total_effort'] for a in data['data']['assignments']]
        max_diff = max(efforts) - min(efforts)
        assert max_diff <= 3  # Allow some variance

    def test_regenerate_deactivates_previous(self, client, setup_data):
        """Test that regenerating deactivates previous assignments."""
        client.post('/api/assignments/generate')
        client.post('/api/assignments/generate')
        
        # Should still have active assignments
        current = client.get('/api/assignments/current').get_json()
        # Should have 3 tasks assigned (number of active tasks)
        assert len(current['data']) == 3
