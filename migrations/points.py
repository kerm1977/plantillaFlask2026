# migrations/points.py - Migración para el motor de puntuación
from sqlalchemy import text, inspect
from db import db


def _migrate_event_puntos():
    try:
        db.session.execute(text('ALTER TABLE event ADD COLUMN puntos INTEGER DEFAULT 0'))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = str(e).lower()
        if 'duplicate column name' in msg or 'already exists' in msg:
            return
        raise


def _migrate_hiker_points():
    from models_core import HikerPoints
    if not inspect(db.engine).has_table('hiker_points'):
        HikerPoints.__table__.create(db.engine)
