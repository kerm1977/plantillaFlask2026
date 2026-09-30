# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""Exportación Single Page Offline: HTML autónomo con buscador y tarjetas QR."""
import os
import base64
from flask import request, Response, render_template, current_app
from db import db
from routes.forms_responses_utils import _fmt_tel


def _static_img_b64(rel_path):
    """Devuelve una imagen de static/ como data URI base64, o None si no existe."""
    if not rel_path:
        return None
    path = os.path.join(current_app.static_folder, rel_path)
    if not os.path.exists(path):
        return None
    ext = 'png' if rel_path.lower().endswith('.png') else 'jpeg'
    with open(path, 'rb') as fh:
        return f'data:image/{ext};base64,' + base64.b64encode(fh.read()).decode()


def _export_singlepage_offline(form, fields, responses):
    """Genera una página HTML offline con buscador y la tarjeta QR de agenda
    (logo, foto, puntos, datos y código QR) para cada persona que respondió."""
    import re
    from datetime import datetime
    from models import Hiker, User, Event
    from routes.admin_actions import _tarjeta_url, _generar_qr_usuario
    from modules.points_engine import get_points_engine

    engine = get_points_engine()
    logo_b64 = _static_img_b64('logo.png')
    default_avatar_b64 = _static_img_b64('default.png')

    # Evento/caminata seleccionada para la pestaña de información
    evento_data = None
    event_id = request.args.get('event_id', type=int)
    if event_id:
        ev = Event.query.get(event_id)
        if ev:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            def _fecha_linda(s):
                if not s:
                    return ''
                p = s.split('-')
                if len(p) == 3:
                    try:
                        return f"{int(p[2])} de {meses[int(p[1]) - 1]} del {p[0]}"
                    except (ValueError, IndexError):
                        return s
                return s
            lugar = (ev.lugar_salida or '').replace('SEGURO_', '')
            fecha_actividad = (_fecha_linda(ev.fecha_unica) if (ev.dias or 1) <= 1
                               else f"Del {_fecha_linda(ev.fecha_inicio)} al {_fecha_linda(ev.fecha_regreso)}")
            evento_data = {
                'nombre': ev.nombre_lugar or '',
                'actividad': ev.actividad or '',
                'dificultad': ev.dificultad or '',
                'tipo_terreno': ev.tipo_terreno or '',
                'provincia': ev.provincia or '',
                'moneda': ev.moneda or '₡',
                'precio': ev.precio or 0,
                'reserva': ev.reserva or 0,
                'precio_buseta': ev.precio_buseta or 0,
                'kilometros': ev.kilometros or 0,
                'capacidad': (ev.capacidad or '').replace('AGOTADO_', ''),
                'dias': ev.dias or 1,
                'fecha_actividad': fecha_actividad,
                'hora_salida': ev.hora_salida or '',
                'lugar_salida': lugar,
                'puntos_recogida': ev.puntos_recogida or '',
                'sinpe': ev.sinpe or '',
                'cuenta': ev.cuenta or '',
                'incluye': [i.strip() for i in (ev.incluye or '').split(',') if i.strip()],
                'itinerario': ev.itinerario or '',
                'texto_referencia': ev.texto_referencia or '',
                'enlace_extra': ev.enlace_extra or '',
                'organicmaps_url': ev.organicmaps_url or '',
                'zona_alto_riesgo': bool(ev.zona_alto_riesgo),
                'is_sold_out': bool(ev.is_sold_out or (ev.capacidad or '').startswith('AGOTADO')),
                'poster_b64': _static_img_b64(f'uploads/{ev.poster}') if ev.poster else default_avatar_b64,
            }

    def _resolver_user(hiker, bound_email):
        user = None
        if bound_email:
            user = User.query.filter(db.func.lower(User.email) == bound_email).first()
        if not user and hiker and hiker.telefono:
            user = User.query.filter_by(phone=hiker.telefono).first()
        if not user and hiker and hiker.nombre_completo:
            objetivo = hiker.nombre_completo.strip().lower()
            for u in User.query.all():
                if f'{u.name} {u.last_name_1} {u.last_name_2}'.strip().lower() == objetivo:
                    user = u
                    break
        return user

    personas = []
    for r in responses:
        cedula_limpia = re.sub(r'\D', '', str(r.cedula or ''))
        hiker = None
        if cedula_limpia:
            for h in Hiker.query.all():
                if h.cedula and re.sub(r'\D', '', str(h.cedula)) == cedula_limpia:
                    hiker = h
                    break
        bound_email = (hiker.card_email or '').strip().lower() if hiker else ''
        user = _resolver_user(hiker, bound_email)

        # QR: mismo enlace inmutable que el QR de la agenda (requiere expediente)
        qr_b64, card_url = None, ''
        if hiker:
            card_url = _tarjeta_url(user, hiker)
            qr_b64 = _generar_qr_usuario(user, hiker)
            bound_email = (hiker.card_email or '').strip().lower()

        # Foto: avatar del usuario si existe, si no, default
        avatar_file = (user.avatar if user else None) or 'default.png'
        if avatar_file != 'default.png' and not avatar_file.startswith('uploads/'):
            avatar_file = 'uploads/' + avatar_file
        avatar_b64 = _static_img_b64(avatar_file) or default_avatar_b64

        nacimiento = ''
        if user and user.dob:
            nacimiento = user.dob.strftime('%d/%m/%Y')
        elif hiker and hiker.fecha_nacimiento:
            nacimiento = hiker.fecha_nacimiento.strftime('%d/%m/%Y')
        elif r.fecha_nacimiento_dia and r.fecha_nacimiento_mes and r.fecha_nacimiento_anio:
            nacimiento = f'{r.fecha_nacimiento_dia}/{r.fecha_nacimiento_mes}/{r.fecha_nacimiento_anio}'

        telefono = (hiker.telefono if hiker else '') or r.telefono or (user.phone if user else '') or ''
        phone_code = (user.phone_code or '') if user else ''
        if phone_code:
            telefono = f'{phone_code} {telefono}'.strip()
        else:
            telefono = _fmt_tel(telefono, form)

        email_display = bound_email if bound_email and '@' in bound_email else (r.email or '')

        cedula_puntos = (hiker.cedula if hiker else '') or r.cedula or ''
        puntos_total = engine.total_by_cedula(cedula_puntos) if cedula_puntos else 0

        nombre = (hiker.nombre_completo if hiker else '') or r.nombre_completo or 'Sin nombre'
        personas.append({
            'nombre': nombre,
            'cedula': (hiker.cedula if hiker else '') or r.cedula or '',
            'email': email_display,
            'telefono': telefono,
            'tipo_sangre': (hiker.tipo_sangre if hiker else '') or r.tipo_sangre or '?',
            'nacimiento': nacimiento,
            'pasaporte': (hiker.pasaporte if hiker else '') or r.pasaporte or '',
            'alergias': (hiker.alergias if hiker else '') or r.alergias or 'Ninguna',
            'cronicas': (hiker.enfermedades_cronicas if hiker else '') or r.enfermedades_cronicas or 'Ninguna',
            'emerg_nombre': (hiker.contacto_emergencia_nombre if hiker else '') or r.contacto_emergencia_nombre or '',
            'emerg_tel': _fmt_tel((hiker.contacto_emergencia_telefono if hiker else '') or r.contacto_emergencia_telefono or '', form),
            'whatsapp': (user.whatsapp if user else '') or '',
            'direccion': (user.address if user else '') or '',
            'institucion': (user.institution if user else '') or '',
            'info_adicional': (user.other_info if user else '') or '',
            'reserva': r.reservation_number or '',
            'puntos': puntos_total,
            'qr_b64': qr_b64,
            'card_url': card_url,
            'avatar_b64': avatar_b64,
            'search': ' '.join([nombre, (hiker.cedula if hiker else '') or r.cedula or '',
                                (hiker.pasaporte if hiker else '') or r.pasaporte or '',
                                telefono, email_display]).lower(),
        })

    # Secciones "Quiénes Somos" seleccionadas por toggles
    from routes.pages import _get_site_text
    secciones = {}
    if request.args.get('include_historia') == '1':
        secciones['Historia'] = _get_site_text('quienes_somos')
    if request.args.get('include_mision') == '1':
        secciones['Misión'] = _get_site_text('mision')
    if request.args.get('include_oracion') == '1':
        secciones['Oración'] = _get_site_text('oracion')
    secciones = {k: v for k, v in secciones.items() if v}

    mostrar_puntos = request.args.get('include_puntos') == '1'

    html = render_template('singlepage_offline.html', form=form, personas=personas,
                           evento=evento_data, secciones=secciones, mostrar_puntos=mostrar_puntos,
                           logo_b64=logo_b64, generado=datetime.now().strftime('%d/%m/%Y %H:%M'))
    return Response(html, mimetype='text/html',
                    headers={'Content-Disposition': f'attachment; filename="{form.name} - offline.html"'})
