# models_home_media.py
from db import db
from datetime import datetime


class HomeMedia(db.Model):
    __tablename__ = 'home_media'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False, default='image')
    # image | youtube | facebook | link
    title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'url': self.url,
            'filename': self.filename,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
