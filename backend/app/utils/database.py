"""
Database initialization and utilities.
"""
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app import db


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign keys and WAL mode."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def init_db():
    """Initialize the database."""
    db.create_all()


def reset_db():
    """Reset the database (for testing)."""
    db.drop_all()
    db.create_all()
