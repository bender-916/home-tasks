""" Routes for managing assignments. """
from flask import Blueprint, request, jsonify
from datetime import datetime
import random
import sys
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
    
    try:
        # Get active persons and tasks
        persons = Person.query.filter_by(is_active=True).all()
        tasks = Task.query.filter_by(is_active=True).all()
        
        if not persons:
            return jsonify({'success': False, 'error': 'No hay personas activas para asignar tareas'}), 400
        if not tasks:
            return jsonify({'success': False, 'error': 'No hay tareas activas para asignar'}), 400
        
        # Deactivate previous assignments
        if clear_previous:
            Assignment.query.update({'is_active': False})
            db.session.commit()
        
        # Prepare data BEFORE modifying session
        # Store person and task data in memory to avoid lazy loading issues
        persons_data = {p.id: {'id': p.id, 'name': p.name, 'color': p.color} for p in persons}
        tasks_data = {t.id: {'id': t.id, 'name': t.name, 'room': t.room, 'effort_points': t.effort_points} for t in tasks}
        
        # Shuffle tasks for randomness
        tasks_list = list(tasks_data.values())
        random.shuffle(tasks_list)
        
        # Track effort per person for balanced distribution
        effort_tracking = {p_id: 0 for p_id in persons_data.keys()}
        
        # Collect assignment data for response
        assignments_for_response = []
        
        # Assign tasks
        for task in tasks_list:
            # Find person with least effort
            min_effort = min(effort_tracking.values())
            candidates = [p_id for p_id, effort in effort_tracking.items() if effort == min_effort]
            selected_person_id = random.choice(candidates)
            selected_person = persons_data[selected_person_id]
            
            # Create assignment in database
            assignment = Assignment(
                person_id=selected_person_id,
                task_id=task['id'],
                assigned_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(assignment)
            
            # Track for response (using in-memory data, no lazy loading)
            assignments_for_response.append({
                'person_id': selected_person_id,
                'person_name': selected_person['name'],
                'task_id': task['id'],
                'task_name': task['name'],
                'effort_points': task['effort_points']
            })
            
            # Update effort tracking
            effort_tracking[selected_person_id] += task['effort_points']
        
        # Commit to database
        db.session.commit()
        
        # Format response using collected data (no database access needed)
        assignments_by_person = {}
        for item in assignments_for_response:
            pid = item['person_id']
            if pid not in assignments_by_person:
                assignments_by_person[pid] = {
                    'person_id': pid,
                    'person_name': item['person_name'],
                    'tasks': [],
                    'total_effort': 0
                }
            assignments_by_person[pid]['tasks'].append({
                'id': item['task_id'],
                'name': item['task_name'],
                'effort_points': item['effort_points']
            })
            assignments_by_person[pid]['total_effort'] += item['effort_points']
        
        return jsonify({
            'success': True,
            'data': {
                'assignments': list(assignments_by_person.values()),
                'generated_at': datetime.utcnow().isoformat() + 'Z'
            },
            'message': 'Asignaciones generadas exitosamente'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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

@assignments_bp.route('/reset', methods=['POST'])
def reset_assignments():
    """Debug endpoint to reset all assignments."""
    try:
        Assignment.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Todas las asignaciones eliminadas'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
