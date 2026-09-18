import os
import random
import re
import secrets
import string
import io
import base64
from datetime import datetime
from flask import request, jsonify, session, current_app, url_for
from itsdangerous import URLSafeSerializer
from models import User, Hiker
from users import hash_password
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS
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


@bp.route('/api/admin/update_user/<int:user_id>', methods=['POST'])
def admin_update_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    u = User.query.get_or_404(user_id)

    u.name = request.form.get('name', u.name)
    u.last_name_1 = request.form.get('last_name_1', u.last_name_1)
    u.last_name_2 = request.form.get('last_name_2', u.last_name_2)
    u.email = request.form.get('email', u.email).lower()

    new_role = request.form.get('role')
    if new_role:
        u.role = new_role
        if new_role == 'Superusuario': u.weight = 100
        elif new_role == 'Administrador': u.weight = 50
        elif new_role == 'Colaborador': u.weight = 10
        else: u.weight = 1

    new_pass = request.form.get('password')
    if new_pass:
        u.password_hash = hash_password(new_pass)

    if request.form.get('phone'):
        u.phone = re.sub(r'\D', '', request.form.get('phone'))

    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"error": "Formato de imagen no permitido"}), 400

        filename = secure_filename(avatar_file.filename)
        filename = f"user_{u.id}_{filename}"
        static_folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
        os.makedirs(static_folder, exist_ok=True)
        avatar_file.save(os.path.join(static_folder, filename))
        u.avatar = f"uploads/{filename}"

    # Sincronizar / actualizar la información del Caminante (CRM) asociada
    cedula = request.form.get('cedula', '').strip()
    if cedula:
        if not cedula.isdigit():
            return jsonify({'error': 'La cédula solo debe contener números'}), 400

    pasaporte = request.form.get('pasaporte', '').strip()
    nombres_em = [v.strip() for v in request.form.getlist('contacto_emergencia_nombre[]') if v.strip()]
    telefonos_em = [re.sub(r'\D', '', v) for v in request.form.getlist('contacto_emergencia_telefono[]') if v.strip()]

    crm_fields_present = any([cedula, pasaporte, request.form.get('fecha_nacimiento'), request.form.get('dob'),
                              request.form.get('tipo_sangre'), request.form.get('alergias'),
                              request.form.get('enfermedades_cronicas'), nombres_em, telefonos_em])

    if cedula or crm_fields_present:
        hiker = None
        if cedula:
            hiker = _hiker_por_cedula_limpia(cedula)
        if not hiker and u.phone:
            phone_clean = re.sub(r'\D', '', u.phone)
            if phone_clean:
                for h in Hiker.query.all():
                    if h.telefono and re.sub(r'\D', '', h.telefono) == phone_clean:
                        hiker = h
                        break
        if not hiker and cedula:
            hiker = Hiker(cedula=cedula)
            db.session.add(hiker)

        if hiker:
            # Validar duplicados excluyendo el caminante actual
            if cedula and _hiker_por_cedula_limpia(cedula, hiker.id):
                return jsonify({'error': 'Ya este usuario existe. Consultar con los superusuarios del sitio web.'}), 400
            if pasaporte and _hiker_por_pasaporte_limpio(pasaporte, hiker.id):
                return jsonify({'error': 'Ya este usuario existe. Consultar con los superusuarios del sitio web.'}), 400

            if cedula:
                hiker.cedula = cedula
            hiker.nombre_completo = f"{u.name} {u.last_name_1} {u.last_name_2}".strip()
            hiker.telefono = u.phone or hiker.telefono
            hiker.pasaporte = pasaporte or hiker.pasaporte
            hiker.tipo_sangre = request.form.get('tipo_sangre', hiker.tipo_sangre)
            hiker.alergias = request.form.get('alergias', hiker.alergias)
            hiker.enfermedades_cronicas = request.form.get('enfermedades_cronicas', hiker.enfermedades_cronicas)
            hiker.contacto_emergencia_nombre = ' | '.join(nombres_em) if nombres_em else (hiker.contacto_emergencia_nombre or '')
            hiker.contacto_emergencia_telefono = ' | '.join(telefonos_em) if telefonos_em else (hiker.contacto_emergencia_telefono or '')

            f_nac = request.form.get('fecha_nacimiento') or request.form.get('dob')
            if f_nac:
                try:
                    fecha_nac = datetime.strptime(f_nac, '%Y-%m-%d').date()
                    hiker.fecha_nacimiento = fecha_nac
                    u.dob = fecha_nac
                except: pass

            if not hiker.pin_secreto:
                for _ in range(10):
                    candidate = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    if not Hiker.query.filter_by(pin_secreto=candidate).first():
                        hiker.pin_secreto = candidate
                        break

    db.session.commit()
    return jsonify({'success': True})


@bp.route('/api/admin/create_user', methods=['POST'])
def admin_create_user():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    email = request.form.get('email', '').strip().lower()
    cedula = request.form.get('cedula', '').strip()
    name = request.form.get('name', '').strip()
    last_name_1 = request.form.get('last_name_1', '').strip()
    last_name_2 = request.form.get('last_name_2', '').strip()
    password = request.form.get('password', '')

    if not name or not email or not last_name_1:
        return jsonify({'error': 'Nombre, 1° apellido y email son obligatorios'}), 400
    if cedula and not cedula.isdigit():
        return jsonify({'error': 'La cédula solo debe contener números'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Ya existe un usuario con ese email'}), 400
    if cedula and _hiker_por_cedula_limpia(cedula):
        return jsonify({'error': 'Ya este usuario existe. Consultar con los superusuarios del sitio web.'}), 400

    pasaporte = request.form.get('pasaporte', '').strip()
    if pasaporte and _hiker_por_pasaporte_limpio(pasaporte):
        return jsonify({'error': 'Ya este usuario existe. Consultar con los superusuarios del sitio web.'}), 400

    nombres_em = [v.strip() for v in request.form.getlist('contacto_emergencia_nombre[]') if v.strip()]
    telefonos_em = [re.sub(r'\D', '', v) for v in request.form.getlist('contacto_emergencia_telefono[]') if v.strip()]

    new_user = User(
        name=name,
        last_name_1=last_name_1,
        last_name_2=last_name_2,
        email=email,
        password_hash=hash_password(password),
        role=request.form.get('role', 'Usuario'),
        phone=re.sub(r'\D', '', request.form.get('phone', '').strip()),
        whatsapp=re.sub(r'\D', '', request.form.get('phone', '').strip()),
        dob=datetime.strptime(request.form.get('dob'), '%Y-%m-%d').date() if request.form.get('dob') else None,
        facebook=request.form.get('facebook', '').strip(),
        instagram=request.form.get('instagram', '').strip(),
        address=request.form.get('address', '').strip(),
        institution=request.form.get('institution', '').strip(),
        other_info=request.form.get('other_info', '').strip(),
        status='Activo'
    )

    role = new_user.role
    if role == 'Superusuario': new_user.weight = 100
    elif role == 'Administrador': new_user.weight = 50
    elif role == 'Colaborador': new_user.weight = 10
    else: new_user.weight = 1

    db.session.add(new_user)
    db.session.flush()

    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"error": "Formato de imagen no permitido"}), 400
        filename = secure_filename(avatar_file.filename)
        filename = f"user_{new_user.id}_{filename}"
        static_folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
        os.makedirs(static_folder, exist_ok=True)
        avatar_file.save(os.path.join(static_folder, filename))
        new_user.avatar = f"uploads/{filename}"

    f_nac = request.form.get('fecha_nacimiento') or request.form.get('dob')
    fecha_nac = None
    if f_nac:
        try:
            fecha_nac = datetime.strptime(f_nac, '%Y-%m-%d').date()
        except: pass

    phone = re.sub(r'\D', '', request.form.get('phone', '').strip())
    hiker = None
    if cedula:
        hiker = Hiker(
            cedula=cedula,
            nombre_completo=f"{name} {last_name_1} {last_name_2}".strip(),
            telefono=phone,
            pasaporte=pasaporte,
            tipo_sangre=request.form.get('tipo_sangre', '').strip(),
            fecha_nacimiento=fecha_nac,
            alergias=request.form.get('alergias', 'Ninguna').strip(),
            enfermedades_cronicas=request.form.get('enfermedades_cronicas', 'Ninguna').strip(),
            contacto_emergencia_nombre=' | '.join(nombres_em),
            contacto_emergencia_telefono=' | '.join(telefonos_em)
        )

        for _ in range(10):
            hiker.pin_secreto = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            if not Hiker.query.filter_by(pin_secreto=hiker.pin_secreto).first():
                break

        db.session.add(hiker)

    db.session.commit()

    if hiker:
        qr_b64 = _generar_qr_usuario(new_user, hiker)
        return jsonify({
            'success': True,
            'pin': hiker.pin_secreto,
            'user_id': new_user.id,
            'qr_base64': qr_b64,
            'card_url': _tarjeta_url(new_user, hiker),
            'card': {
                'name': f"{new_user.name} {new_user.last_name_1} {new_user.last_name_2}".strip(),
                'email': new_user.email or '',
                'phone': hiker.telefono or '',
                'blood': hiker.tipo_sangre or '',
                'pasaporte': hiker.pasaporte or '',
                'emergency_name': hiker.contacto_emergencia_nombre or '',
                'emergency_phone': hiker.contacto_emergencia_telefono or '',
                'alergias': hiker.alergias or '',
                'enfermedades': hiker.enfermedades_cronicas or '',
                'cedula': hiker.cedula or '',
                'puntos': 0
            }
        })

    return jsonify({'success': True, 'user_id': new_user.id})


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
