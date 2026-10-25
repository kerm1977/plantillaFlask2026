# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# (listados de caminatas en pages_caminatas.py, gestor de fechas en pages_fechas.py)
from flask import render_template, session, redirect, url_for, jsonify, request, current_app, abort
from itsdangerous import URLSafeSerializer, BadSignature
from models import Notification, Event, Hiker, Publicacion, LogoConfig, SiteContent, HomeMedia
from modules.points_engine import get_points_engine
from datetime import datetime, date
from sqlalchemy import func
from db import db
from routes import bp
from helpers.holidays import get_today_holiday, get_background_music
from helpers.active_note import get_active_note


def _home_context():
    notifications = Notification.query.all()
    today = date.today()
    birthday_hikers = Hiker.query.filter(
        func.strftime('%m-%d', Hiker.fecha_nacimiento) == today.strftime('%m-%d'),
        Hiker.fecha_nacimiento != None
    ).all()
    today_holiday = get_today_holiday(today)
    if today_holiday and today_holiday.get('superuser_only') and session.get('role') not in ('Superusuario', 'Administrador'):
        today_holiday = None
    active_note = get_active_note()
    if active_note and not active_note.get('is_public') and not today_holiday and session.get('role') not in ('Superusuario', 'Administrador'):
        active_note = None
    background_music = get_background_music()
    return dict(notifications=notifications, birthday_hikers=birthday_hikers, today_holiday=today_holiday, active_note=active_note, background_music=background_music)


@bp.route('/')
def home():
    home_media = HomeMedia.query.filter_by(is_active=True).order_by(HomeMedia.sort_order.asc(), HomeMedia.id.asc()).all()

    public_accion = None
    public_user_id = None
    token = request.args.get('token')
    if token:
        secret = current_app.config.get('SECRET_KEY') or 'dev-secret-change-me'
        serializer = URLSafeSerializer(secret, salt='public-user-link')
        try:
            data = serializer.loads(token)
            public_accion = data.get('accion')
            public_user_id = data.get('user_id')
        except BadSignature:
            pass

    return render_template('home.html', home_media=home_media, public_accion=public_accion, public_user_id=public_user_id)


from routes.about import DEFAULT_SITE_CONTENT


def _get_site_text(key):
    row = SiteContent.query.filter_by(key=key).first()
    return row.value if row else DEFAULT_SITE_CONTENT.get(key, '')


@bp.route('/nuestra-historia')
def nuestra_historia():
    return render_template('nuestra_historia.html', historia_text=_get_site_text('quienes_somos'))


@bp.route('/mision')
def mision():
    return render_template('mision.html', mision_text=_get_site_text('mision'))


@bp.route('/nuestra-oracion')
def nuestra_oracion():
    return render_template('nuestra_oracion.html', oracion_text=_get_site_text('oracion'))


@bp.route('/terminos')
def terminos():
    return render_template('terminos.html')


@bp.route('/nuestra-musica')
def nuestra_musica():
    return render_template('nuestra_musica.html')


@bp.route('/quienes-somos')
def quienes_somos():
    return render_template('quienes_somos.html',
        historia_text=_get_site_text('quienes_somos'),
        mision_text=_get_site_text('mision'),
        oracion_text=_get_site_text('oracion'),
        equipo_text=_get_site_text('equipo'),
        musica_text=_get_site_text('musica'),
        is_super=session.get('role') == 'Superusuario'
    )


@bp.route('/api/eventos-activos')
def api_eventos_activos():
    eventos = []
    try:
        # Eventos de caminatas
        caminatas = Event.query.order_by(Event.id.desc()).all()
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


@bp.route('/tarjeta/<cedula>/<email>')
def tarjeta(cedula, email):
    from models import User
    hiker = Hiker.query.filter_by(cedula=(cedula or '').strip()).first()
    bound_email = (hiker.card_email or '').strip().lower() if hiker else ''
    if not hiker or not bound_email or bound_email != (email or '').strip().lower() or (hiker.status or 'Activo') == 'Bloqueado':
        abort(404)
    user = User.query.filter(func.lower(User.email) == bound_email).first()
    if not user:
        if hiker.telefono:
            user = User.query.filter_by(phone=hiker.telefono).first()
        if not user and hiker.nombre_completo:
            for u in User.query.all():
                if f'{u.name} {u.last_name_1} {u.last_name_2}'.strip().lower() == hiker.nombre_completo.strip().lower():
                    user = u
                    break
    engine = get_points_engine()
    puntos_total = engine.total_by_cedula(hiker.cedula)
    avatar_file = (user.avatar if user else None) or 'default.png'
    if avatar_file != 'default.png' and not avatar_file.startswith('uploads/'):
        avatar_file = 'uploads/' + avatar_file
    return render_template('tarjeta.html', user=user, hiker=hiker, card_email=bound_email, puntos_total=puntos_total, avatar_file=avatar_file)


@bp.route('/profile')
def profile():
    from models import User
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.home'))
    full_name = f'{user.name} {user.last_name_1} {user.last_name_2}'.strip()
    hiker = Hiker.query.filter_by(telefono=user.phone).first() if user.phone else None
    if not hiker:
        hiker = Hiker.query.filter_by(nombre_completo=full_name).first()
    puntos_cedula = hiker.cedula if hiker else ''
    engine = get_points_engine()
    puntos_total = engine.total_by_cedula(puntos_cedula) if puntos_cedula else 0
    puntos_history = engine.history_with_names(puntos_cedula) if puntos_cedula else []
    from modules.points_helpers import (get_puntos_password, get_puntos_admin_visible,
                                        get_notif_cutoff, personas_con_puntos)
    notif_cutoff = get_notif_cutoff(puntos_cedula)
    puntos_notificaciones = [r for r in puntos_history if r['tipo'] in ('obsequio', 'donacion_recibida') and (r.get('creado_at') or '') > notif_cutoff]
    todos_hikers = Hiker.query.order_by(Hiker.nombre_completo).all() if session.get('role') == 'Superusuario' else []
    caminatas_escaneadas = _build_escaneos(engine) if session.get('role') == 'Superusuario' else []
    return render_template('perfil.html', user=user, hiker=hiker, puntos_cedula=puntos_cedula,
                           puntos_total=puntos_total, puntos_history=puntos_history, puntos_notificaciones=puntos_notificaciones,
                           todos_hikers=todos_hikers, caminatas_escaneadas=caminatas_escaneadas,
                           puntos_password=get_puntos_password(), puntos_pwd_msg=session.pop('puntos_pwd_msg', None),
                           puntos_pwd_visible=get_puntos_admin_visible())


def _build_escaneos(engine):
    """Resumen de caminatas/eventos con puntos escaneados (solo superusuario)."""
    from models import HikerPoints, EventRegistration, PuntosEvento
    hoy = date.today()
    grupos = {}
    recs = HikerPoints.query.filter(
        HikerPoints.tipo.in_(['participacion', 'evento']),
        db.or_(HikerPoints.event_id != None, HikerPoints.puntos_evento_id != None)
    ).order_by(HikerPoints.created_at.desc()).all()
    for r in recs:
        key = ('cam', r.event_id) if r.event_id else ('pe', r.puntos_evento_id)
        grupos.setdefault(key, []).append(r)

    hikers_cache = {}
    totals_cache = {}

    def _hiker(ced):
        if ced not in hikers_cache:
            hikers_cache[ced] = Hiker.query.filter_by(cedula=ced).first()
        return hikers_cache[ced]

    def _total(ced):
        if ced not in totals_cache:
            totals_cache[ced] = engine.total_by_cedula(ced)
        return totals_cache[ced]

    resultado = []
    for (kind, oid), rows in grupos.items():
        if kind == 'cam':
            ev = Event.query.get(oid)
            if not ev:
                continue
            nombre, pts_cfg = ev.nombre_lugar, ev.puntos or 0
            url = url_for('main.ver_caminata_2027', event_id=oid)
        else:
            pe = PuntosEvento.query.get(oid)
            if not pe:
                continue
            nombre, pts_cfg = pe.nombre, pe.puntos or 0
            url = url_for('main.puntos_evento_qr_page', pid=oid)

        retiradas = {x.cedula for x in HikerPoints.query.filter_by(
            tipo='retiro', event_id=oid if kind == 'cam' else None,
            puntos_evento_id=oid if kind == 'pe' else None).all()}

        personas = []
        for r in rows:
            h = _hiker(r.cedula)
            es_hoy = bool(r.created_at and r.created_at.date() == hoy)
            personas.append({
                'nombre': h.nombre_completo if h else r.cedula,
                'cedula': r.cedula,
                'puntos': r.points,
                'total': _total(r.cedula),
                'hora': r.created_at.strftime('%d/%m/%Y %H:%M') if r.created_at else '',
                'hoy': es_hoy,
                'retirado': r.cedula in retiradas,
                'operador': r.created_by or '',
            })

        pendientes = []
        if kind == 'cam':
            escaneadas = {r.cedula for r in rows}
            for reg in EventRegistration.query.filter_by(event_id=oid).all():
                h = Hiker.query.get(reg.hiker_id)
                if h and h.cedula not in escaneadas:
                    pendientes.append({'nombre': h.nombre_completo, 'cedula': h.cedula,
                                       'telefono': h.telefono or ''})

        resultado.append({
            'kind': kind,
            'id': oid,
            'nombre': nombre,
            'puntos_config': pts_cfg,
            'url': url,
            'personas': personas,
            'pendientes': pendientes,
            'total_generado': sum(p['puntos'] for p in personas),
            'hoy_puntos': sum(p['puntos'] for p in personas if p['hoy']),
            'hoy_count': sum(1 for p in personas if p['hoy']),
            'ultimo': rows[0].created_at if rows else None,
        })
    resultado.sort(key=lambda e: e['ultimo'] or datetime.min, reverse=True)
    return resultado


@bp.route('/public/usuarios/<token>')
def public_usuarios(token):
    return redirect(url_for('main.home', token=token))
