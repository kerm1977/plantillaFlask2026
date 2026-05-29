from flask import render_template, session, redirect, url_for, jsonify, request
from models import Notification, Event, Hiker, Publicacion, LogoConfig
from datetime import datetime, date
from sqlalchemy import func
from db import db
from routes import bp


@bp.route('/')
def home():
    notifications = Notification.query.all()
    today = date.today()
    birthday_hikers = Hiker.query.filter(
        func.strftime('%m-%d', Hiker.fecha_nacimiento) == today.strftime('%m-%d'),
        Hiker.fecha_nacimiento != None
    ).all()
    return render_template('home.html', notifications=notifications, birthday_hikers=birthday_hikers)


@bp.route('/api/eventos-activos')
def api_eventos_activos():
    eventos = []
    # Eventos de caminatas
    caminatas = Event.query.filter_by(is_active=True).all()
    for ev in caminatas:
        eventos.append({
            'nombre': ev.nombre,
            'url': f'/eventos/{ev.id}'
        })
    # Eventos especiales/publicaciones
    publicaciones = Publicacion.query.filter_by(is_active=True).all()
    for pub in publicaciones:
        eventos.append({
            'nombre': pub.nombre,
            'url': f'/eventos/{pub.id}'
        })
    return jsonify(eventos)


@bp.route('/api/logo-config', methods=['GET'])
def api_get_logo_config():
    config = LogoConfig.query.first()
    if not config:
        # Crear configuración por defecto
        config = LogoConfig()
        db.session.add(config)
        db.session.commit()
    return jsonify({
        'mostrar': config.mostrar,
        'enlace': config.enlace,
        'tamaño_pc': config.tamaño_pc,
        'tamaño_mobile': config.tamaño_mobile,
        'posicion_left': config.posicion_left,
        'posicion_bottom': config.posicion_bottom,
        'nombre_archivo': config.nombre_archivo
    })


@bp.route('/api/logo-config', methods=['POST'])
def api_save_logo_config():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.get_json()
    config = LogoConfig.query.first()

    if not config:
        config = LogoConfig()
        db.session.add(config)

    config.mostrar = data.get('mostrar', True)
    config.enlace = data.get('enlace', '')
    config.tamaño_pc = data.get('tamaño_pc', 150)
    config.tamaño_mobile = data.get('tamaño_mobile', 120)
    config.posicion_left = data.get('posicion_left', 20)
    config.posicion_bottom = data.get('posicion_bottom', 100)
    config.nombre_archivo = data.get('nombre_archivo', 'logosueños.png')
    config.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/profile')
def profile():
    from models import User
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.home'))
    return render_template('perfil.html', user=user)


@bp.route('/calendario')
def calendario():
    # Protegemos la ruta para que solo Superusuarios puedan acceder
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    
    # Obtener todos los eventos ordenados por fecha
    eventos_db = Event.query.order_by(Event.fecha_inicio).all()
    
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    eventos_procesados = []
    for ev in eventos_db:
        if getattr(ev, 'fecha_inicio', None):
            fecha_dt = ev.fecha_inicio
            
            # Blindaje: Por si la fecha viene como string desde SQLite
            if isinstance(fecha_dt, str):
                try:
                    fecha_dt = datetime.strptime(fecha_dt, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        fecha_dt = datetime.strptime(fecha_dt, '%d/%m/%Y').date()
                    except ValueError:
                        continue # Si el formato es totalmente ilegible, lo omite sin crashear
            
            # Extracción segura de mes y día
            mes_num = getattr(fecha_dt, 'month', 1)
            dia_num = getattr(fecha_dt, 'day', 1)
            
            eventos_procesados.append({
                'mes': meses_es.get(mes_num, 'S/M'),
                'dia': str(dia_num),
                'nombre': getattr(ev, 'nombre_lugar', 'Caminata'),
                'categoria': getattr(ev, 'actividad', 'Caminata') or 'Caminata',
                'dificultad': getattr(ev, 'dificultad', 'Moderada') or 'Moderada'
            })
    
    # Pasamos los eventos ya procesados al HTML sin errores de Json
    return render_template('calendario.html', eventos=eventos_procesados)
