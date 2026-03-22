"""Script to initialize the database."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from app.models.models import db


def init_database():
    """Initialize the database with tables and indexes."""
    app = create_app('production')
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database initialized successfully!")


if __name__ == '__main__':
    init_database()
