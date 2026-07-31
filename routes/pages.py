from flask import render_template, session, redirect, url_for, jsonify, request, make_response
from models import Notification, Event, Hiker, Publicacion, LogoConfig
from models_core import EventDateChange
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
    try:
        # Eventos de caminatas
        caminatas = Event.query.filter_by(is_active=True).all()
        for ev in caminatas:
            eventos.append({
                'nombre': getattr(ev, 'nombre_lugar', 'Caminata'),
                'url': f'/eventos/{ev.id}'
            })
        # Eventos especiales/publicaciones
        publicaciones = Publicacion.query.filter_by(is_active=True).all()
        for pub in publicaciones:
            eventos.append({
                'nombre': pub.nombre,
                'url': f'/eventos/{pub.id}'
            })
    except Exception as e:
        print(f"Error en api_eventos_activos: {e}")
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


@bp.route('/gestor-fechas')
def gestor_fechas():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    eventos_db = Event.query.all()
    eventos_procesados = []
    for ev in eventos_db:
        fecha_str = getattr(ev, 'fecha_inicio', None) or getattr(ev, 'fecha_unica', None)
        fecha_completa = ''
        if fecha_str:
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    fecha_completa = datetime.strptime(str(fecha_str), fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
        # Último cambio (anterior) y lista de fechas asignadas
        cambios = EventDateChange.query.filter_by(event_id=ev.id).order_by(EventDateChange.cambiado_at.desc()).all()
        ultimo_cambio = cambios[0] if cambios else None
        fecha_anterior = ultimo_cambio.fecha_anterior if ultimo_cambio else ''
        historial_fechas = []
        if fecha_completa and (not cambios or cambios[0].fecha_nueva != fecha_completa):
            historial_fechas.append({'fecha': fecha_completa, 'cambiado_at': '—'})
        for c in cambios:
            if c.fecha_nueva:
                historial_fechas.append({
                    'fecha': c.fecha_nueva,
                    'cambiado_at': c.cambiado_at.strftime('%d/%m/%Y %H:%M') if c.cambiado_at else ''
                })
        eventos_procesados.append({
            'id': ev.id,
            'nombre': getattr(ev, 'nombre_lugar', 'Caminata'),
            'fecha_completa': fecha_completa,
            'fecha_anterior': fecha_anterior,
            'historial_fechas': historial_fechas
        })
    eventos_procesados.sort(key=lambda x: x['fecha_completa'] or '9999')
    resp = make_response(render_template('gestor_fechas.html', eventos=eventos_procesados))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp



@bp.route('/api/eventos/<int:event_id>/mover-fecha', methods=['POST'])
def mover_evento_fecha(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    evento = Event.query.get_or_404(event_id)
    data = request.get_json()
    nueva_fecha = data.get('nueva_fecha')
    
    if not nueva_fecha:
        return jsonify({'error': 'Fecha requerida'}), 400
    
    try:
        fecha_dt = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
        fecha_anterior = getattr(evento, 'fecha_inicio', None) or getattr(evento, 'fecha_unica', None)
        print(f"DEBUG: Moviendo evento {event_id} de {fecha_anterior} a {fecha_dt}")
        evento.fecha_inicio = fecha_dt.strftime('%Y-%m-%d')
        cambio = EventDateChange(
            event_id=event_id,
            fecha_anterior=fecha_anterior or '',
            fecha_nueva=nueva_fecha,
            usuario=session.get('email', 'Sistema')
        )
        db.session.add(cambio)
        db.session.commit()
        print(f"DEBUG: Evento movido exitosamente")
        return jsonify({'ok': True, 'nueva_fecha': nueva_fecha})
    except ValueError as e:
        print(f"ERROR: Formato de fecha inválido: {e}")
        return jsonify({'error': 'Formato de fecha inválido (YYYY-MM-DD)'}), 400
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/eventos/<int:event_id>/borrar-fecha', methods=['POST'])
def borrar_evento_fecha(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    evento = Event.query.get_or_404(event_id)
    try:
        fecha_anterior = getattr(evento, 'fecha_inicio', None) or getattr(evento, 'fecha_unica', None)
        evento.fecha_inicio = None
        evento.fecha_unica = None
        cambio = EventDateChange(
            event_id=event_id,
            fecha_anterior=fecha_anterior or '',
            fecha_nueva='',
            usuario=session.get('email', 'Sistema')
        )
        db.session.add(cambio)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
