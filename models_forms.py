from db import db
from datetime import datetime

class Form(db.Model):
    __tablename__ = 'form'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True)
    form_type = db.Column(db.String(20), default='registro')
    is_active = db.Column(db.Boolean, default=True)
    allow_edit = db.Column(db.Boolean, default=False)
    show_nombre = db.Column(db.Boolean, default=True)
    show_cedula = db.Column(db.Boolean, default=False)
    show_fecha = db.Column(db.Boolean, default=False)
    show_email = db.Column(db.Boolean, default=False)
    show_edad = db.Column(db.Boolean, default=False)
    show_telefono = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    fields = db.relationship('FormField', backref='form', lazy=True, cascade='all, delete-orphan',
                             order_by='FormField.order')
    responses = db.relationship('FormResponse', backref='form', lazy=True, cascade='all, delete-orphan')

class FormField(db.Model):
    __tablename__ = 'form_field'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    field_type = db.Column(db.String(30), nullable=False)
    label = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    correct_answer = db.Column(db.Text)

class FormResponse(db.Model):
    __tablename__ = 'form_response'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    edit_token = db.Column(db.String(64), unique=True)
    nombre_completo = db.Column(db.String(200))
    cedula = db.Column(db.String(50))
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(50))
    edad = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float)
    total_questions = db.Column(db.Integer)
    answers = db.relationship('FormAnswer', backref='response', lazy=True, cascade='all, delete-orphan')

class FormAnswer(db.Model):
    __tablename__ = 'form_answer'
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey('form_response.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('form_field.id'), nullable=False)
    value = db.Column(db.Text)
    file_path = db.Column(db.String(500))
