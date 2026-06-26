import os
import secrets
from flask import request, jsonify, session, redirect, url_for, render_template
from models import User
from users import hash_password, check_password
from db import db
from datetime import datetime, timedelta
from urllib.parse import quote
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS
from security import check_rate_limit, validate_password_strength


@bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').lower()
    
    if not check_rate_limit(email):
        return jsonify({'error': 'Demasiados intentos. Espere 15 minutos.'}), 429
    
    user = User.query.filter_by(email=email).first()
    if user and check_password(data.get('password'), user.password_hash):
        if user.status == 'Bloqueado':
            return jsonify({'error': 'Usuario bloqueado'}), 403
        session['user_id'] = user.id
        session['role'] = user.role
        session['avatar'] = user.avatar or 'default.png'
        return jsonify({'success': True})
    return jsonify({'error': 'Credenciales inválidas'}), 401


@bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    password = data.get('password', '')
    
    valid, msg = validate_password_strength(password)
    if not valid:
        return jsonify({'error': msg}), 400
    
    if User.query.filter_by(email=data.get('email').lower()).first():
        return jsonify({'error': 'Email ya registrado'}), 400
        
    try:
        new_user = User(
            name=data.get('name'),
            last_name_1=data.get('last_name_1'),
            last_name_2=data.get('last_name_2'),
            email=data.get('email').lower(),
            password_hash=hash_password(password)
        )
        
        if data.get('phone_code'): new_user.phone_code = data.get('phone_code')
        if data.get('phone'): new_user.phone = data.get('phone')
        if data.get('dob'): new_user.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date()

        if data.get('whatsapp') and hasattr(new_user, 'whatsapp'): new_user.whatsapp = data.get('whatsapp')
        if data.get('facebook') and hasattr(new_user, 'facebook'): new_user.facebook = data.get('facebook')
        if data.get('instagram') and hasattr(new_user, 'instagram'): new_user.instagram = data.get('instagram')
        if data.get('address') and hasattr(new_user, 'address'): new_user.address = data.get('address')
        if data.get('institution') and hasattr(new_user, 'institution'): new_user.institution = data.get('institution')
        if data.get('other_info') and hasattr(new_user, 'other_info'): new_user.other_info = data.get('other_info')

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback() 
        return jsonify({'error': str(e)}), 500


@bp.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    try:
        user.name = request.form.get('name', user.name)
        user.last_name_1 = request.form.get('last_name_1', user.last_name_1)
        user.last_name_2 = request.form.get('last_name_2', user.last_name_2)
        user.email = request.form.get('email', user.email).lower()
        
        if request.form.get('phone_code'): user.phone_code = request.form.get('phone_code')
        if request.form.get('phone'): user.phone = request.form.get('phone')
        
        dob_str = request.form.get('dob')
        if dob_str: user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        if request.form.get('whatsapp') and hasattr(user, 'whatsapp'): user.whatsapp = request.form.get('whatsapp')
        if request.form.get('facebook') and hasattr(user, 'facebook'): user.facebook = request.form.get('facebook')
        if request.form.get('instagram') and hasattr(user, 'instagram'): user.instagram = request.form.get('instagram')
        if request.form.get('address') and hasattr(user, 'address'): user.address = request.form.get('address')
        if request.form.get('institution') and hasattr(user, 'institution'): user.institution = request.form.get('institution')
        if request.form.get('other_info') and hasattr(user, 'other_info'): user.other_info = request.form.get('other_info')

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
                
            filename = secure_filename(avatar_file.filename)
            filename = f"user_{user.id}_{filename}"
            static_folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(static_folder, exist_ok=True)
            filepath = os.path.join(static_folder, filename)
            avatar_file.save(filepath)
            user.avatar = f"uploads/{filename}" 

        db.session.commit()
        session['avatar'] = user.avatar or 'default.png'
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno al guardar los datos'}), 500


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))


@bp.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'ok': False, 'error': 'No existe una cuenta con ese correo'}), 404

    token = secrets.token_hex(20)
    expires = (datetime.utcnow() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    user.reset_token = token
    user.reset_expires = expires
    db.session.commit()

    reset_url = f"{request.host_url}reset/{token}"
    phone = (user.whatsapp or user.phone or '').strip().replace(' ', '').replace('-', '')
    if phone and not phone.startswith('+'):
        phone = '506' + phone

    result = {'ok': True, 'reset_url': reset_url}
    if phone:
        msg = (f"\U0001f510 *Recuperar Contrase\u00f1a*\n\n"
               f"Hola {user.name}, usa este enlace para crear una nueva contrase\u00f1a:\n"
               f"{reset_url}\n\n"
               f"\u23f1\ufe0f V\u00e1lido por 2 horas. Si no solicitaste esto, ign\u00f3ralo.")
        result['whatsapp_url'] = f"https://wa.me/{phone}?text={quote(msg)}"
    return jsonify(result)


@bp.route('/reset/<token>', methods=['GET'])
def reset_password_page(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_expires:
        return render_template('reset_password.html', valid=False, token=token)
    try:
        expires = datetime.strptime(user.reset_expires, '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() > expires:
            return render_template('reset_password.html', valid=False, token=token)
    except Exception:
        return render_template('reset_password.html', valid=False, token=token)
    return render_template('reset_password.html', valid=True, token=token, user_name=user.name)


@bp.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token', '')
    new_pass = data.get('password', '').strip()
    
    valid, msg = validate_password_strength(new_pass)
    if not valid:
        return jsonify({'ok': False, 'error': msg}), 400
    if not token:
        return jsonify({'ok': False, 'error': 'Token requerido'}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'ok': False, 'error': 'Token inválido o expirado'}), 400
    try:
        expires = datetime.strptime(user.reset_expires, '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() > expires:
            return jsonify({'ok': False, 'error': 'El enlace ha expirado'}), 400
    except Exception:
        return jsonify({'ok': False, 'error': 'Token inválido'}), 400

    user.password_hash = hash_password(new_pass)
    user.reset_token = None
    user.reset_expires = None
    db.session.commit()
    return jsonify({'ok': True})
