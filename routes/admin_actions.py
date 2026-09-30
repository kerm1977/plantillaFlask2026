# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# (crear/actualizar usuarios en admin_users_crud.py)
import re
import secrets
import io
import base64
from flask import request, jsonify, session, current_app, url_for
from itsdangerous import URLSafeSerializer
from models import User, Hiker
from db import db
from routes import bp
import qrcode

def _hiker_por_cedula_limpia(cedula_limpia, excluir_id=None):
    for h in Hiker.query.all():
        if not h.cedula:
            continue
        if excluir_id and h.id == excluir_id:
            continue
        if re.sub(r'\D', '', str(h.cedula)) == cedula_limpia:
            return h
    return None

def _hiker_por_pasaporte_limpio(pasaporte_limpio, excluir_id=None):
    pasaporte_limpio = (pasaporte_limpio or '').upper().replace(' ', '').replace('-', '')
    if not pasaporte_limpio:
        return None
    for h in Hiker.query.all():
        if not h.pasaporte:
            continue
        if excluir_id and h.id == excluir_id:
            continue
        if str(h.pasaporte).upper().replace(' ', '').replace('-', '') == pasaporte_limpio:
            return h
    return None

def _tarjeta_url(user, hiker):
    """URL permanente de la tarjeta. El correo (o token, si el contacto no tiene correo)
    queda vinculado la primera vez y nunca cambia — el QR es inmutable."""
    if not hiker.card_email:
        if user and user.email:
            hiker.card_email = user.email.strip().lower()
        else:
            hiker.card_email = secrets.token_hex(8)
        db.session.commit()
    return url_for('main.tarjeta', cedula=hiker.cedula, email=hiker.card_email, _external=True)


def _generar_qr_usuario(user, hiker):
    """Genera un QR con el enlace a la tarjeta pública del usuario (sin contraseña ni rol)."""
    qr = qrcode.make(_tarjeta_url(user, hiker))
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    return img_b64

# ==========================================
# RUTAS DE ADMINISTRACIÓN – ACCIONES
# ==========================================

@bp.route('/api/admin/toggle_status/<contact_id>', methods=['POST'])
def admin_toggle_status(contact_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if str(contact_id).startswith('h'):
        try:
            h = Hiker.query.get(int(str(contact_id)[1:]))
        except (ValueError, TypeError):
            h = None
        if not h:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        h.status = 'Bloqueado' if (h.status or 'Activo') == 'Activo' else 'Activo'
        db.session.commit()
        return jsonify({'success': True, 'new_status': h.status})
    try:
        uid = int(contact_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Contacto no encontrado'}), 404
    if uid == session['user_id']:
        return jsonify({'error': 'No puedes bloquear tu propia cuenta principal'}), 400

    u = User.query.get_or_404(uid)
    u.status = 'Bloqueado' if u.status == 'Activo' else 'Activo'
    db.session.commit()
    return jsonify({'success': True, 'new_status': u.status})


@bp.route('/api/admin/delete_user/<contact_id>', methods=['DELETE'])
def admin_delete_user(contact_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if str(contact_id).startswith('h'):
        try:
            h = Hiker.query.get(int(str(contact_id)[1:]))
        except (ValueError, TypeError):
            h = None
        if not h:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        from models import EventRegistration
        EventRegistration.query.filter_by(hiker_id=h.id).delete()
        db.session.delete(h)
        db.session.commit()
        return jsonify({'success': True})
    try:
        uid = int(contact_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Contacto no encontrado'}), 404
    if uid == session['user_id']:
        return jsonify({'error': 'No puedes eliminar tu propia cuenta principal'}), 400

    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/api/admin/usuario-card/<contact_id>', methods=['GET'])
def admin_usuario_card(contact_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    user = None
    hiker = None
    full_name = ''
    if str(contact_id).startswith('h'):
        try:
            hiker = Hiker.query.get(int(str(contact_id)[1:]))
        except (ValueError, TypeError):
            hiker = None
        if not hiker:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        full_name = hiker.nombre_completo or 'Contacto'
        if hiker.telefono:
            user = User.query.filter_by(phone=hiker.telefono).first()
        if not user:
            for u in User.query.all():
                if f'{u.name} {u.last_name_1} {u.last_name_2}'.strip().lower() == (hiker.nombre_completo or '').strip().lower():
                    user = u
                    break
    else:
        try:
            user = User.query.get(int(contact_id))
        except (ValueError, TypeError):
            user = None
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        full_name = f"{user.name} {user.last_name_1} {user.last_name_2}".strip()
        hiker = Hiker.query.filter_by(telefono=user.phone).first() if user.phone else None
        if not hiker:
            hiker = Hiker.query.filter_by(nombre_completo=full_name).first()
    if not hiker or not hiker.cedula:
        return jsonify({'error': 'Este contacto no tiene expediente (cédula) vinculado.'}), 404
    from modules.points_engine import get_points_engine
    puntos_total = get_points_engine().total_by_cedula(hiker.cedula)
    return jsonify({
        'success': True,
        'qr_base64': _generar_qr_usuario(user, hiker),
        'card_url': _tarjeta_url(user, hiker),
        'card': {
            'name': full_name,
            'email': (user.email if user else '') or '',
            'cedula': hiker.cedula or '',
            'phone': hiker.telefono or (user.phone if user else '') or '',
            'blood': hiker.tipo_sangre or '',
            'pasaporte': hiker.pasaporte or '',
            'emergency_name': hiker.contacto_emergencia_nombre or '',
            'emergency_phone': hiker.contacto_emergencia_telefono or '',
            'alergias': hiker.alergias or '',
            'enfermedades': hiker.enfermedades_cronicas or '',
            'puntos': puntos_total
        }
    })


@bp.route('/api/admin/hiker_by_cedula/<cedula>', methods=['GET'])
def admin_hiker_by_cedula(cedula):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    cedula_clean = re.sub(r'\D', '', cedula.strip())
    if not cedula_clean:
        return jsonify({'error': 'Cédula inválida'}), 400

    hiker = _hiker_por_cedula_limpia(cedula_clean)
    if not hiker:
        return jsonify({'found': False}), 404

    user = None
    if hiker.telefono:
        phone_clean = re.sub(r'\D', '', hiker.telefono)
        for u in User.query.all():
            if u.phone and re.sub(r'\D', '', u.phone) == phone_clean:
                user = u
                break

    def _parte_nombre(pos):
        nombres = (hiker.nombre_completo or '').split()
        return nombres[pos] if len(nombres) > pos else ''

    return jsonify({
        'found': True,
        'name': user.name if user else _parte_nombre(0),
        'last_name_1': user.last_name_1 if user else _parte_nombre(1),
        'last_name_2': user.last_name_2 if user else _parte_nombre(2),
        'phone': hiker.telefono or '',
        'pasaporte': hiker.pasaporte or '',
        'tipo_sangre': hiker.tipo_sangre or '',
        'fecha_nacimiento': hiker.fecha_nacimiento.isoformat() if hiker.fecha_nacimiento else '',
        'alergias': hiker.alergias or '',
        'enfermedades_cronicas': hiker.enfermedades_cronicas or '',
        'contacto_emergencia_nombre': hiker.contacto_emergencia_nombre or '',
        'contacto_emergencia_telefono': hiker.contacto_emergencia_telefono or '',
        'email': user.email if user else ''
    })


@bp.route('/api/admin/generar_enlace_publico', methods=['POST'])
def admin_generar_enlace_publico():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.get_json(silent=True) or {}
    accion = data.get('accion', 'crear')
    user_id = data.get('user_id')

    if accion not in ('crear', 'actualizar'):
        return jsonify({'error': 'Acción no válida'}), 400
    if accion == 'actualizar':
        if not user_id or not User.query.get(user_id):
            return jsonify({'error': 'Usuario no válido para actualizar'}), 400

    secret = current_app.config.get('SECRET_KEY') or 'dev-secret-change-me'
    serializer = URLSafeSerializer(secret, salt='public-user-link')
    token = serializer.dumps({'accion': accion, 'user_id': user_id})
    link_url = url_for('main.home', token=token, _external=True)
    return jsonify({'success': True, 'url': link_url})
