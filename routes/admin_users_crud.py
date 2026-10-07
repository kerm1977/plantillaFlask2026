# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/admin_users_crud.py - Crear/actualizar usuarios (superusuario)
import os
import random
import re
import string
from datetime import datetime
from flask import request, jsonify, session
from models import User, Hiker
from users import hash_password
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS
from routes.admin_actions import (_hiker_por_cedula_limpia,
                                  _hiker_por_pasaporte_limpio,
                                  _tarjeta_url, _generar_qr_usuario)


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
    phone = re.sub(r'\D', '', request.form.get('phone', '').strip())
    password = request.form.get('password', '')

    if not name or not email or not last_name_1 or not phone:
        return jsonify({'error': 'Nombre, 1° apellido, correo y teléfono son obligatorios'}), 400
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
        phone=phone,
        whatsapp=phone,
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
