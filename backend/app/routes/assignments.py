"""
Routes for managing assignments.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import random
from app import db
from app.models.models import Person, Task, Assignment

assignments_bp = Blueprint('assignments', __name__)


@assignments_bp.route('', methods=['GET'])
def get_assignments():
    """List all assignments."""
    assignments = Assignment.query.all()
    return jsonify({
        'success': True,
        'data': [a.to_dict() for a in assignments],
        'count': len(assignments)
    })


@assignments_bp.route('/current', methods=['GET'])
def get_current_assignments():
    """Get current active assignments."""
    assignments = Assignment.query.filter_by(is_active=True).all()
    
    # Get the most recent assignment time
    generated_at = None
    if assignments:
        generated_at = max(a.assigned_at for a in assignments)
    
    return jsonify({
        'success': True,
        'data': [a.to_dict() for a in assignments],
        'generated_at': generated_at.isoformat() + 'Z' if generated_at else None
    })


@assignments_bp.route('/generate', methods=['POST'])
def generate_assignments():
    """
    Generate new random assignments.
    
    Algorithm:
    1. Deactivate all previous assignments
    2. Get active persons and tasks
    3. Distribute tasks evenly considering effort points
    4. Create new assignments
    """
    data = request.get_json() or {}
    strategy = data.get('strategy', 'balanced')
    clear_previous = data.get('clear_previous', True)
    
    # Get active persons and tasks
    persons = Person.query.filter_by(is_active=True).all()
    tasks = Task.query.filter_by(is_active=True).all()
    
    if not persons:
        return jsonify({
            'success': False,
            'error': 'No hay personas activas para asignar tareas'
        }), 400
    
    if not tasks:
        return jsonify({
            'success': False,
            'error': 'No hay tareas activas para asignar'
        }), 400
    
    # Deactivate previous assignments
    if clear_previous:
        Assignment.query.update({'is_active': False})
    
    # Shuffle tasks for randomness
    tasks_list = list(tasks)
    random.shuffle(tasks_list)
    
    # Track effort per person for balanced distribution
    effort_tracking = {p.id: 0 for p in persons}
    new_assignments = []
    
    # Sort persons by current effort (ascending) for each assignment
    for task in tasks_list:
        # Find person with least effort
        min_effort = min(effort_tracking.values())
        candidates = [p for p in persons if effort_tracking[p.id] == min_effort]
        
        # Random selection among candidates with same effort
        selected_person = random.choice(candidates)
        
        # Create assignment
        assignment = Assignment(
            person_id=selected_person.id,
            task_id=task.id,
            assigned_at=datetime.utcnow(),
            is_active=True
        )
        db.session.add(assignment)
        new_assignments.append(assignment)
        
        # Update effort tracking
        effort_tracking[selected_person.id] += task.effort_points
    
    db.session.commit()
    
    # Format response after commit - query fresh data with joined relationships
    assignments_by_person = {}
    for a in new_assignments:
        # Reload the assignment with relationships
        assignment = Assignment.query.filter_by(id=a.id).first()
        if assignment:
            pid = assignment.person_id
            if pid not in assignments_by_person:
                assignments_by_person[pid] = {
                    'person_id': pid,
                    'person_name': assignment.person.name if assignment.person else 'Unknown',
                    'tasks': [],
                    'total_effort': 0
                }
            if assignment.task:
                assignments_by_person[pid]['tasks'].append({
                    'id': assignment.task.id,
                    'name': assignment.task.name,
                    'effort_points': assignment.task.effort_points
                })
                assignments_by_person[pid]['total_effort'] += assignment.task.effort_points
    
    return jsonify({
        'success': True,
        'data': {
            'assignments': list(assignments_by_person.values()),
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        },
        'message': 'Asignaciones generadas exitosamente'
    }), 201


@assignments_bp.route('/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """Delete an assignment."""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'success': False, 'error': 'Asignación no encontrada'}), 404
    
    db.session.delete(assignment)
    db.session.commit()
    
    return '', 204


@assignments_bp.route('/<int:assignment_id>/complete', methods=['POST'])
def complete_assignment(assignment_id):
    """Mark an assignment as completed."""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'success': False, 'error': 'Asignación no encontrada'}), 404
    
    assignment.completed_at = datetime.utcnow()
    assignment.is_active = False
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'id': assignment.id,
            'completed_at': assignment.completed_at.isoformat() + 'Z'
        }
    })
