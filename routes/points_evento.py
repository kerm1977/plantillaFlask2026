# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_evento.py - Página de puntos por caminata (link público)
import re
from urllib.parse import quote
from flask import request, session, render_template, redirect, url_for
from models import Hiker, Event
from modules.points_engine import get_points_engine
from modules.points_bonuses import get_points_bonuses
from modules.points_admin import get_points_admin
from modules.points_donations import birthday_hikers, donate
from modules.points_helpers import get_puntos_password
from routes import bp
from routes.points import _current_user


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
        elif (hiker_check.status or 'Activo') == 'Bloqueado':
            error = 'Tu acceso está bloqueado. Contactá a los coordinadores de La Tribu.'
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
