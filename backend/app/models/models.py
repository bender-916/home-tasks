"""
SQLAlchemy models for the Home Tasks application.
"""
from datetime import datetime
from app import db


class Person(db.Model):
    """Model representing a person (household member)."""
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#3B82F6')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = db.relationship('Assignment', backref='person', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }

    def __repr__(self):
        return f'<Person {self.name}>'


class Task(db.Model):
    """Model representing a task/room to be assigned."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    room = db.Column(db.String(50), nullable=True)
    effort_points = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = db.relationship('Assignment', backref='task', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'room': self.room,
            'effort_points': self.effort_points,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }

    def __repr__(self):
        return f'<Task {self.name}>'


class Assignment(db.Model):
    """Model representing a task assignment to a person."""
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'task_id': self.task_id,
            'person': {
                'id': self.person.id,
                'name': self.person.name,
                'color': self.person.color
            } if self.person else None,
            'task': {
                'id': self.task.id,
                'name': self.task.name,
                'room': self.task.room,
                'effort_points': self.task.effort_points
            } if self.task else None,
            'assigned_at': self.assigned_at.isoformat() + 'Z' if self.assigned_at else None,
            'completed_at': self.completed_at.isoformat() + 'Z' if self.completed_at else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Assignment person={self.person_id} task={self.task_id}>'
