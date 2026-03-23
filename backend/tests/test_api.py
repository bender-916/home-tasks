"""Tests for Home Tasks API."""
import pytest
import os
import tempfile
from app import create_app, db
from app.models.models import Person, Task, Assignment


@pytest.fixture
def client():
    """Create a test client with temporary database."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
    
    os.close(db_fd)
    os.unlink(db_path)


# =============================================================================
# TESTS FOR PERSONS (8 tests)
# =============================================================================

def test_create_person(client):
    """Test creating a person with valid data."""
    response = client.post('/api/persons', json={'name': 'Test', 'color': '#FF0000'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'Test'


def test_create_person_without_name(client):
    """Test rejecting a person without a name."""
    response = client.post('/api/persons', json={'color': '#FF0000'})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_create_person_duplicate_name(client):
    """Test rejecting a person with duplicate name."""
    client.post('/api/persons', json={'name': 'Juan', 'color': '#FF0000'})
    response = client.post('/api/persons', json={'name': 'Juan', 'color': '#00FF00'})
    assert response.status_code == 409


def test_get_person_list(client):
    """Test listing all persons."""
    client.post('/api/persons', json={'name': 'Person1'})
    client.post('/api/persons', json={'name': 'Person2'})
    response = client.get('/api/persons')
    assert response.status_code == 200
    assert len(response.get_json()['data']) == 2


def test_get_person_by_id(client):
    """Test getting a specific person by ID."""
    response = client.post('/api/persons', json={'name': 'Maria'})
    person_id = response.get_json()['data']['id']
    response = client.get(f'/api/persons/{person_id}')
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == 'Maria'


def test_get_person_not_found(client):
    """Test getting a non-existent person."""
    assert client.get('/api/persons/999').status_code == 404


def test_update_person(client):
    """Test updating a person."""
    response = client.post('/api/persons', json={'name': 'Carlos'})
    person_id = response.get_json()['data']['id']
    response = client.put(f'/api/persons/{person_id}', json={'name': 'Carlos Updated'})
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == 'Carlos Updated'


def test_delete_person(client):
    """Test deleting a person."""
    response = client.post('/api/persons', json={'name': 'ToDelete'})
    person_id = response.get_json()['data']['id']
    assert client.delete(f'/api/persons/{person_id}').status_code == 204
    assert client.get(f'/api/persons/{person_id}').status_code == 404


# =============================================================================
# TESTS FOR TASKS (8 tests)
# =============================================================================

def test_create_task(client):
    """Test creating a task with valid data."""
    response = client.post('/api/tasks', json={'name': 'Clean Kitchen', 'room': 'Kitchen', 'effort_points': 2})
    assert response.status_code == 201
    assert response.get_json()['data']['name'] == 'Clean Kitchen'


def test_create_task_without_name(client):
    """Test rejecting a task without a name."""
    response = client.post('/api/tasks', json={'description': 'No name'})
    assert response.status_code == 400


def test_get_task_list(client):
    """Test listing all tasks."""
    client.post('/api/tasks', json={'name': 'Task1'})
    client.post('/api/tasks', json={'name': 'Task2'})
    response = client.get('/api/tasks')
    assert len(response.get_json()['data']) == 2


def test_get_task_by_id(client):
    """Test getting a specific task by ID."""
    response = client.post('/api/tasks', json={'name': 'Mop Floor', 'effort_points': 3})
    task_id = response.get_json()['data']['id']
    response = client.get(f'/api/tasks/{task_id}')
    assert response.get_json()['data']['name'] == 'Mop Floor'


def test_get_task_not_found(client):
    """Test getting a non-existent task."""
    assert client.get('/api/tasks/999').status_code == 404


def test_update_task(client):
    """Test updating a task."""
    response = client.post('/api/tasks', json={'name': 'Old Name'})
    task_id = response.get_json()['data']['id']
    response = client.put(f'/api/tasks/{task_id}', json={'name': 'New Name', 'effort_points': 5})
    assert response.get_json()['data']['name'] == 'New Name'


def test_delete_task(client):
    """Test deleting a task."""
    response = client.post('/api/tasks', json={'name': 'ToDelete'})
    task_id = response.get_json()['data']['id']
    assert client.delete(f'/api/tasks/{task_id}').status_code == 204
    assert client.get(f'/api/tasks/{task_id}').status_code == 404


def test_filter_tasks_by_room(client):
    """Test filtering tasks by room."""
    client.post('/api/tasks', json={'name': 'Bedroom Task', 'room': 'Bedroom'})
    client.post('/api/tasks', json={'name': 'Kitchen Task', 'room': 'Kitchen'})
    response = client.get('/api/tasks?room=Bedroom')
    assert len(response.get_json()['data']) == 1


# =============================================================================
# TESTS FOR ASSIGNMENTS (6 tests)
# =============================================================================

def test_generate_assignments(client):
    """Test generating valid assignments."""
    # Setup: create 2 persons and 4 tasks
    client.post('/api/persons', json={'name': 'Alice'})
    client.post('/api/persons', json={'name': 'Bob'})
    client.post('/api/tasks', json={'name': 'Kitchen', 'effort_points': 2})
    client.post('/api/tasks', json={'name': 'Bathroom', 'effort_points': 3})
    client.post('/api/tasks', json={'name': 'Living Room', 'effort_points': 2})
    client.post('/api/tasks', json={'name': 'Bedroom', 'effort_points': 1})
    
    response = client.post('/api/assignments/generate', json={})
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'assignments' in data['data']


def test_generate_assignments_no_persons(client):
    """Test generating assignments with no persons should fail."""
    client.post('/api/tasks', json={'name': 'Task1', 'effort_points': 1})
    response = client.post('/api/assignments/generate', json={})
    assert response.status_code == 400
    assert response.get_json()['success'] is False


def test_generate_assignments_no_tasks(client):
    """Test generating assignments with no tasks should fail."""
    client.post('/api/persons', json={'name': 'Alice'})
    response = client.post('/api/assignments/generate', json={})
    assert response.status_code == 400
    assert response.get_json()['success'] is False


def test_complete_assignment(client):
    """Test marking an assignment as completed."""
    # Setup
    client.post('/api/persons', json={'name': 'Alice'})
    client.post('/api/tasks', json={'name': 'Kitchen', 'effort_points': 2})
    client.post('/api/tasks', json={'name': 'Bath', 'effort_points': 1})
    client.post('/api/assignments/generate', json={})
    
    # Get assignment ID
    response = client.get('/api/assignments')
    assignments = response.get_json()['data']
    assert len(assignments) > 0
    assignment_id = assignments[0]['id']
    
    # Complete assignment
    response = client.post(f'/api/assignments/{assignment_id}/complete')
    assert response.status_code == 200
    assert response.get_json()['success'] is True


def test_distribution_equity(client):
    """Test that assignments are distributed equitably among persons."""
    # Create 2 persons and 2 tasks with equal effort
    client.post('/api/persons', json={'name': 'Alice'})
    client.post('/api/persons', json={'name': 'Bob'})
    client.post('/api/tasks', json={'name': 'Task1', 'effort_points': 1})
    client.post('/api/tasks', json={'name': 'Task2', 'effort_points': 1})
    
    response = client.post('/api/assignments/generate', json={})
    data = response.get_json()['data']['assignments']
    
    # Check each person got at least one task
    total_tasks = sum(len(p['tasks']) for p in data)
    assert total_tasks == 2


def test_get_current_assignments(client):
    """Test getting current active assignments."""
    # Setup and generate
    client.post('/api/persons', json={'name': 'Alice'})
    client.post('/api/tasks', json={'name': 'Kitchen', 'effort_points': 2})
    client.post('/api/assignments/generate', json={})
    
    response = client.get('/api/assignments/current')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['data']) > 0
    assert 'generated_at' in data
