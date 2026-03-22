"""
Flask application factory.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                static_folder='../frontend',
                static_url_path='')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    from app.config import get_config
    app.config.from_object(get_config())
    
    # Ensure data directory exists
    db_path = app.config.get('DATABASE_PATH', '/data/home_tasks.db')
    if db_path != ':memory:':
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()
        from app.utils.database import init_db
        init_db()
    
    # Register blueprints
    from app.routes.persons import persons_bp
    from app.routes.tasks import tasks_bp
    from app.routes.assignments import assignments_bp
    
    app.register_blueprint(persons_bp, url_prefix='/api/persons')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        from datetime import datetime
        return {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    # Stats endpoint
    @app.route('/api/stats')
    def stats():
        from app.models.models import Person, Task, Assignment
        from datetime import datetime, timedelta
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        return {
            'success': True,
            'data': {
                'persons': {
                    'total': Person.query.count(),
                    'active': Person.query.filter_by(is_active=True).count()
                },
                'tasks': {
                    'total': Task.query.count(),
                    'active': Task.query.filter_by(is_active=True).count()
                },
                'assignments': {
                    'active': Assignment.query.filter_by(is_active=True).count(),
                    'completed_today': Assignment.query.filter(
                        Assignment.completed_at >= today_start
                    ).count()
                }
            }
        }
    
    # Serve frontend
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    return app
