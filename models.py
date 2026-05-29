# models.py
from db import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default='Usuario') 
    weight = db.Column(db.Integer, default=1) 
    avatar = db.Column(db.String(255), default='default.png')
    name = db.Column(db.String(100), nullable=False)
    last_name_1 = db.Column(db.String(100), nullable=False)
    last_name_2 = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    dob = db.Column(db.Date)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Activo') 
    
    # Campos de Información Adicional
    whatsapp = db.Column(db.String(20))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    address = db.Column(db.String(255))
    institution = db.Column(db.String(200))
    other_info = db.Column(db.Text)
    
    reset_token = db.Column(db.String(64))
    reset_expires = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster = db.Column(db.String(255)) 
    nombre_lugar = db.Column(db.String(200), nullable=False)
    dificultad = db.Column(db.String(50))
    actividad = db.Column(db.String(100))
    moneda = db.Column(db.String(5))
    precio = db.Column(db.Integer)
    reserva = db.Column(db.Integer)
    capacidad = db.Column(db.String(50))
    sinpe = db.Column(db.String(100))
    cuenta = db.Column(db.String(200))
    
    solo_chat = db.Column(db.Boolean, default=False)
    logistica_segura = db.Column(db.Boolean, default=False)
    is_sold_out = db.Column(db.Boolean, default=False)

    dias = db.Column(db.Integer, default=1)
    fecha_unica = db.Column(db.String(50))
    fecha_inicio = db.Column(db.String(50))
    fecha_regreso = db.Column(db.String(50))
    hora_salida = db.Column(db.String(50))
    lugar_salida = db.Column(db.String(200))
    puntos_recogida = db.Column(db.Text)
    itinerario = db.Column(db.Text)
    incluye = db.Column(db.Text) 
    gpx_filename = db.Column(db.String(255))
    gpx_password = db.Column(db.String(50))
    organicmaps_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    type_notif = db.Column(db.String(50)) 
    message = db.Column(db.Text)

class SiteContent(db.Model):
    __tablename__ = 'site_content'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

class Hiker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    tipo_sangre = db.Column(db.String(10))
    fecha_nacimiento = db.Column(db.Date) 
    alergias = db.Column(db.Text)
    enfermedades_cronicas = db.Column(db.Text)
    contacto_emergencia_nombre = db.Column(db.String(200))
    contacto_emergencia_telefono = db.Column(db.String(20))
    pin_secreto = db.Column(db.String(20), unique=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    hiker_id = db.Column(db.Integer, db.ForeignKey('hiker.id'), nullable=False)
    estado_pago = db.Column(db.String(50), default='Pendiente')
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================================
# SISTEMA DE FORMULARIOS DINÁMICOS
# ==========================================
class Form(db.Model):
    __tablename__ = 'form'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True)
    form_type = db.Column(db.String(20), default='registro')  # 'examen' o 'registro'
    is_active = db.Column(db.Boolean, default=True)
    allow_edit = db.Column(db.Boolean, default=False)
    # Triggers de visibilidad de campos personales
    show_nombre = db.Column(db.Boolean, default=True)
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
    field_type = db.Column(db.String(30), nullable=False)  # 'text', 'radio', 'checkbox', 'file'
    label = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text)  # JSON array para radio/checkbox
    order = db.Column(db.Integer, default=0)
    correct_answer = db.Column(db.Text)  # Para calificación automática


class FormResponse(db.Model):
    __tablename__ = 'form_response'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    edit_token = db.Column(db.String(64), unique=True)
    nombre_completo = db.Column(db.String(200))
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
    value = db.Column(db.Text)  # JSON para selecciones múltiples
    file_path = db.Column(db.String(500))


# ==========================================
# SISTEMA DE RIFAS
# ==========================================
class Raffle(db.Model):
    __tablename__ = 'raffle'
    id = db.Column(db.Integer, primary_key=True)
    raffle_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    prize = db.Column(db.String(500), nullable=False)
    detail = db.Column(db.Text, nullable=False)
    raffle_date = db.Column(db.Date, nullable=False)
    raffle_time = db.Column(db.String(50))
    image_filename = db.Column(db.String(255), nullable=False)
    winning_numbers = db.Column(db.Text, default='[]')  # JSON string
    sinpe_name_default = db.Column(db.String(200))
    sinpe_phone_default = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    selections = db.relationship('RaffleSelection', backref='raffle', lazy=True, cascade='all, delete-orphan')


class RaffleSelection(db.Model):
    __tablename__ = 'raffle_selection'
    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffle.id'), nullable=False)
    number = db.Column(db.String(5), nullable=False)  # 00-99
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=False)
    customer_cedula = db.Column(db.String(50))  # Nueva: cédula del cliente
    pin = db.Column(db.String(10), nullable=False)  # PIN de 4 dígitos alfanumérico
    selection_password = db.Column(db.String(100), nullable=False, default='', server_default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_canceled = db.Column(db.Boolean, default=False)
    payment_method = db.Column(db.String(50), default='No especificado')
    sinpe_name = db.Column(db.String(200))
    sinpe_phone = db.Column(db.String(50))
    __table_args__ = (db.UniqueConstraint('raffle_id', 'number', name='_raffle_number_uc'),)


# ==========================================
# SISTEMA DE PUBLICACIONES / EVENTOS
# ==========================================
class Publicacion(db.Model):
    __tablename__ = 'publicacion'
    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(200), nullable=False)
    logo_filename   = db.Column(db.String(255))
    flyer_filename  = db.Column(db.String(255))
    audio_filename  = db.Column(db.String(255))
    fecha_inicio    = db.Column(db.Date, nullable=False)
    fecha_fin       = db.Column(db.Date)
    descripcion     = db.Column(db.Text)
    tipo_evento     = db.Column(db.String(50))          # Caminata | Taller | Rifa
    rifa_url        = db.Column(db.String(500))
    rifa_url_2      = db.Column(db.String(500))
    lugar           = db.Column(db.String(200))
    punto_salida    = db.Column(db.String(200))
    hora_encuentro  = db.Column(db.String(50))
    recomendaciones = db.Column(db.Text)
    desc_caminata   = db.Column(db.Text)
    direccion       = db.Column(db.String(255))
    url_externa     = db.Column(db.String(500))
    mostrar         = db.Column(db.Text, default='[]')  # JSON list of visible fields
    sinpe_info         = db.Column(db.String(300))
    sinpe_info_2       = db.Column(db.String(300))
    sinpe_info_3       = db.Column(db.String(300))
    sinpe_info_4       = db.Column(db.String(300))
    cuenta_info        = db.Column(db.String(400))
    cuenta_info_2      = db.Column(db.String(400))
    cuenta_info_3      = db.Column(db.String(400))
    cuenta_info_4      = db.Column(db.String(400))
    cuentas_visibles   = db.Column(db.Text, default='[]')  # JSON list of visible account indices
    colaborar_detalle  = db.Column(db.String(300), default='Apoyo Sueños de Vida')
    telefono        = db.Column(db.String(50))
    whatsapp        = db.Column(db.String(50))
    facebook        = db.Column(db.String(300))
    instagram       = db.Column(db.String(300))
    tiktok          = db.Column(db.String(300))
    youtube         = db.Column(db.String(300))
    is_active       = db.Column(db.Boolean, default=True)
    monto_recaudado = db.Column(db.Float, default=0.0)


# ==========================================
# CONFIGURACIÓN DEL LOGO DE SUEÑOS
# ==========================================
class LogoConfig(db.Model):
    __tablename__ = 'logo_config'
    id = db.Column(db.Integer, primary_key=True)
    mostrar = db.Column(db.Boolean, default=True)
    enlace = db.Column(db.String(500))
    tamaño_pc = db.Column(db.Integer, default=150)
    tamaño_mobile = db.Column(db.Integer, default=120)
    posicion_left = db.Column(db.Integer, default=20)
    posicion_bottom = db.Column(db.Integer, default=100)
    nombre_archivo = db.Column(db.String(255), default='logosueños.png')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)