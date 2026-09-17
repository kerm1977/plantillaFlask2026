# routes/points.py - Endpoints del motor de puntuación
import re
import json
from datetime import datetime
from urllib.parse import quote
from flask import request, jsonify, session, render_template, Response, redirect, url_for
from db import db
from models import Hiker, Event, HikerPoints, User, EventRegistration
from modules.points_engine import get_points_engine
from modules.points_bonuses import get_points_bonuses
from modules.points_admin import get_points_admin
from modules.points_donations import birthday_hikers, donate
from modules.points_helpers import is_past_event, get_puntos_password, set_puntos_password, get_notif_cutoff, set_notif_cleared, get_puntos_admin_visible, set_puntos_admin_visible
from routes import bp


def _current_user():
    return session.get('name') or session.get('email') or 'sistema'


@bp.route('/admin/puntos/password', methods=['POST'])
def puntos_password():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    pwd = (request.form.get('password') or '').strip()
    if not (pwd.isdigit() and len(pwd) == 4):
        session['puntos_pwd_msg'] = 'La contraseña debe tener exactamente 4 dígitos.'
    else:
        set_puntos_password(pwd)
        session['puntos_pwd_msg'] = 'Contraseña de ingreso a puntos actualizada correctamente.'
    return redirect(url_for('main.profile'))


@bp.route('/admin/puntos/password-visibilidad', methods=['POST'])
def puntos_password_visibilidad():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    set_puntos_admin_visible(bool(request.form.get('visible')))
    return redirect(url_for('main.profile'))


@bp.route('/puntos/limpiar-notificaciones', methods=['POST'])
def puntos_limpiar_notificaciones():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('main.home'))
    full_name = f'{user.name} {user.last_name_1} {user.last_name_2}'.strip()
    hiker = Hiker.query.filter_by(telefono=user.phone).first() if user.phone else None
    if not hiker:
        hiker = Hiker.query.filter_by(nombre_completo=full_name).first()
    if hiker:
        set_notif_cleared(hiker.cedula)
    return redirect(url_for('main.profile'))


@bp.route('/admin/puntos/exportar-json', methods=['GET'])
def admin_puntos_exportar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    engine = get_points_engine()
    hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
    data = {
        'generado': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'usuarios': []
    }
    for hiker in hikers:
        data['usuarios'].append({
            'cedula': hiker.cedula,
            'nombre_completo': hiker.nombre_completo,
            'total': engine.total_by_cedula(hiker.cedula),
            'historial': engine.history_with_names(hiker.cedula)
        })
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(text, mimetype='application/json', headers={'Content-Disposition': 'attachment; filename=puntos_todos_usuarios.json'})


@bp.route('/admin/puntos/importar-json', methods=['POST'])
def admin_puntos_importar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    if 'archivo' not in request.files:
        session['puntos_pwd_msg'] = 'Falta el archivo JSON.'
        return redirect(url_for('main.profile'))
    archivo = request.files['archivo']
    if archivo.filename == '':
        session['puntos_pwd_msg'] = 'Archivo vacío.'
        return redirect(url_for('main.profile'))
    try:
        contenido = json.loads(archivo.read().decode('utf-8'))
        registros = []
        if isinstance(contenido, dict) and isinstance(contenido.get('usuarios'), list):
            for u in contenido['usuarios']:
                ced = (u.get('cedula') or '').strip()
                for r in (u.get('historial') or []):
                    r = dict(r)
                    r['cedula'] = ced
                    registros.append(r)
        elif isinstance(contenido, dict) and isinstance(contenido.get('historial'), list):
            ced = (contenido.get('cedula') or '').strip()
            for r in contenido['historial']:
                r = dict(r)
                r.setdefault('cedula', ced)
                registros.append(r)
        elif isinstance(contenido, list):
            registros = contenido
        else:
            session['puntos_pwd_msg'] = 'El JSON no contiene registros de puntos.'
            return redirect(url_for('main.profile'))
        agregados = 0
        for r in registros:
            ced = (r.get('cedula') or '').strip()
            if not ced:
                continue
            hiker = Hiker.query.filter_by(cedula=ced).first()
            hp = HikerPoints(
                cedula=ced,
                hiker_id=hiker.id if hiker else None,
                event_id=r.get('event_id'),
                points=int(r.get('puntos', 0) or 0),
                tipo=(r.get('tipo') or 'participacion')[:20],
                detalle=(r.get('detalle') or '')[:255],
                created_by=(r.get('creado_por') or _current_user())[:100],
                created_at=datetime.fromisoformat(r['creado_at']) if r.get('creado_at') else datetime.utcnow()
            )
            db.session.add(hp)
            agregados += 1
        db.session.commit()
        session['puntos_pwd_msg'] = f'Importación completada: {agregados} movimientos de puntos agregados.'
        return redirect(url_for('main.profile'))
    except Exception as e:
        session['puntos_pwd_msg'] = f'Error al importar: {e}'
        return redirect(url_for('main.profile'))


@bp.route('/api/puntos/asignar/<int:event_id>', methods=['POST'])
def puntos_asignar(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    result = get_points_engine().assign_to_event(event_id, _current_user())
    return jsonify(result), (200 if result.get('ok') else 400)


@bp.route('/api/puntos/retirar/<int:event_id>', methods=['POST'])
def puntos_retirar(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.json or request.form or {}
    cedula = (data.get('cedula') or '').strip()
    justificado = (data.get('justificado') or data.get('lesion') or '').lower() in ('true', '1', 'si', 'yes', 'on')
    mensaje = (data.get('mensaje') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cédula'}), 400
    result = get_points_engine().withdraw(event_id, cedula, _current_user(), justificado=justificado, mensaje=mensaje)
    return jsonify(result), (200 if result.get('ok') else 400)


@bp.route('/api/puntos/historial/<cedula>', methods=['GET'])
def puntos_historial(cedula):
    engine = get_points_engine()
    cedula = cedula.strip()
    total = engine.total_by_cedula(cedula)
    history = engine.history_with_names(cedula)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    return jsonify({
        'ok': True,
        'cedula': cedula,
        'nombre_completo': hiker.nombre_completo if hiker else '',
        'total': total,
        'history': history
    })


@bp.route('/api/puntos/evento/<int:event_id>', methods=['GET'])
def puntos_evento(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    rows = get_points_engine().event_assignments(event_id)
    event = Event.query.get_or_404(event_id)
    return jsonify({'ok': True, 'puntos_por_persona': event.puntos or 0, 'asignados': rows})


@bp.route('/mis-puntos', methods=['GET', 'POST'])
def mis_puntos():
    cedula = ''
    result = None
    is_super = session.get('role') == 'Superusuario'
    admin_message = session.pop('admin_message', None)
    admin_error = session.pop('admin_error', None)
    donacion_message = session.pop('donacion_message', None)
    donacion_error = session.pop('donacion_error', None)
    engine = get_points_engine()
    bonuses = get_points_bonuses()
    admin = get_points_admin()
    cumpleaneros = birthday_hikers()
    todos_hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
    eventos_redimir = [e for e in Event.query.order_by(Event.id.desc()).all() if not is_past_event(e) and (e.visitado in ('Programados', 'Por programar'))]
    if request.method == 'POST':
        cedula = (request.form.get('cedula') or '').strip()
        accion = (request.form.get('accion') or '').strip()
        redirect_url = url_for('main.mis_puntos', cedula=cedula)
        if cedula and accion in ('donar', 'transferir', 'redimir', 'limpiar_notificaciones') and not is_super and session.get('mis_puntos_ok') != cedula:
            session['admin_error'] = 'Verificá tu cédula y contraseña primero.'
            return redirect(redirect_url)
        if cedula and accion == 'donar':
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            res = donate(cedula, cedula_destino, monto, cedula)
            if res.get('ok'):
                session['donacion_message'] = f'Donaste {monto} puntos. Tu nuevo total: {res.get("donor_total")}'
            else:
                session['donacion_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'transferir':
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            detalle = (request.form.get('detalle') or '').strip()
            res = donate(cedula, cedula_destino, monto, _current_user(), detalle)
            if res.get('ok'):
                recipient = Hiker.query.filter_by(cedula=cedula_destino).first()
                session['admin_message'] = f'Obsequiaste {monto} puntos a {recipient.nombre_completo if recipient else cedula_destino}. Tu total: {res.get("donor_total")}'
            else:
                session['admin_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'redimir':
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            concepto = (request.form.get('concepto') or '').strip()
            detalle_extra = (request.form.get('detalle') or '').strip()
            event_id = None
            if concepto.startswith('caminata_'):
                try:
                    event_id = int(concepto.split('_', 1)[1])
                except ValueError:
                    event_id = None
            if event_id:
                event = Event.query.get(event_id)
                if not event:
                    session['admin_error'] = 'La caminata seleccionada no existe.'
                else:
                    detalle = f'{event.nombre_lugar}'
                    if detalle_extra:
                        detalle += f' - {detalle_extra}'
                    res = engine.redeem(cedula, monto, 'caminata', _current_user(), detalle, event_id)
                    if res.get('ok'):
                        session['admin_message'] = f'Redimiste {monto} puntos. Valor aplicado: {res.get("valor")}.'
                    else:
                        session['admin_error'] = res.get('error')
            elif concepto == 'otro':
                res = engine.redeem(cedula, monto, 'dinero', _current_user(), detalle_extra)
                if res.get('ok'):
                    session['admin_message'] = f'Redimiste {monto} puntos. Valor aplicado: {res.get("valor")} (80%).'
                else:
                    session['admin_error'] = res.get('error')
            else:
                session['admin_error'] = 'Seleccioná una caminata u "Otros".'
            return redirect(redirect_url)
        elif is_super and cedula and accion == 'regalar':
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            detalle = (request.form.get('detalle') or '').strip()
            res = admin.gift(cedula_destino, monto, _current_user(), detalle)
            if res.get('ok'):
                cedula = cedula_destino
                session['admin_message'] = f'Regalaste {monto} puntos. Total destinatario: {res.get("total")}'
            else:
                session['admin_error'] = res.get('error')
            return redirect(url_for('main.mis_puntos', cedula=cedula))
        elif is_super and cedula and accion == 'restar':
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            detalle = (request.form.get('detalle') or '').strip()
            res = admin.subtract(cedula_destino, monto, _current_user(), detalle)
            if res.get('ok'):
                cedula = cedula_destino
                session['admin_message'] = f'Restaste {monto} puntos. Total destinatario: {res.get("total")}'
            else:
                session['admin_error'] = res.get('error')
            return redirect(url_for('main.mis_puntos', cedula=cedula))
        elif is_super and cedula and accion == 'retirar':
            try:
                evento_id_retiro = int(request.form.get('evento_id') or 0)
            except ValueError:
                evento_id_retiro = 0
            justificado = (request.form.get('justifico') or '') == 'si'
            mensaje = (request.form.get('mensaje') or '').strip()
            if not evento_id_retiro:
                session['admin_error'] = 'No se indicó la caminata.'
            else:
                res = engine.withdraw(evento_id_retiro, cedula, _current_user(), justificado=justificado, mensaje=mensaje)
                if res.get('ok'):
                    msg = f'Retiro registrado. Puntos retirados: {res.get("points_deducted")}.'
                    if res.get('reembolso'):
                        msg += f' Reintegrados {res["reembolso"]} puntos por la redención (descuento 12%: {res["descuento"]}).'
                    session['admin_message'] = msg
                else:
                    session['admin_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'limpiar_notificaciones':
            set_notif_cleared(cedula)
            session['admin_message'] = 'Notificaciones limpiadas.'
            return redirect(redirect_url)
        # Cualquier otro POST (incluyendo búsqueda antigua) redirige para evitar reenvío
        return redirect(redirect_url)
    else:
        cedula = (request.args.get('cedula') or '').strip()
        clave = (request.args.get('clave') or '').strip()
    whatsapp_url = ''
    registro_whatsapp_url = ''
    estado_whatsapp_url = ''
    telefono_registrado = ''
    registros = []
    no_registrado = False
    pendiente_password = False
    nombre_bienvenida = ''
    if cedula:
        hiker_found = Hiker.query.filter_by(cedula=cedula).first()
        if not hiker_found:
            no_registrado = True
            texto_reg = ('Saludos, estoy interesado en el sistema de puntos de la Tribu de los Libres '
                         'para poder participar con ustedes. Me gustaria que me registren en el sistema '
                         'de puntos y para ello, en el siguiente mensaje, voy a proporcionar mi nombre y '
                         'mi numero de cedula. Muchas gracias.')
            registro_whatsapp_url = 'https://wa.me/50686529837?text=' + quote(texto_reg)
        else:
            nombre_bienvenida = hiker_found.nombre_completo or ''
            pwd_global = get_puntos_password()
            verificado = session.get('mis_puntos_ok') == cedula
            if not verificado:
                if not pwd_global:
                    admin_error = 'El sistema de puntos aún no tiene contraseña configurada. Contactá a los coordinadores.'
                elif clave == pwd_global:
                    session['mis_puntos_ok'] = cedula
                    verificado = True
                else:
                    pendiente_password = True
                    if clave:
                        admin_error = 'La contraseña no es correcta.'
            if verificado:
                bonuses.apply(cedula)
                history = engine.history_with_names(cedula)
                cutoff = get_notif_cutoff(cedula)
                notificaciones = [r for r in history if r['tipo'] in ('obsequio', 'donacion_recibida') and (r.get('creado_at') or '') > cutoff]
                result = {
                    'cedula': cedula,
                    'nombre_completo': getattr(hiker_found, 'nombre_completo', ''),
                    'total': engine.total_by_cedula(cedula),
                    'history': history,
                    'notificaciones': notificaciones
                }
                if is_super:
                    for r in EventRegistration.query.filter_by(hiker_id=hiker_found.id).all():
                        ev = Event.query.get(r.event_id)
                        if ev:
                            registros.append({'registro': r, 'evento': ev})
                wa_lines = [f'Cedula: {cedula}', f'Nombre: {result["nombre_completo"]}', f'Total: {result["total"]} puntos', 'Historial:', '']
                for row in history[:10]:
                    wa_lines.append(f'{(row.get("creado_at") or "")[:10]} | {row.get("tipo")} | {row.get("puntos")} | {row.get("detalle") or ""}')
                whatsapp_url = 'https://wa.me/?text=' + quote("\n".join(wa_lines), safe='')
                telefono_registrado = re.sub(r'\D', '', hiker_found.telefono or '')
                estado_txt = _build_estado_cuenta_whatsapp(cedula, hiker_found)
                estado_whatsapp_url = ('https://wa.me/' + telefono_registrado if telefono_registrado else 'https://wa.me/') + '?text=' + quote(estado_txt)
    return render_template('mis_puntos.html', cedula=cedula, result=result, is_super=is_super, admin_message=admin_message, admin_error=admin_error, donacion_message=donacion_message, donacion_error=donacion_error, cumpleaneros=cumpleaneros, todos_hikers=todos_hikers, eventos_redimir=eventos_redimir, whatsapp_url=whatsapp_url, registros=registros, no_registrado=no_registrado, registro_whatsapp_url=registro_whatsapp_url, pendiente_password=pendiente_password, nombre_bienvenida=nombre_bienvenida, estado_whatsapp_url=estado_whatsapp_url, telefono_registrado=telefono_registrado)


@bp.route('/caminata/<int:event_id>/puntos', methods=['GET', 'POST'])
def evento_puntos(event_id):
    event = Event.query.get_or_404(event_id)
    engine = get_points_engine()
    bonuses = get_points_bonuses()
    admin = get_points_admin()
    cedula = ''
    total = 0
    registrado = False
    history = []
    ticket = session.pop('evento_ticket', None)
    regalo = session.pop('evento_regalo', None)
    cumpleaneros = birthday_hikers()
    participantes = Hiker.query.order_by(Hiker.nombre_completo).all()
    is_super = session.get('role') == 'Superusuario'
    message = session.pop('evento_message', None)
    error = session.pop('evento_error', None)
    if request.method == 'POST':
        cedula = (request.form.get('cedula') or '').strip()
        accion = (request.form.get('accion') or '').strip()
        redirect_url = url_for('main.evento_puntos', event_id=event_id, cedula=cedula)
        if cedula and accion == 'buscar':
            return redirect(redirect_url)
        if cedula and not is_super and session.get(f'puntos_ok_{event_id}') != cedula:
            session['evento_error'] = 'Verificá tu cédula y contraseña primero.'
            return redirect(redirect_url)
        if cedula and accion == 'registrar':
            res = engine.earn_from_link(event_id, cedula)
            if res.get('ok'):
                session['evento_message'] = f'Ganaste {res["puntos_ganados"]} puntos. Total acumulado: {res["total"]}. '
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'retirar':
            mensaje = (request.form.get('mensaje') or '').strip()
            justificado = (request.form.get('justifico') or '') == 'si'
            res = engine.withdraw(event_id, cedula, 'link', justificado=justificado, mensaje=mensaje)
            if res.get('ok'):
                session['evento_ticket'] = {
                    'cedula': cedula,
                    'justificado': res.get('justificado'),
                    'mensaje': res.get('mensaje'),
                    'points_deducted': res.get('points_deducted'),
                    'reembolso': res.get('reembolso'),
                    'descuento': res.get('descuento')
                }
                msg = 'Retiro registrado correctamente.'
                if res.get('reembolso'):
                    msg += f' Reintegrados {res["reembolso"]} puntos (descuento 12%: {res["descuento"]}).'
                session['evento_message'] = msg
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'comprar':
            try:
                puntos = int(request.form.get('cantidad') or 0)
            except ValueError:
                puntos = 0
            res = engine.buy_points(cedula, event_id, puntos, 'link')
            if res.get('ok'):
                session['evento_message'] = f'Compra registrada. Pagá {res["costo"]["total"]} colones (Jenny Ceciliano Córdova).'
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'redimir':
            try:
                monto = int(request.form.get('cantidad') or 0)
            except ValueError:
                monto = 0
            tipo = (request.form.get('tipo') or 'caminata').strip()
            if tipo not in ('caminata', 'dinero'):
                tipo = 'caminata'
            res = engine.redeem(cedula, monto, tipo, 'link')
            if res.get('ok'):
                session['evento_message'] = f'Redimiste {monto} puntos. Valor aplicado: {res["valor"]}. '
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'donar':
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            res = donate(cedula, cedula_destino, monto, cedula)
            if res.get('ok'):
                recipient = Hiker.query.filter_by(cedula=cedula_destino).first()
                nombre = recipient.nombre_completo if recipient else cedula_destino
                telefono = re.sub(r'\D', '', recipient.telefono) if recipient and recipient.telefono else ''
                texto = f'Hola {nombre}, te he obsequiado {monto} puntos a tu cuenta. Feliz cumpleaños y esperamos que cumplas muchos años más.'
                if telefono:
                    whatsapp_url = f'https://wa.me/{telefono}?text={quote(texto)}'
                else:
                    whatsapp_url = f'https://wa.me/?text={quote(texto)}'
                session['evento_regalo'] = {
                    'nombre': nombre,
                    'monto': monto,
                    'recipient_total': res.get('recipient_total'),
                    'whatsapp_url': whatsapp_url,
                    'mostrar_whatsapp': True
                }
                session['evento_message'] = f'Donaste {monto} puntos a {nombre}. '
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'transferir':
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            res = donate(cedula, cedula_destino, monto, cedula)
            if res.get('ok'):
                recipient = Hiker.query.filter_by(cedula=cedula_destino).first()
                nombre = recipient.nombre_completo if recipient else cedula_destino
                session['evento_regalo'] = {
                    'nombre': nombre,
                    'monto': monto,
                    'recipient_total': res.get('recipient_total'),
                    'whatsapp_url': '',
                    'mostrar_whatsapp': False
                }
                session['evento_message'] = f'Transferiste {monto} puntos a {nombre}. Tu total: {res.get("donor_total")}. '
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        elif cedula and accion == 'regalar':
            cedula_destino = (request.form.get('cedula_destino') or '').strip()
            try:
                monto = int(request.form.get('monto') or 0)
            except ValueError:
                monto = 0
            motivo = (request.form.get('motivo') or '').strip()
            res = admin.gift(cedula_destino, monto, _current_user(), motivo)
            if res.get('ok'):
                session['evento_message'] = f'Regalaste {monto} puntos a {cedula_destino}. Total receptor: {res.get("total")}. '
            else:
                session['evento_error'] = res.get('error')
            return redirect(redirect_url)
        # Si no hubo acción conocida, redirigir de todos modos para evitar reenvío
        return redirect(redirect_url)
    else:
        cedula = (request.args.get('cedula') or '').strip()
        pin = (request.args.get('pin') or '').strip()
    verificado = False
    no_registrado = False
    if cedula:
        hiker_check = Hiker.query.filter_by(cedula=cedula).first()
        pwd_global = get_puntos_password()
        if not hiker_check:
            no_registrado = True
        elif session.get(f'puntos_ok_{event_id}') != cedula and (not pwd_global or pin != pwd_global):
            error = 'La contraseña no es correcta. Pedila a los coordinadores.'
        else:
            session[f'puntos_ok_{event_id}'] = cedula
            verificado = True
            bonuses.apply(cedula)
            total = engine.total_by_cedula(cedula)
            registrado = engine.has_earned(event_id, cedula)
            history = engine.history_with_names(cedula)
    return render_template('evento_puntos.html', event=event, cedula=cedula, total=total, registrado=registrado, history=history, ticket=ticket, regalo=regalo, is_super=is_super, message=message, error=error, cumpleaneros=cumpleaneros, participantes=participantes, verificado=verificado, no_registrado=no_registrado)


def _build_estado_cuenta_whatsapp(cedula, hiker=None):
    engine = get_points_engine()
    sep = '-' * 40
    lines = []
    lines.append('*ESTADO DE CUENTA DE PUNTOS - LA TRIBU DE LOS LIBRES*')
    lines.append(sep)
    lines.append(f'Cédula: {cedula}')
    lines.append(f'Nombre: {hiker.nombre_completo if hiker else ""}')
    if hiker and hiker.telefono:
        lines.append(f'Teléfono: {hiker.telefono}')
    lines.append(f'Total puntos: {engine.total_by_cedula(cedula)}')
    lines.append(f'Generado: {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC')
    lines.append(sep)
    lines.append('*MOVIMIENTOS*')
    lines.append('')
    for row in engine.history_with_names(cedula):
        fecha = (row.get('creado_at') or '')[:19].replace('T', ' ')
        lines.append(f'Fecha y hora: {fecha}')
        lines.append(f'Tipo: {row.get("tipo")}')
        lines.append(f'Puntos: {row.get("puntos", 0)}')
        if row.get('evento_nombre'):
            lines.append(f'Caminata: {row["evento_nombre"]}')
        if row.get('detalle'):
            lines.append(f'Detalle: {row["detalle"]}')
        lines.append(sep)
        lines.append('')
    return '\n'.join(lines)


def _format_row_line(row):
    fecha = (row.get('creado_at') or '')[:19].replace('T', ' ')
    tipo = (row.get('tipo') or '')[:17]
    detalle = (row.get('detalle') or '')[:40]
    return f'{fecha:<20} {tipo:<17} {detalle:<40} {row.get("puntos", 0):>8}'


def _build_estado_cuenta(cedula, hiker=None):
    engine = get_points_engine()
    lines = []
    lines.append('=' * 90)
    lines.append('ESTADO DE CUENTA - La Tribu de los Libres')
    lines.append('=' * 90)
    lines.append(f'Cedula: {cedula}')
    lines.append(f'Nombre: {hiker.nombre_completo if hiker else ""}')
    if hiker:
        fn = hiker.fecha_nacimiento
        lines.append(f'Telefono: {hiker.telefono or "No registrado"}')
        lines.append(f'Pasaporte: {hiker.pasaporte or "No registrado"}')
        lines.append(f'Tipo de sangre: {hiker.tipo_sangre or "No registrado"}')
        lines.append(f'Fecha de nacimiento: {fn.strftime("%d/%m/%Y") if fn else "No registrada"}')
        lines.append(f'Alergias: {hiker.alergias or "Ninguna"}')
        lines.append(f'Enfermedades cronicas: {hiker.enfermedades_cronicas or "Ninguna"}')
        lines.append(f'Contacto emergencia: {hiker.contacto_emergencia_nombre or ""} {hiker.contacto_emergencia_telefono or ""}'.strip())
    lines.append(f'Total puntos: {engine.total_by_cedula(cedula)}')
    lines.append('Generado: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    lines.append('')
    lines.append(f'{"Fecha":<20} {"Tipo":<17} {"Detalle":<40} {"Puntos":>8}')
    lines.append('-' * 90)
    for row in engine.history_with_names(cedula):
        lines.append(_format_row_line(row))
    lines.append('')
    return '\n'.join(lines)


@bp.route('/mis-puntos/estado-cuenta', methods=['GET'])
def estado_cuenta():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    text = _build_estado_cuenta(cedula, hiker)
    filename = f'estado_cuenta_{cedula}.txt'
    return Response(text, mimetype='text/plain', headers={'Content-Disposition': f'attachment; filename={filename}'})


@bp.route('/admin/puntos/exportar', methods=['GET'])
def admin_puntos_exportar():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
    parts = []
    parts.append('=' * 90)
    parts.append('RESUMEN DE ESTADOS DE CUENTA - La Tribu de los Libres')
    parts.append('Generado: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    parts.append('=' * 90)
    parts.append('')
    for hiker in hikers:
        parts.append(_build_estado_cuenta(hiker.cedula, hiker))
    text = '\n'.join(parts)
    return Response(text, mimetype='text/plain', headers={'Content-Disposition': 'attachment; filename=estados_cuenta_todos.txt'})


@bp.route('/mis-puntos/eliminar/<int:row_id>', methods=['POST'])
def mis_puntos_eliminar(row_id):
    if 'user_id' not in session and session.get('role') != 'Superusuario':
        return redirect(url_for('main.mis_puntos'))
    record = HikerPoints.query.get_or_404(row_id)
    cedula = record.cedula
    is_super = session.get('role') == 'Superusuario'
    puede_eliminar = is_super
    if not is_super and 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            full_name = f'{user.name} {user.last_name_1} {user.last_name_2}'.strip()
            hiker = Hiker.query.filter_by(telefono=user.phone).first() if user.phone else None
            if not hiker:
                hiker = Hiker.query.filter_by(nombre_completo=full_name).first()
            if hiker and hiker.cedula == cedula:
                puede_eliminar = True
    if not puede_eliminar:
        return redirect(url_for('main.mis_puntos', cedula=cedula))
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('main.mis_puntos', cedula=cedula))


@bp.route('/mis-puntos/exportar-json', methods=['GET'])
def mis_puntos_exportar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    engine = get_points_engine()
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    data = {
        'cedula': cedula,
        'nombre_completo': hiker.nombre_completo if hiker else '',
        'total': engine.total_by_cedula(cedula),
        'historial': engine.history_with_names(cedula)
    }
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(text, mimetype='application/json', headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.json'})


@bp.route('/mis-puntos/importar-json', methods=['POST'])
def mis_puntos_importar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    cedula = (request.form.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    if 'archivo' not in request.files:
        return jsonify({'ok': False, 'error': 'Falta el archivo'}), 400
    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({'ok': False, 'error': 'Archivo vacío'}), 400
    try:
        contenido = json.loads(archivo.read().decode('utf-8'))
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        hiker_id = hiker.id if hiker else None
        registros = contenido.get('historial', contenido) if isinstance(contenido, dict) else contenido
        if not isinstance(registros, list):
            return jsonify({'ok': False, 'error': 'El JSON no contiene una lista de registros'}), 400
        agregados = 0
        for r in registros:
            if (r.get('cedula') or '').strip() != cedula:
                continue
            puntos = int(r.get('puntos', 0) or 0)
            hp = HikerPoints(
                cedula=cedula,
                hiker_id=hiker_id,
                event_id=r.get('event_id'),
                points=puntos,
                tipo=(r.get('tipo') or 'participacion')[:20],
                detalle=(r.get('detalle') or '')[:255],
                created_by=(r.get('creado_por') or _current_user())[:100],
                created_at=datetime.fromisoformat(r['creado_at']) if r.get('creado_at') else datetime.utcnow()
            )
            db.session.add(hp)
            agregados += 1
        db.session.commit()
        return redirect(url_for('main.mis_puntos', cedula=cedula))
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400
