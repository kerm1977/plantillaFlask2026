# routes.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import User, Notification
from users import hash_password, check_password
from db import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    notifications = Notification.query.all()
    return render_template('home.html', notifications=notifications)

@bp.route('/profile')
def profile():
    """Ruta para visualizar el perfil del usuario logueado."""
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.home'))
        
    return render_template('perfil.html', user=user)

@bp.route('/dashboard')
def dashboard():
    """Ruta para el panel de administración exclusivo de Superusuarios."""
    # Verificación de seguridad: solo Superusuarios pueden acceder
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
        
    return render_template('dashboard.html')

@bp.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "PWA Dual App",
        "short_name": "DualApp",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#ff8c00"
    })

@bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email').lower()).first()
    if user and check_password(data.get('password'), user.password_hash):
        if user.status == 'Bloqueado':
            return jsonify({'error': 'Usuario bloqueado'}), 403
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({'success': True})
    return jsonify({'error': 'Credenciales inválidas'}), 401

@bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data.get('email').lower()).first():
         return jsonify({'error': 'Email ya registrado'}), 400
         
    try:
        new_user = User(
            name=data.get('name'),
            last_name_1=data.get('last_name_1'),
            last_name_2=data.get('last_name_2'),
            email=data.get('email').lower(),
            password_hash=hash_password(data.get('password'))
        )
        
        # Guardar campos dinámicos principales
        if data.get('phone_code'):
            new_user.phone_code = data.get('phone_code')
        if data.get('phone'):
            new_user.phone = data.get('phone')
        if data.get('dob'):
            new_user.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date()

        # Guardar el resto de opciones de "Información Adicional" (WhatsApp, Facebook, Instagram, etc)
        # Usamos hasattr para evitar que Flask colapse si aún no has agregado estas columnas a models.py
        if data.get('whatsapp') and hasattr(new_user, 'whatsapp'):
            new_user.whatsapp = data.get('whatsapp')
        if data.get('facebook') and hasattr(new_user, 'facebook'):
            new_user.facebook = data.get('facebook')
        if data.get('instagram') and hasattr(new_user, 'instagram'):
            new_user.instagram = data.get('instagram')
        if data.get('address') and hasattr(new_user, 'address'):
            new_user.address = data.get('address')
        if data.get('institution') and hasattr(new_user, 'institution'):
            new_user.institution = data.get('institution')
        if data.get('other_info') and hasattr(new_user, 'other_info'):
            new_user.other_info = data.get('other_info')

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback() # Revierte si hay error para no bloquear la BD
        print(f"Error grave en registro: {e}") # Se mostrará en tu consola de Flask
        return jsonify({'error': 'Error interno de base de datos al registrar'}), 500

@bp.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    try:
        # Recuperamos los datos principales del FormData
        user.name = request.form.get('name', user.name)
        user.last_name_1 = request.form.get('last_name_1', user.last_name_1)
        user.last_name_2 = request.form.get('last_name_2', user.last_name_2)
        user.email = request.form.get('email', user.email).lower()
        
        # Campos Dinámicos / Opcionales
        if request.form.get('phone_code'): user.phone_code = request.form.get('phone_code')
        if request.form.get('phone'): user.phone = request.form.get('phone')
        
        dob_str = request.form.get('dob')
        if dob_str:
            user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Recuperamos TODAS las opciones de Información Adicional posibles
        if request.form.get('whatsapp') and hasattr(user, 'whatsapp'):
            user.whatsapp = request.form.get('whatsapp')
        if request.form.get('facebook') and hasattr(user, 'facebook'):
            user.facebook = request.form.get('facebook')
        if request.form.get('instagram') and hasattr(user, 'instagram'):
            user.instagram = request.form.get('instagram')
        if request.form.get('address') and hasattr(user, 'address'):
            user.address = request.form.get('address')
        if request.form.get('institution') and hasattr(user, 'institution'):
            user.institution = request.form.get('institution')
        if request.form.get('other_info') and hasattr(user, 'other_info'):
            user.other_info = request.form.get('other_info')

        # Manejo de la subida del avatar
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            # Crear nombre seguro y único
            filename = secure_filename(avatar_file.filename)
            filename = f"user_{user.id}_{filename}"
            
            # Asegurar que la ruta 'static' existe
            static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
            os.makedirs(static_folder, exist_ok=True)
            
            filepath = os.path.join(static_folder, filename)
            avatar_file.save(filepath)
            user.avatar = filename # Actualizamos el campo de la BD

        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar perfil: {e}")
        return jsonify({'error': 'Error interno al guardar los datos'}), 500

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))