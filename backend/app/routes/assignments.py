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
            return jsonify({'success': False, 'error': 'No hay personas activas'}), 400
        if not tasks:
            return jsonify({'success': False, 'error': 'No hay tareas activas'}), 400

        # Deactivate previous
        if clear_previous:
            Assignment.query.update({'is_active': False})
            db.session.commit()

        # Crear asignaciones
        assignments_data = []
        tasks_list = list(tasks)
        random.shuffle(tasks_list)
        effort_tracking = {p.id: 0 for p in persons}

        for task in tasks_list:
            min_effort = min(effort_tracking.values())
            candidates = [p for p in persons if effort_tracking[p.id] == min_effort]
            selected_person = random.choice(candidates)

            assignment = Assignment(
                person_id=selected_person.id,
                task_id=task.id,
                assigned_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(assignment)
            db.session.flush()  # Get ID without commit

            # Guardar datos para respuesta
            assignments_data.append({
                'assignment_id': assignment.id,
                'person_id': selected_person.id,
                'person_name': selected_person.name,
                'task_id': task.id,
                'task_name': task.name,
                'effort_points': task.effort_points
            })
            effort_tracking[selected_person.id] += task.effort_points

        db.session.commit()

        # Formatear respuesta desde los datos guardados (sin lazy loading)
        result = {}
        for item in assignments_data:
            pid = item['person_id']
            if pid not in result:
                result[pid] = {
                    'person_id': pid,
                    'person_name': item['person_name'],
                    'tasks': [],
                    'total_effort': 0
                }
            result[pid]['tasks'].append({
                'id': item['task_id'],
                'name': item['task_name'],
                'effort_points': item['effort_points']
            })
            result[pid]['total_effort'] += item['effort_points']

        return jsonify({
            'success': True,
            'data': {'assignments': list(result.values())},
            'message': 'Asignaciones generadas'
        }), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
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
