"""
Routes for managing tasks.
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Task

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('', methods=['GET'])
def get_tasks():
    """List all tasks."""
    query = Task.query
    
    # Apply filters
    room = request.args.get('room')
    if room:
        query = query.filter_by(room=room)
    
    is_active = request.args.get('is_active')
    if is_active is not None:
        is_active_bool = is_active.lower() in ('true', '1', 'yes')
        query = query.filter_by(is_active=is_active_bool)
    
    tasks = query.all()
    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in tasks],
        'count': len(tasks)
    })


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a task by ID."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Tarea no encontrada'}), 404
    return jsonify({'success': True, 'data': task.to_dict()})


@tasks_bp.route('', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.get_json() or {}
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'El nombre es requerido'}), 400
    
    # Create task
    task = Task(
        name=data['name'].strip(),
        description=data.get('description'),
        room=data.get('room'),
        effort_points=data.get('effort_points', 1),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'success': True, 'data': task.to_dict()}), 201


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Tarea no encontrada'}), 404
    
    data = request.get_json() or {}
    
    # Update fields
    if 'name' in data:
        task.name = data['name'].strip()
    
    if 'description' in data:
        task.description = data['description']
    
    if 'room' in data:
        task.room = data['room']
    
    if 'effort_points' in data:
        task.effort_points = data['effort_points']
    
    if 'is_active' in data:
        task.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({'success': True, 'data': task.to_dict()})


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Tarea no encontrada'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return '', 204
