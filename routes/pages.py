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
    escaneos_data = _build_escaneos(engine) if session.get('role') == 'Superusuario' else {'caminatas': [], 'hoy': []}
    return render_template('perfil.html', user=user, hiker=hiker, puntos_cedula=puntos_cedula,
                           puntos_total=puntos_total, puntos_history=puntos_history, puntos_notificaciones=puntos_notificaciones,
                           todos_hikers=todos_hikers, caminatas_escaneadas=escaneos_data['caminatas'],
                           escaneos_hoy=escaneos_data['hoy'],
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

    hoy_lista = []
    for c in resultado:
        for p in c['personas']:
            if p['hoy']:
                hoy_lista.append({'nombre': p['nombre'], 'cedula': p['cedula'],
                                  'puntos': p['puntos'], 'total': p['total'],
                                  'hora': p['hora'], 'caminata': c['nombre']})
    return {'caminatas': resultado, 'hoy': hoy_lista}


@bp.route('/api/admin/estado_cuenta/<cedula>')
def admin_estado_cuenta(cedula):
    """Estado de cuenta completo de puntos de una persona (solo superusuario)."""
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    import re as _re
    from models import Hiker
    ced = _re.sub(r'\D', '', str(cedula))
    hiker = Hiker.query.filter_by(cedula=ced).first()
    if not hiker:
        return jsonify({'ok': False, 'error': 'Persona no encontrada'}), 404
    engine = get_points_engine()
    movs = [{
        'fecha': (r['creado_at'] or '')[:10],
        'hora': (r['creado_at'] or '')[11:16],
        'actividad': r['evento_nombre'] or (r['tipo'] or '').replace('_', ' ').capitalize(),
        'detalle': r['detalle'] or '',
        'puntos': r['puntos'],
        'tipo': r['tipo'],
        'operador': r.get('creado_por') or '',
    } for r in engine.history_with_names(ced)]
    return jsonify({'ok': True,
                    'nombre': hiker.nombre_completo,
                    'cedula': ced,
                    'telefono': hiker.telefono or '',
                    'pin': hiker.pin_secreto or '',
                    'total': engine.total_by_cedula(ced),
                    'ganados': sum(m['puntos'] for m in movs if m['puntos'] > 0),
                    'usados': -sum(m['puntos'] for m in movs if m['puntos'] < 0),
                    'generado': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'movimientos': movs})


@bp.route('/api/admin/puntos/export')
def admin_puntos_export():
    """Exporta TODA la información del sistema de puntos a un JSON descargable
    (solo superusuario): personas, movimientos, resúmenes y fidelidad."""
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    import json as _json
    from models import Hiker, HikerPoints, PuntosEvento, FidelidadAjuste, FidelidadLog

    hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
    pts = HikerPoints.query.order_by(HikerPoints.created_at, HikerPoints.id).all()
    events = {e.id: e for e in Event.query.all()}
    pevs = {p.id: p for p in PuntosEvento.query.all()}
    nombres = {h.cedula: h.nombre_completo for h in hikers}

    def _iso(dt):
        return dt.isoformat(sep=' ', timespec='seconds') if dt else None

    # Escaneos por caminata / evento de puntos
    esc_ev, esc_pe = {}, {}
    for r in pts:
        if r.event_id and r.tipo == 'participacion':
            s = esc_ev.setdefault(r.event_id, {'escaneos': 0, 'cedulas': set(), 'puntos': 0})
            s['escaneos'] += 1
            s['cedulas'].add(r.cedula)
            s['puntos'] += r.points or 0
        elif r.puntos_evento_id and r.tipo == 'evento':
            s = esc_pe.setdefault(r.puntos_evento_id, {'escaneos': 0, 'cedulas': set(), 'puntos': 0})
            s['escaneos'] += 1
            s['cedulas'].add(r.cedula)
            s['puntos'] += r.points or 0

    # Resumen por cédula: ganados (positivos), usados/redimidos (negativos), disponible (neto)
    resumen = {}
    for r in pts:
        s = resumen.setdefault(r.cedula, {'ganados': 0, 'usados': 0, 'disponible': 0, 'movimientos': 0})
        if r.points and r.points > 0:
            s['ganados'] += r.points
        elif r.points and r.points < 0:
            s['usados'] += -r.points
        s['disponible'] += r.points or 0
        s['movimientos'] += 1

    payload = {
        'app': 'latribu-puntos',
        'version': 1,
        'generado': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'resumen': [{
            'cedula': ced,
            'nombre': nombres.get(ced, ''),
            'ganados': s['ganados'],
            'usados': s['usados'],
            'disponible': s['disponible'],
            'movimientos': s['movimientos'],
        } for ced, s in sorted(resumen.items(), key=lambda kv: (nombres.get(kv[0], '') or kv[0]))],
        'caminatas': [{
            'id': e.id,
            'nombre': e.nombre_lugar,
            'puntos': e.puntos,
            'tipo_caminata': e.tipo_caminata,
            'fecha_unica': e.fecha_unica,
            'fecha_inicio': e.fecha_inicio,
            'fecha_regreso': e.fecha_regreso,
            'escaneada': e.id in esc_ev,
            'escaneos': esc_ev.get(e.id, {}).get('escaneos', 0),
            'personas': len(esc_ev.get(e.id, {}).get('cedulas', set())),
            'puntos_generados': esc_ev.get(e.id, {}).get('puntos', 0),
            'ultimo_escaneo': _iso(max((r.created_at for r in pts
                                        if r.event_id == e.id and r.tipo == 'participacion'),
                                       default=None)),
        } for e in events.values() if e.puntos],
        'eventos_puntos': [{
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'puntos': p.puntos,
            'activo': p.activo,
            'publico': p.publico,
            'escaneada': p.id in esc_pe,
            'escaneos': esc_pe.get(p.id, {}).get('escaneos', 0),
            'personas': len(esc_pe.get(p.id, {}).get('cedulas', set())),
            'puntos_generados': esc_pe.get(p.id, {}).get('puntos', 0),
        } for p in pevs.values()],
        'caminantes': [{
            'cedula': h.cedula,
            'nombre_completo': h.nombre_completo,
            'telefono': h.telefono,
            'pasaporte': h.pasaporte,
            'tipo_sangre': h.tipo_sangre,
            'fecha_nacimiento': h.fecha_nacimiento.isoformat() if h.fecha_nacimiento else None,
            'alergias': h.alergias,
            'enfermedades_cronicas': h.enfermedades_cronicas,
            'contacto_emergencia_nombre': h.contacto_emergencia_nombre,
            'contacto_emergencia_telefono': h.contacto_emergencia_telefono,
            'pin_secreto': h.pin_secreto,
            'card_email': h.card_email,
            'status': h.status,
            'consultas_puntos_count': h.consultas_puntos_count,
            'created_at': _iso(h.created_at),
        } for h in hikers],
        'movimientos': [{
            'cedula': r.cedula,
            'event_id': r.event_id,
            'evento_nombre': (events[r.event_id].nombre_lugar if r.event_id in events else '')
                             or (pevs[r.puntos_evento_id].nombre if r.puntos_evento_id in pevs else ''),
            'puntos_evento_id': r.puntos_evento_id,
            'donacion_finalidad_id': r.donacion_finalidad_id,
            'points': r.points,
            'tipo': r.tipo,
            'detalle': r.detalle,
            'created_by': r.created_by,
            'created_at': _iso(r.created_at),
        } for r in pts],
        'fidelidad_ajustes': [{
            'cedula': a.cedula, 'nivel': a.nivel, 'nota': a.nota,
            'created_by': a.created_by, 'updated_at': _iso(a.updated_at),
        } for a in FidelidadAjuste.query.all()],
        'fidelidad_log': [{
            'cedula': l.cedula, 'nivel_anterior': l.nivel_anterior, 'nivel_nuevo': l.nivel_nuevo,
            'origen': l.origen, 'nota': l.nota, 'created_by': l.created_by,
            'created_at': _iso(l.created_at),
        } for l in FidelidadLog.query.all()],
    }
    resp = current_app.response_class(
        _json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8')
    resp.headers['Content-Disposition'] = (
        f'attachment; filename=puntos-latribu-{datetime.now():%Y%m%d-%H%M}.json')
    return resp


@bp.route('/api/admin/puntos/import', methods=['POST'])
def admin_puntos_import():
    """Importa un JSON exportado por /api/admin/puntos/export (solo superusuario).
    Inserta solo lo que falte: caminantes nuevos y movimientos no duplicados."""
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    import json as _json
    from models import Hiker, HikerPoints, FidelidadAjuste, FidelidadLog

    data = request.get_json(silent=True)
    if data is None and request.files:
        f = request.files.get('archivo') or next(iter(request.files.values()))
        try:
            data = _json.loads(f.read().decode('utf-8'))
        except Exception:
            data = None
    if not isinstance(data, dict) or 'movimientos' not in data:
        return jsonify({'ok': False, 'error': 'JSON inválido: se esperaba el formato exportado por La Tribu.'}), 400

    def _dt(v):
        if not v:
            return None
        try:
            d = datetime.fromisoformat(str(v).replace('Z', '+00:00'))
            return d.replace(tzinfo=None)
        except Exception:
            return None

    # 1) Caminantes faltantes
    cam_nuevos = 0
    por_cedula = {}
    for c in data.get('caminantes') or []:
        ced = str(c.get('cedula') or '').strip()
        if not ced or not c.get('nombre_completo'):
            continue
        h = Hiker.query.filter_by(cedula=ced).first()
        if h:
            por_cedula[ced] = h.id
            continue
        pin = c.get('pin_secreto')
        if pin and Hiker.query.filter_by(pin_secreto=pin).first():
            pin = None
        h = Hiker(
            cedula=ced, nombre_completo=c['nombre_completo'],
            telefono=c.get('telefono'), pasaporte=c.get('pasaporte'),
            tipo_sangre=c.get('tipo_sangre'),
            alergias=c.get('alergias'),
            enfermedades_cronicas=c.get('enfermedades_cronicas'),
            contacto_emergencia_nombre=c.get('contacto_emergencia_nombre'),
            contacto_emergencia_telefono=c.get('contacto_emergencia_telefono'),
            pin_secreto=pin, card_email=c.get('card_email'),
            status=c.get('status') or 'Activo',
            consultas_puntos_count=c.get('consultas_puntos_count') or 0,
        )
        if c.get('fecha_nacimiento'):
            try:
                h.fecha_nacimiento = datetime.fromisoformat(str(c['fecha_nacimiento'])[:10]).date()
            except Exception:
                pass
        db.session.add(h)
        db.session.flush()
        por_cedula[ced] = h.id
        cam_nuevos += 1
    for h in Hiker.query.all():
        por_cedula.setdefault(h.cedula, h.id)

    # 2) Movimientos faltantes (dedup por contenido completo)
    def _key(ced, tipo, ev, pe, don, pts, ts, det):
        return (ced, tipo or '', ev or 0, pe or 0, don or 0, pts or 0,
                ts.strftime('%Y-%m-%d %H:%M:%S') if ts else '', det or '')

    existentes = {_key(r.cedula, r.tipo, r.event_id, r.puntos_evento_id,
                       r.donacion_finalidad_id, r.points, r.created_at, r.detalle)
                  for r in HikerPoints.query.all()}
    mov_nuevos, mov_omitidos = 0, 0
    for m in data.get('movimientos') or []:
        ced = str(m.get('cedula') or '').strip()
        if not ced:
            mov_omitidos += 1
            continue
        ts = _dt(m.get('created_at')) or datetime.utcnow()
        k = _key(ced, m.get('tipo'), m.get('event_id'), m.get('puntos_evento_id'),
                 m.get('donacion_finalidad_id'), m.get('points'), ts, m.get('detalle'))
        if k in existentes:
            mov_omitidos += 1
            continue
        db.session.add(HikerPoints(
            cedula=ced, hiker_id=por_cedula.get(ced),
            event_id=m.get('event_id'), puntos_evento_id=m.get('puntos_evento_id'),
            donacion_finalidad_id=m.get('donacion_finalidad_id'),
            points=m.get('points') or 0, tipo=m.get('tipo') or 'participacion',
            detalle=m.get('detalle'), created_by=m.get('created_by'),
            created_at=ts))
        existentes.add(k)
        mov_nuevos += 1

    # 3) Ajustes de nivel VIP (upsert por cédula)
    ajustes = 0
    for a in data.get('fidelidad_ajustes') or []:
        ced = str(a.get('cedula') or '').strip()
        if not ced or not a.get('nivel'):
            continue
        row = FidelidadAjuste.query.filter_by(cedula=ced).first()
        if row:
            if row.nivel != a['nivel']:
                row.nivel = a['nivel']
                ajustes += 1
        else:
            db.session.add(FidelidadAjuste(cedula=ced, nivel=a['nivel'],
                                           nota=a.get('nota'), created_by=a.get('created_by')))
            ajustes += 1

    # 4) Bitácora de fidelidad
    log_keys = {(l.cedula, l.nivel_anterior or '', l.nivel_nuevo or '',
                 l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else '')
                for l in FidelidadLog.query.all()}
    logs = 0
    for l in data.get('fidelidad_log') or []:
        ced = str(l.get('cedula') or '').strip()
        ts = _dt(l.get('created_at'))
        k = (ced, l.get('nivel_anterior') or '', l.get('nivel_nuevo') or '',
             ts.strftime('%Y-%m-%d %H:%M:%S') if ts else '')
        if not ced or k in log_keys:
            continue
        db.session.add(FidelidadLog(
            cedula=ced, nivel_anterior=l.get('nivel_anterior'), nivel_nuevo=l.get('nivel_nuevo'),
            origen=l.get('origen') or 'manual', nota=l.get('nota'),
            created_by=l.get('created_by'), created_at=ts or datetime.utcnow()))
        log_keys.add(k)
        logs += 1

    db.session.commit()
    return jsonify({'ok': True,
                    'caminantes_nuevos': cam_nuevos,
                    'movimientos_importados': mov_nuevos,
                    'movimientos_omitidos': mov_omitidos,
                    'ajustes': ajustes,
                    'logs': logs})


@bp.route('/public/usuarios/<token>')
def public_usuarios(token):
    return redirect(url_for('main.home', token=token))
