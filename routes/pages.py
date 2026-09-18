from flask import render_template, session, redirect, url_for, jsonify, request, make_response, current_app, abort
import hashlib
from itsdangerous import URLSafeSerializer, BadSignature
from models import Notification, Event, Hiker, Publicacion, LogoConfig, SiteContent, HomeMedia, CaminataBlock
from modules.points_engine import get_points_engine
from models_core import EventDateChange
from datetime import datetime, date
from sqlalchemy import func, or_
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


@bp.route('/caminatas')
def caminatas():
    from itertools import groupby
    is_super = session.get('role') == 'Superusuario'
    meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    eventos = Event.query.order_by(Event.fecha_unica, Event.fecha_inicio).all()
    if not is_super:
        eventos = [ev for ev in eventos if ev.visitado != 'Cotización']

    def mes_key(ev):
        fecha = ev.fecha_unica or ev.fecha_inicio or ev.fecha_regreso
        if fecha and len(fecha.split('-')) >= 2:
            return fecha[:7]
        return '9999-99'

    por_definir = 'Otras Caminatas'

    def mes_label(key):
        if key == '9999-99':
            return por_definir
        y, m = key.split('-')
        return f"{meses[int(m)-1]} {y}"

    def es_caminata_2027(ev):
        return (
            (ev.fecha_unica or '').startswith('2027') or
            (ev.fecha_inicio or '').startswith('2027') or
            (ev.fecha_regreso or '').startswith('2027')
        )

    eventos_sorted = sorted(eventos, key=lambda ev: (mes_key(ev), ev.fecha_unica or ev.fecha_inicio or '9999-99-99'))
    timeline = []
    for idx, (key, items) in enumerate(groupby(eventos_sorted, key=mes_key)):
        items = list(items)
        entry = {'type': 'provincia', 'order': idx, 'group_label': mes_label(key), 'walks': items, 'walks_2027': []}
        if key == '9999-99':
            walks_2027 = [ev for ev in items if es_caminata_2027(ev)]
            walks_other = [ev for ev in items if not es_caminata_2027(ev)]
            entry['walks'] = walks_other
            entry['walks_2027'] = walks_2027
        timeline.append(entry)

    return render_template('caminatas_2027.html',
        caminatas_2027_text=_get_site_text('caminatas'),
        is_super=is_super,
        eventos=eventos,
        timeline=timeline,
        page_title='Caminatas de la Tribu',
        is_caminatas_2027_page=False,
        empty_message='Aún no hay caminatas registradas.',
        detail_endpoint='main.detalles_evento',
        group_header_text_class='',
        show_expand_hint=True,
        expand_hint_text='Toca para expandir el mes',
        group_badge_class='bg-white text-dark border ms-3 shadow-sm',
        group_badge_style='',
        group_badge_icon='bi-person-walking',
        group_badge_icon_color='#0dcaf0')


from routes.about import DEFAULT_SITE_CONTENT


def _get_site_text(key):
    row = SiteContent.query.filter_by(key=key).first()
    return row.value if row else DEFAULT_SITE_CONTENT.get(key, '')


@bp.route('/caminatas/pendientes')
def caminatas_pendientes():
    is_super = session.get('role') == 'Superusuario'
    eventos = Event.query.filter(
        or_(
            Event.visitado == 'Pendiente',
            Event.visitado == 'No',
            Event.visitado == '',
            Event.visitado.is_(None)
        )
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas Pendientes')


@bp.route('/caminatas/anio')
def caminatas_anio():
    is_super = session.get('role') == 'Superusuario'
    eventos = [e for e in Event.query.order_by(Event.nombre_lugar).all()
               if e.visitado and e.visitado.isdigit() and len(e.visitado) == 4]
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas por Año')


@bp.route('/caminatas/visitados')
def caminatas_visitados():
    is_super = session.get('role') == 'Superusuario'
    eventos = Event.query.filter(
        or_(
            Event.visitado == 'Visitados',
            Event.visitado == 'Visitado',
            Event.visitado == 'Sí'
        )
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas Visitadas')


@bp.route('/caminatas/programados')
def caminatas_programados():
    is_super = session.get('role') == 'Superusuario'
    eventos = Event.query.filter(
        or_(Event.visitado == 'Programados', Event.visitado == 'Por programar')
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas Programadas')


@bp.route('/caminatas/cotizaciones')
def caminatas_cotizaciones():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    eventos = Event.query.filter(
        Event.visitado == 'Cotización'
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=True,
        eventos=eventos,
        page_title='Cotizaciones')


@bp.route('/cotizaciones/buseta')
def cotizaciones_buseta():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    from itertools import groupby
    eventos = Event.query.filter_by(visitado='Cotización').order_by(Event.provincia, Event.nombre_lugar).all()
    grupos = []
    for prov, items in groupby(eventos, key=lambda e: e.provincia or 'Sin provincia'):
        grupos.append({'provincia': prov, 'eventos': list(items)})
    return render_template('cotizaciones_buseta.html',
        is_super=True,
        grupos=grupos,
        page_title='Cotizaciones de buseta')


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


@bp.route('/caminatas-2027')
def caminatas_2027():
    from itertools import groupby
    is_share = request.args.get('share') == '1'
    is_super = session.get('role') == 'Superusuario' and not is_share
    eventos = Event.query.filter(
        or_(
            Event.fecha_unica.like('2027%'),
            Event.fecha_inicio.like('2027%'),
            Event.fecha_regreso.like('2027%')
        )
    ).order_by(Event.fecha_unica, Event.fecha_inicio).all()

    if not is_super:
        eventos = [ev for ev in eventos if ev.provincia != 'Referencia' and ev.visitado != 'Cotización']

    eventos_sorted = sorted(eventos, key=lambda e: (e.provincia or 'Sin provincia'))
    timeline = []
    for idx, (provincia, items) in enumerate(groupby(eventos_sorted, key=lambda e: (e.provincia or 'Sin provincia'))):
        timeline.append({'type': 'provincia', 'order': idx * 100.0, 'group_label': provincia or 'Sin provincia', 'walks': list(items)})

    blocks = CaminataBlock.query.filter_by(page='caminatas_2027').order_by(CaminataBlock.order).all()
    for b in blocks:
        timeline.append({'type': 'block', 'order': b.order, 'id': b.id, 'content': b.content})

    timeline.sort(key=lambda x: x['order'])

    share_url = url_for('main.caminatas_2027', share=1, _external=True)
    share_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')

    return render_template('caminatas_2027.html',
        caminatas_2027_text=_get_site_text('caminatas_2027'),
        is_super=is_super,
        is_share=is_share,
        share_url=share_url,
        share_datetime=share_datetime,
        eventos=eventos,
        timeline=timeline,
        detail_endpoint='main.ver_caminata_2027',
        group_badge_icon='bi-person-walking',
        group_badge_icon_color='#ffffff')


@bp.route('/caminatas-2027/<int:event_id>')
def ver_caminata_2027(event_id):
    is_share = request.args.get('share') == '1'
    is_super = session.get('role') == 'Superusuario' and not is_share
    event = Event.query.get_or_404(event_id)
    if event.visitado == 'Cotización' and not is_super:
        return redirect(url_for('main.home'))
    share_url = url_for('main.ver_caminata_2027', event_id=event_id, share=1, _external=True)
    share_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')
    itinerario_hash = hashlib.md5((event.itinerario or '').encode('utf-8')).hexdigest()
    return render_template('ver_caminata_2027.html',
        event=event,
        is_super=is_super,
        is_share=is_share,
        share_url=share_url,
        share_datetime=share_datetime,
        itinerario_hash=itinerario_hash)


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
    from modules.points_helpers import get_puntos_password, get_puntos_admin_visible, get_notif_cutoff
    notif_cutoff = get_notif_cutoff(puntos_cedula)
    puntos_notificaciones = [r for r in puntos_history if r['tipo'] in ('obsequio', 'donacion_recibida') and (r.get('creado_at') or '') > notif_cutoff]
    return render_template('perfil.html', user=user, hiker=hiker, puntos_cedula=puntos_cedula,
                           puntos_total=puntos_total, puntos_history=puntos_history, puntos_notificaciones=puntos_notificaciones,
                           puntos_password=get_puntos_password(), puntos_pwd_msg=session.pop('puntos_pwd_msg', None),
                           puntos_pwd_visible=get_puntos_admin_visible())


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


@bp.route('/public/usuarios/<token>')
def public_usuarios(token):
    return redirect(url_for('main.home', token=token))
