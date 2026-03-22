"""Script to seed the database with sample data."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from app.models.models import db, Person, Task


def seed_data():
    """Populate database with sample data."""
    app = create_app('development')
    
    with app.app_context():
        # Check if data already exists
        if Person.query.first() is not None:
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding database...")
        
        # Create sample persons
        persons = [
            Person(name='Juan', color='#3B82F6'),
            Person(name='María', color='#EF4444'),
            Person(name='Pedro', color='#10B981'),
            Person(name='Ana', color='#F59E0B'),
        ]
        
        for person in persons:
            db.session.add(person)
        
        # Create sample tasks
        tasks = [
            Task(name='Lavar platos', description='Lavar todos los platos del día', room='Cocina', effort_points=2),
            Task(name='Sacar basura', description='Sacar los contenedores', room='Cocina', effort_points=1),
            Task(name='Limpiar baño', description='Limpiar baño principal', room='Baño', effort_points=3),
            Task(name='Barrer salón', description='Barrer y fregar el salón', room='Salón', effort_points=2),
            Task(name='Hacer camas', description='Hacer las camas', room='Dormitorio', effort_points=1),
            Task(name='Regar plantas', description='Regar todas las plantas', room='Terraza', effort_points=1),
            Task(name='Limpiar cocina', description='Limpiar encimeras y suelo', room='Cocina', effort_points=2),
            Task(name='Organizar recibidor', description='Ordenar zapatos y abrigos', room='Recibidor', effort_points=1),
        ]
        
        for task in tasks:
            db.session.add(task)
        
        db.session.commit()
        print(f"Created {len(persons)} persons and {len(tasks)} tasks.")


if __name__ == '__main__':
    seed_data()
