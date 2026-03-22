"""Assignment service for task distribution logic."""
import random
from datetime import datetime
from typing import List, Dict, Any
from ..models import db, Person, Task, Assignment


class AssignmentService:
    """Service for generating and managing task assignments."""

    @staticmethod
    def generate_assignments(strategy: str = 'balanced', clear_previous: bool = True) -> Dict[str, Any]:
        """
        Generate new task assignments using the specified strategy.
        
        Args:
            strategy: Assignment strategy ('random', 'balanced', 'rotation')
            clear_previous: Whether to deactivate previous assignments
            
        Returns:
            Dictionary with assignment results
        """
        # Get active persons and tasks
        active_persons = Person.query.filter_by(is_active=True).all()
        active_tasks = Task.query.filter_by(is_active=True).all()

        if not active_persons:
            return {
                'success': False,
                'error': 'No hay personas activas para asignar tareas'
            }
        
        if not active_tasks:
            return {
                'success': False,
                'error': 'No hay tareas activas para asignar'
            }

        # Deactivate previous assignments if requested
        if clear_previous:
            Assignment.query.update({'is_active': False})
            db.session.commit()

        # Generate new assignments based on strategy
        if strategy == 'random':
            assignments = AssignmentService._random_assignment(active_persons, active_tasks)
        elif strategy == 'rotation':
            assignments = AssignmentService._rotation_assignment(active_persons, active_tasks)
        else:  # balanced (default)
            assignments = AssignmentService._balanced_assignment(active_persons, active_tasks)

        # Save assignments
        for assignment in assignments:
            db.session.add(assignment)
        db.session.commit()

        # Format response
        result = AssignmentService._format_assignment_result(assignments)
        result['success'] = True
        result['message'] = 'Asignaciones generadas exitosamente'
        result['generated_at'] = datetime.utcnow().isoformat() + 'Z'

        return result

    @staticmethod
    def _random_assignment(persons: List[Person], tasks: List[Task]) -> List[Assignment]:
        """Random assignment - each task to a random person."""
        assignments = []
        for task in tasks:
            person = random.choice(persons)
            assignments.append(Assignment(
                person_id=person.id,
                task_id=task.id,
                assigned_at=datetime.utcnow()
            ))
        return assignments

    @staticmethod
    def _balanced_assignment(persons: List[Person], tasks: List[Task]) -> List[Assignment]:
        """
        Balanced assignment - distribute tasks considering effort points.
        Each person gets roughly equal total effort.
        """
        # Shuffle tasks for randomness
        shuffled_tasks = tasks.copy()
        random.shuffle(shuffled_tasks)

        # Track effort per person
        effort_tracking = {p.id: 0 for p in persons}
        assignments = []

        for task in shuffled_tasks:
            # Find person with minimum effort
            min_person_id = min(effort_tracking, key=effort_tracking.get)
            
            assignments.append(Assignment(
                person_id=min_person_id,
                task_id=task.id,
                assigned_at=datetime.utcnow()
            ))
            
            # Update effort tracking
            effort_tracking[min_person_id] += task.effort_points

        return assignments

    @staticmethod
    def _rotation_assignment(persons: List[Person], tasks: List[Task]) -> List[Assignment]:
        """
        Rotation assignment - tries to avoid repeating previous assignments.
        Falls back to balanced if no history exists.
        """
        # Get previous assignments for rotation logic
        previous_assignments = Assignment.query.filter_by(is_active=False).order_by(
            Assignment.created_at.desc()
        ).limit(100).all()
        
        if not previous_assignments:
            return AssignmentService._balanced_assignment(persons, tasks)

        # Build history of person-task pairs
        history = set()
        for a in previous_assignments:
            history.add((a.person_id, a.task_id))

        # Track effort per person
        effort_tracking = {p.id: 0 for p in persons}
        assignments = []

        # Sort persons by who did least recently
        person_last_assigned = {}
        for a in reversed(previous_assignments):
            if a.person_id not in person_last_assigned:
                person_last_assigned[a.person_id] = a.created_at

        # Sort tasks by effort (higher first for better distribution)
        sorted_tasks = sorted(tasks, key=lambda t: t.effort_points, reverse=True)

        for task in sorted_tasks:
            # Find best person (avoiding history, then by effort)
            available_persons = [
                p for p in persons 
                if (p.id, task.id) not in history
            ]
            
            if not available_persons:
                available_persons = persons
            
            # Choose person with minimum effort
            person = min(available_persons, key=lambda p: effort_tracking[p.id])
            
            assignments.append(Assignment(
                person_id=person.id,
                task_id=task.id,
                assigned_at=datetime.utcnow()
            ))
            
            effort_tracking[person.id] += task.effort_points

        return assignments

    @staticmethod
    def _format_assignment_result(assignments: List[Assignment]) -> Dict[str, Any]:
        """Format assignments for API response."""
        # Group by person
        person_tasks = {}
        for a in assignments:
            if a.person_id not in person_tasks:
                person_tasks[a.person_id] = {
                    'person_id': a.person_id,
                    'person_name': a.person.name if a.person else None,
                    'person_color': a.person.color if a.person else None,
                    'tasks': [],
                    'total_effort': 0
                }
            
            task_dict = a.task.to_dict() if a.task else None
            if task_dict:
                person_tasks[a.person_id]['tasks'].append({
                    'id': task_dict['id'],
                    'name': task_dict['name'],
                    'room': task_dict['room'],
                    'effort_points': task_dict['effort_points']
                })
                person_tasks[a.person_id]['total_effort'] += task_dict['effort_points']

        return {
            'assignments': list(person_tasks.values()),
            'total_assignments': len(assignments)
        }

    @staticmethod
    def get_current_assignments() -> Dict[str, Any]:
        """Get all active assignments."""
        assignments = Assignment.query.filter_by(is_active=True).all()
        
        if not assignments:
            return {
                'success': True,
                'data': [],
                'generated_at': None
            }

        # Get the earliest assignment date as generated_at
        generated_at = min(a.assigned_at for a in assignments)

        return {
            'success': True,
            'data': [a.to_dict() for a in assignments],
            'generated_at': generated_at.isoformat() + 'Z' if generated_at else None
        }

    @staticmethod
    def complete_assignment(assignment_id: int) -> Dict[str, Any]:
        """Mark an assignment as completed."""
        assignment = Assignment.query.get(assignment_id)
        
        if not assignment:
            return {
                'success': False,
                'error': 'Asignación no encontrada'
            }

        assignment.completed_at = datetime.utcnow()
        assignment.is_active = False
        db.session.commit()

        return {
            'success': True,
            'data': assignment.to_dict()
        }
