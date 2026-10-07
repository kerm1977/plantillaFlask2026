# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_mis.py - Página "Mis Puntos" (consulta, donar, redimir)
import re
from urllib.parse import quote
from flask import request, session, render_template, redirect, url_for
from db import db
from models import Hiker, Event, User, EventRegistration
from modules.points_engine import get_points_engine
from modules.points_bonuses import get_points_bonuses
from modules.points_admin import get_points_admin
from modules.points_donations import birthday_hikers, donate
from modules import fidelidad
from modules.points_helpers import (is_past_event, get_puntos_password, set_notif_cleared,
                                    get_notif_cutoff, build_estado_cuenta_whatsapp)
from routes import bp
from routes.points import _current_user


@bp.route('/api/mis-puntos/salida', methods=['POST'])
def mis_puntos_salida():
    # BLINDADO: beacon de salida de "Mis puntos" — libera el marcador para que
    # la próxima entrada cuente como nueva consulta (no toca la sesión de acceso).
    session.pop('mis_puntos_counted', None)
    return ('', 204)


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
    estado_coordinador_url = ''
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
            bloqueado = (hiker_found.status or 'Activo') == 'Bloqueado'
            pwd_global = get_puntos_password()
            # La gestión solo depende del rol de superusuario. Quien no es
            # superusuario entra con cédula + PIN y ve solo su estado de cuenta.
            if pwd_global and clave == pwd_global:
                session['mis_puntos_ok'] = cedula
            verificado = (is_super or session.get('mis_puntos_ok') == cedula) and not bloqueado
            if bloqueado:
                admin_error = 'Tu acceso está bloqueado. Contactá a los coordinadores de La Tribu.'
            elif not verificado:
                if not pwd_global:
                    admin_error = 'El sistema de puntos aún no tiene contraseña configurada. Contactá a los coordinadores.'
                else:
                    pendiente_password = True
                    if clave:
                        admin_error = 'La contraseña no es correcta.'
            if verificado:
                bonuses.apply(cedula)
                # BLINDADO: contador disimulado de consultas de puntos (solo superusuario lo ve).
                # Cuenta una vez por visita: el marcador se limpia al salir de la página (beacon),
                # así recargar NO cuenta, pero salir y volver a entrar SÍ.
                if not is_super and session.get('mis_puntos_counted') != cedula:
                    hiker_found.consultas_puntos_count = (hiker_found.consultas_puntos_count or 0) + 1
                    session['mis_puntos_counted'] = cedula
                    db.session.commit()
                    # BLINDADO: el commit expira los objetos cargados; se re-consultan
                    # para que el template no reciba instancias expiradas.
                    hiker_found = Hiker.query.get(hiker_found.id)
                    todos_hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
                    cumpleaneros = birthday_hikers()
                    eventos_redimir = [e for e in Event.query.order_by(Event.id.desc()).all() if not is_past_event(e) and (e.visitado in ('Programados', 'Por programar'))]
                history = engine.history_with_names(cedula)
                cutoff = get_notif_cutoff(cedula)
                notificaciones = [r for r in history if r['tipo'] in ('obsequio', 'donacion_recibida') and (r.get('creado_at') or '') > cutoff]
                result = {
                    'cedula': cedula,
                    'nombre_completo': getattr(hiker_found, 'nombre_completo', ''),
                    'total': engine.total_by_cedula(cedula),
                    'history': history,
                    'notificaciones': notificaciones,
                    'consultas_puntos_count': hiker_found.consultas_puntos_count or 0,
                    'fidelidad': fidelidad.info(cedula)
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
                estado_txt = build_estado_cuenta_whatsapp(cedula, hiker_found)
                estado_whatsapp_url = ('https://wa.me/' + telefono_registrado if telefono_registrado else 'https://wa.me/') + '?text=' + quote(estado_txt)
                estado_coordinador_url = 'https://wa.me/50686529837?text=' + quote('Hola Jenny, este es mi estado de cuenta\n\n' + estado_txt)
    return render_template('mis_puntos.html', cedula=cedula, result=result, is_super=is_super, admin_message=admin_message, admin_error=admin_error, donacion_message=donacion_message, donacion_error=donacion_error, cumpleaneros=cumpleaneros, todos_hikers=todos_hikers, eventos_redimir=eventos_redimir, whatsapp_url=whatsapp_url, registros=registros, no_registrado=no_registrado, registro_whatsapp_url=registro_whatsapp_url, pendiente_password=pendiente_password, nombre_bienvenida=nombre_bienvenida, estado_whatsapp_url=estado_whatsapp_url, estado_coordinador_url=estado_coordinador_url, telefono_registrado=telefono_registrado)

