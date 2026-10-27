# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_mis.py - Página "Mis Puntos" (consulta, donar, redimir)
import io
import re
from urllib.parse import quote
from datetime import datetime
from flask import request, session, render_template, redirect, url_for, jsonify, send_file
from db import db
from models import Hiker, Event, User, EventRegistration, HikerPoints
from modules.points_engine import get_points_engine
from modules.points_bonuses import get_points_bonuses
from modules.points_admin import get_points_admin
from modules.points_donations import birthday_hikers, donate
from modules import fidelidad, retos, retos_builder
from modules.estado_global import resumen_global, detalle_persona, estadisticas_persona
from modules.points_helpers import (is_past_event, get_puntos_password, set_notif_cleared,
                                    get_notif_cutoff, build_estado_cuenta_whatsapp,
                                    descargar_token, get_puntos_admin_visible)
from routes import bp
from routes.points import _current_user


@bp.route('/api/mis-puntos/exportar-whatsapp')
def mis_puntos_exportar_whatsapp():
    """Texto de WhatsApp con todas las personas: puntos que tienen y ganados.
    Solo superusuario (botón flotante en /mis-puntos)."""
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    filas = resumen_global()
    lineas = ['*PUNTOS — LA TRIBU DE LOS LIBRES*',
              datetime.now().strftime('%d/%m/%Y %H:%M'), '',
              '*Persona* | *Tiene* | *Ganó*']
    total_tiene = 0
    total_gano = 0
    for i, f in enumerate(filas, 1):
        lineas.append(f"{i}. {f['nombre']} — {f['total']} pts (ganó {f['ganados']})")
        total_tiene += f['total']
        total_gano += f['ganados']
    lineas += ['', f'*{len(filas)} personas — {total_tiene} pts disponibles · {total_gano} pts ganados*']
    texto = '\n'.join(lineas)
    return jsonify({'ok': True, 'personas': len(filas),
                    'url': 'https://wa.me/?text=' + quote(texto)})


def _personas_por_evento(event_id):
    """Personas con movimientos de puntos en una caminata: ganados,
    perdidos y neto, ordenadas alfabéticamente (solo superusuario)."""
    hikers = {re.sub(r'\D', '', h.cedula or ''): h.nombre_completo
              for h in Hiker.query.all()}
    por = {}
    for r in (HikerPoints.query.filter_by(event_id=event_id)
              .order_by(HikerPoints.created_at).all()):
        key = re.sub(r'\D', '', r.cedula or '')
        p = por.setdefault(key, {'cedula': key, 'ganados': 0, 'perdidos': 0, 'movs': []})
        pts = r.points or 0
        if pts > 0:
            p['ganados'] += pts
        elif pts < 0:
            p['perdidos'] += -pts
        p['movs'].append(r)
    lista = [{'cedula': p['cedula'],
              'nombre': hikers.get(p['cedula']) or '(sin registro)',
              'ganados': p['ganados'], 'perdidos': p['perdidos'],
              'neto': p['ganados'] - p['perdidos'],
              'movs': p['movs']} for p in por.values()]
    lista.sort(key=lambda x: (x['nombre'] or '').lower())
    return lista


@bp.route('/mis-puntos/caminata/<int:event_id>')
def mis_puntos_caminata(event_id):
    """Puntos por caminata: quién acumuló cuánto + total (solo superusuario)."""
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.mis_puntos'))
    event = Event.query.get_or_404(event_id)
    lista = _personas_por_evento(event_id)
    total = sum(p['neto'] for p in lista)
    ganados_total = sum(p['ganados'] for p in lista)
    perdidos_total = sum(p['perdidos'] for p in lista)
    lineas = [f'*{(event.nombre_lugar or "CAMINATA").upper()}*',
              f'{event.puntos or 0} pts por participación', '']
    for i, p in enumerate(lista, 1):
        lineas.append(f"{i}. {p['nombre']} — {p['neto']} pts")
    lineas += ['', f'*{len(lista)} personas — Total: {total} pts*']
    wa_url = 'https://wa.me/?text=' + quote('\n'.join(lineas))
    return render_template('mis_puntos_caminata.html', event=event, lista=lista,
                           total=total, ganados_total=ganados_total,
                           perdidos_total=perdidos_total, wa_url=wa_url)


@bp.route('/api/mis-puntos/caminata/<int:event_id>.txt')
def mis_puntos_caminata_txt(event_id):
    """TXT de una caminata: personas, ganados/perdidos/neto, movimientos
    y total de puntos acumulados (solo superusuario)."""
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    event = Event.query.get_or_404(event_id)
    lista = _personas_por_evento(event_id)
    sep = '=' * 64
    sep2 = '-' * 64
    L = [f"PUNTOS POR CAMINATA - {(event.nombre_lugar or '').upper()}",
         f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
         f"Puntos por participación: {event.puntos or 0}", sep]
    total = 0
    for i, p in enumerate(lista, 1):
        total += p['neto']
        L += ['',
              f"{i}. {p['nombre'].upper()} - Céd. {p['cedula']}",
              sep2,
              f"   Puntos ganados   : {p['ganados']}",
              f"   Puntos perdidos  : {p['perdidos']}",
              f"   Puntos netos     : {p['neto']}",
              '   Movimientos:']
        for r in p['movs']:
            L.append(f"      - {(r.tipo or ''):20} {r.points:+d}  "
                     f"{r.created_at.strftime('%d/%m/%Y %H:%M') if r.created_at else ''}"
                     + (f"  ({r.created_by})" if r.created_by else ''))
    L += ['', sep,
          f'   Personas con puntos : {len(lista)}',
          f'   TOTAL ACUMULADO     : {total} pts']
    buf = io.BytesIO('\n'.join(L).encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='text/plain; charset=utf-8', as_attachment=True,
                     download_name=f"puntos-{re.sub(r'[^a-z0-9]+', '-', (event.nombre_lugar or 'caminata').lower())}-{datetime.now().strftime('%Y%m%d-%H%M')}.txt")


@bp.route('/api/mis-puntos/exportar.txt')
def mis_puntos_exportar_txt():
    """TXT ordenado alfabéticamente con todo lo de puntos por persona:
    disponibles, ganados, perdidos, caminatas participadas y no
    participadas, nivel VIP; al final el total de puntos del sistema.
    Solo superusuario."""
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    filas = resumen_global()
    sep = '=' * 64
    sep2 = '-' * 64
    L = ['PUNTOS - LA TRIBU DE LOS LIBRES',
         f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", sep]
    tot_tiene = tot_gano = tot_perdio = 0
    for i, f in enumerate(filas, 1):
        tot_tiene += f['total']
        tot_gano += f['ganados']
        tot_perdio += f['perdidos']
        L += ['',
              f"{i}. {f['nombre'].upper()} - Céd. {f['cedula']}",
              sep2,
              f"   Puntos disponibles   : {f['total']}",
              f"   Puntos ganados       : {f['ganados']}",
              f"   Puntos perdidos      : {f['perdidos']}"]
        if f.get('donados'):
            L.append(f"   Puntos donados       : {f['donados']}")
        if f.get('obsequiados'):
            L.append(f"   Obsequios recibidos  : {f['obsequiados']}")
        L += [f"   Nivel VIP            : {f['vip_label']}",
              f"   Retiros              : {f['retiros']}",
              f"   Caminatas participadas ({len(f['caminatas_ok'])}):"]
        L += [f'      - {c}' for c in f['caminatas_ok']]
        L.append(f"   Caminatas sin participar ({len(f['caminatas_no'])}):")
        L += [f'      - {c}' for c in f['caminatas_no']]
    L += ['', sep,
          'RESUMEN GLOBAL DEL SISTEMA',
          f'   Personas registradas   : {len(filas)}',
          f'   PUNTOS EN EL SISTEMA   : {tot_tiene}  (total guardado)',
          f'   Puntos ganados total   : {tot_gano}',
          f'   Puntos perdidos total  : {tot_perdio}']
    buf = io.BytesIO('\n'.join(L).encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='text/plain; charset=utf-8', as_attachment=True,
                     download_name=f"puntos-latribu-{datetime.now().strftime('%Y%m%d-%H%M')}.txt")


@bp.route('/api/mis-puntos/salida', methods=['POST'])
def mis_puntos_salida():
    # BLINDADO: beacon de salida de "Mis puntos" — libera el marcador para que
    # la próxima entrada cuente como nueva consulta (no toca la sesión de acceso).
    session.pop('mis_puntos_counted', None)
    return ('', 204)


@bp.route('/mis-puntos/persona/<cedula>')
def mis_puntos_persona(cedula):
    # BLINDADO: detalle individual del estado global — solo superusuario.
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.mis_puntos'))
    persona = detalle_persona(cedula)
    if not persona:
        return redirect(url_for('main.mis_puntos'))
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    estado_txt = build_estado_cuenta_whatsapp(cedula, hiker)
    extra = ['', '-' * 30, 'FIDELIDAD',
             f'Nivel: {persona["fidelidad"]["nivel_label"]}',
             f'Estatus: {"Superusuario" if persona["es_super"] else "Regular"}',
             f'Caminatas participadas: {len(persona["caminatas_ok"])}',
             f'Caminatas ausentes: {len(persona["caminatas_no"])}']
    estado_txt += '\n'.join(extra)
    wa_url = 'https://wa.me/?text=' + quote(estado_txt)
    return render_template('mis_puntos_persona.html', p=persona, wa_url=wa_url,
                           retos_cumplidos=retos.cumplidos(cedula))


@bp.route('/mis-puntos/persona/<cedula>/pdf')
def mis_puntos_persona_pdf(cedula):
    # BLINDADO: PDF del estado de cuenta individual — solo superusuario.
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.mis_puntos'))
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return redirect(url_for('main.mis_puntos'))
    from modules.estado_cuenta_pdf import build_estado_cuenta_pdf
    from flask import Response
    return Response(build_estado_cuenta_pdf(cedula, hiker), mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.pdf'})


@bp.route('/mis-puntos', methods=['GET', 'POST'])
def mis_puntos():
    cedula = ''
    result = None
    is_super = session.get('role') == 'Superusuario'
    admin_message = session.pop('admin_message', None)
    admin_error = session.pop('admin_error', None)
    wa_aviso = session.pop('wa_aviso', '')
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
    carnet_wa_url = ''
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
                result['retos'] = retos.estados_todos(cedula)
                result['retos_custom'] = retos_builder.lista_custom(cedula)
                result['dl_token'] = descargar_token(cedula)
                result['perfil'] = {
                    'nombre_completo': hiker_found.nombre_completo or '',
                    'telefono': hiker_found.telefono or '',
                    'email': hiker_found.card_email or '',
                    'tipo_sangre': hiker_found.tipo_sangre or '',
                    'pasaporte': hiker_found.pasaporte or '',
                    'fecha_nacimiento': hiker_found.fecha_nacimiento.strftime('%Y-%m-%d') if hiker_found.fecha_nacimiento else '',
                    'alergias': hiker_found.alergias or '',
                    'enfermedades_cronicas': hiker_found.enfermedades_cronicas or '',
                    'contacto_emergencia_nombre': hiker_found.contacto_emergencia_nombre or '',
                    'contacto_emergencia_telefono': hiker_found.contacto_emergencia_telefono or '',
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
                tel_wa = ('506' + telefono_registrado) if telefono_registrado and len(telefono_registrado) <= 8 else telefono_registrado
                carnet_wa_url = ('https://wa.me/' + tel_wa if tel_wa else 'https://wa.me/') + '?text=' + quote(
                    'Te comparto el carnet de La Tribu de los Libres de ' + (hiker_found.nombre_completo or '') + '.')
                estado_txt = build_estado_cuenta_whatsapp(cedula, hiker_found)
                estado_whatsapp_url = ('https://wa.me/' + telefono_registrado if telefono_registrado else 'https://wa.me/') + '?text=' + quote(estado_txt)
                estado_coordinador_url = 'https://wa.me/50686529837?text=' + quote('Hola Jenny, este es mi estado de cuenta\n\n' + estado_txt)
    extra = {}
    if is_super:
        from models import PuntosEvento
        from modules.points_helpers import personas_con_puntos, get_lista_ocultar_ceros
        evts = PuntosEvento.query.order_by(PuntosEvento.id.desc()).all()
        ocultar = get_lista_ocultar_ceros()
        personas = personas_con_puntos()
        n_con_puntos = sum(1 for p in personas if p['total'] != 0)
        total_puntos_global = sum(p['total'] for p in personas if p['total'] > 0)
        if ocultar:
            personas = [p for p in personas if p['total'] != 0]
        extra = dict(
            eventos=evts,
            pe_eventos={e.id: {'nombre': e.nombre, 'puntos': e.puntos or 0,
                               'descripcion': e.descripcion or '', 'publico': bool(e.publico)}
                        for e in evts},
            personas_puntos=personas, ocultar_ceros=ocultar,
            n_con_puntos=n_con_puntos, n_personas=len(personas),
            total_puntos_global=total_puntos_global,
            puntos_password=get_puntos_password(),
            puntos_pwd_visible=get_puntos_admin_visible(),
            puntos_pwd_msg=session.pop('puntos_pwd_msg', None))
    return render_template('mis_puntos.html', cedula=cedula, result=result, is_super=is_super, admin_message=admin_message, admin_error=admin_error, donacion_message=donacion_message, donacion_error=donacion_error, cumpleaneros=cumpleaneros, todos_hikers=todos_hikers, todos_eventos=Event.query.order_by(Event.nombre_lugar).all() if is_super else [], eventos_redimir=eventos_redimir, whatsapp_url=whatsapp_url, registros=registros, no_registrado=no_registrado, registro_whatsapp_url=registro_whatsapp_url, pendiente_password=pendiente_password, nombre_bienvenida=nombre_bienvenida, estado_whatsapp_url=estado_whatsapp_url, estado_coordinador_url=estado_coordinador_url, telefono_registrado=telefono_registrado, estado_global=resumen_global() if is_super else [], carnet_wa_url=carnet_wa_url, wa_aviso=wa_aviso, stats=estadisticas_persona(cedula) if result else None, **extra)

