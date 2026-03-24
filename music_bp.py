# ARCHIVO: music_bp.py
import os
from flask import Blueprint, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
from db import db
from models import Song

music_bp = Blueprint('music_bp', __name__)

# Configuración de ruta absoluta compatible con Flask
basedir = os.path.abspath(os.path.dirname(__file__))
MUSIC_FOLDER = os.path.join(basedir, 'static', 'music')

# Asegura que la carpeta exista
os.makedirs(MUSIC_FOLDER, exist_ok=True)

@music_bp.route('/reproductor')
def render_player():
    """Renderiza la SPA del reproductor (Mantenido por si navegan directo)"""
    return render_template('music.html')

@music_bp.route('/api/songs', methods=['GET'])
def get_songs():
    """Obtiene la lista de canciones y auto-escanea archivos manuales"""
    # --- NUEVO: Escaneo Automático de Archivos Subidos Manualmente ---
    existing_songs = {s.filename for s in Song.query.all()}
    
    try:
        for file in os.listdir(MUSIC_FOLDER):
            if file.endswith('.mp3') and file not in existing_songs:
                base_name = os.path.splitext(file)[0]
                cover_file = None
                
                # Buscar una imagen que coincida (con o sin prefijo 'cover_')
                for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                    if os.path.exists(os.path.join(MUSIC_FOLDER, f"{base_name}{ext}")):
                        cover_file = f"{base_name}{ext}"
                        break
                    elif os.path.exists(os.path.join(MUSIC_FOLDER, f"cover_{base_name}{ext}")):
                        cover_file = f"cover_{base_name}{ext}"
                        break
                
                # Insertar automáticamente en la Base de Datos
                new_song = Song(
                    title=base_name.replace('_', ' ').title(),
                    filename=file,
                    cover_filename=cover_file
                )
                db.session.add(new_song)
        
        db.session.commit()
    except Exception as e:
        print(f"Error escaneando música: {e}")
    # -----------------------------------------------------

    songs = Song.query.order_by(Song.id.desc()).all()
    return jsonify([{
        'id': s.id,
        'title': s.title,
        'filename': s.filename,
        'cover': s.cover_filename or 'logo.png'
    } for s in songs])

@music_bp.route('/api/songs', methods=['POST'])
def upload_song():
    """Sube audio (Solo Superusuario)"""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    if 'audio' not in request.files:
        return jsonify({'error': 'No file'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(audio_file.filename)
    audio_file.save(os.path.join(MUSIC_FOLDER, filename))

    cover_filename = None
    if 'cover' in request.files:
        cover_file = request.files['cover']
        if cover_file.filename != '':
            cover_filename = f"cover_{secure_filename(cover_file.filename)}"
            cover_file.save(os.path.join(MUSIC_FOLDER, cover_filename))

    new_song = Song(title=request.form.get('title', filename), filename=filename, cover_filename=cover_filename)
    db.session.add(new_song)
    db.session.commit()

    return jsonify({'message': 'Subido correctamente', 'id': new_song.id})

@music_bp.route('/api/songs/<int:song_id>', methods=['PUT'])
def edit_song(song_id):
    """Edita canción (Solo Superusuario)"""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    song = Song.query.get_or_404(song_id)
    
    if 'title' in request.form:
        song.title = request.form['title']
        
    if 'cover' in request.files:
        cover_file = request.files['cover']
        if cover_file.filename != '':
            cover_filename = f"cover_{song.id}_{secure_filename(cover_file.filename)}"
            cover_file.save(os.path.join(MUSIC_FOLDER, cover_filename))
            song.cover_filename = cover_filename
            
    db.session.commit()
    return jsonify({'message': 'Actualizado'})

@music_bp.route('/api/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    """Elimina canción (Solo Superusuario)"""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    song = Song.query.get_or_404(song_id)
    try:
        if song.filename:
            path = os.path.join(MUSIC_FOLDER, song.filename)
            if os.path.exists(path): os.remove(path)
        
        if song.cover_filename and song.cover_filename != 'logo.png':
            cover_path = os.path.join(MUSIC_FOLDER, song.cover_filename)
            if os.path.exists(cover_path): os.remove(cover_path)

        db.session.delete(song)
        db.session.commit()
        return jsonify({'message': 'Eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500