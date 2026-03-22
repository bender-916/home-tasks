"""
Routes for managing persons.
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Person

persons_bp = Blueprint('persons', __name__)


@persons_bp.route('', methods=['GET'])
def get_persons():
    """List all persons."""
    persons = Person.query.all()
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in persons],
        'count': len(persons)
    })


@persons_bp.route('/<int:person_id>', methods=['GET'])
def get_person(person_id):
    """Get a person by ID."""
    person = Person.query.get(person_id)
    if not person:
        return jsonify({'success': False, 'error': 'Persona no encontrada'}), 404
    return jsonify({'success': True, 'data': person.to_dict()})


@persons_bp.route('', methods=['POST'])
def create_person():
    """Create a new person."""
    data = request.get_json() or {}
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'El nombre es requerido'}), 400
    
    name = data['name'].strip()
    
    # Check for duplicates
    if Person.query.filter_by(name=name).first():
        return jsonify({'success': False, 'error': 'Ya existe una persona con ese nombre'}), 409
    
    # Create person
    person = Person(
        name=name,
        color=data.get('color', '#3B82F6'),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(person)
    db.session.commit()
    
    return jsonify({'success': True, 'data': person.to_dict()}), 201


@persons_bp.route('/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    """Update a person."""
    person = Person.query.get(person_id)
    if not person:
        return jsonify({'success': False, 'error': 'Persona no encontrada'}), 404
    
    data = request.get_json() or {}
    
    # Update fields
    if 'name' in data:
        name = data['name'].strip()
        # Check for duplicates (excluding current person)
        existing = Person.query.filter_by(name=name).first()
        if existing and existing.id != person_id:
            return jsonify({'success': False, 'error': 'Ya existe una persona con ese nombre'}), 409
        person.name = name
    
    if 'color' in data:
        person.color = data['color']
    
    if 'is_active' in data:
        person.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({'success': True, 'data': person.to_dict()})


@persons_bp.route('/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    """Delete a person."""
    person = Person.query.get(person_id)
    if not person:
        return jsonify({'success': False, 'error': 'Persona no encontrada'}), 404
    
    db.session.delete(person)
    db.session.commit()
    
    return '', 204
