""" Routes for managing assignments. """
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
    """Generate new random assignments."""
    try:
        data = request.get_json() or {}
        clear_previous = data.get('clear_previous', True)
        
        # Get active persons and tasks
        persons = Person.query.filter_by(is_active=True).all()
        tasks = Task.query.filter_by(is_active=True).all()
        
        if not persons:
            return jsonify({'success': False, 'error': 'No hay personas activas'}), 400
        if not tasks:
            return jsonify({'success': False, 'error': 'No hay tareas activas'}), 400
        
        # Store data in memory BEFORE any DB operations
        persons_list = [{'id': p.id, 'name': p.name} for p in persons]
        tasks_list = [{'id': t.id, 'name': t.name, 'effort_points': t.effort_points} for t in tasks]
        
        # Deactivate previous assignments
        if clear_previous:
            Assignment.query.update({'is_active': False})
            db.session.commit()
        
        # Shuffle and assign
        import random
        random_tasks = list(tasks_list)
        random.shuffle(random_tasks)
        
        effort = {p['id']: 0 for p in persons_list}
        assignments_data = []
        
        for task in random_tasks:
            # Find person with minimum effort
            min_effort = min(effort.values())
            candidates = [p for p in persons_list if effort[p['id']] == min_effort]
            person = random.choice(candidates)
            
            # Create assignment
            assignment = Assignment(
                person_id=person['id'],
                task_id=task['id'],
                assigned_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(assignment)
            
            # Track for response
            assignments_data.append({
                'person_id': person['id'],
                'person_name': person['name'],
                'task_id': task['id'],
                'task_name': task['name'],
                'effort_points': task['effort_points']
            })
            
            effort[person['id']] += task['effort_points']
        
        # Single commit for all
        db.session.commit()
        
        # Build response from memory data
        by_person = {}
        for row in assignments_data:
            pid = row['person_id']
            if pid not in by_person:
                by_person[pid] = {
                    'person_id': pid,
                    'person_name': row['person_name'],
                    'tasks': [],
                    'total_effort': 0
                }
            by_person[pid]['tasks'].append({
                'id': row['task_id'],
                'name': row['task_name'],
                'effort_points': row['effort_points']
            })
            by_person[pid]['total_effort'] += row['effort_points']
        
        return jsonify({
            'success': True,
            'data': {'assignments': list(by_person.values())},
            'message': 'Asignaciones generadas'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        tb = traceback.format_exc()
        # Print to stderr for debugging
        import sys
        print(f"ERROR: {tb}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': tb
        }), 500

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
