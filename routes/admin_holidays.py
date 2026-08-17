import os
from flask import render_template, session, redirect, url_for, jsonify, request
from routes import bp
from helpers.holidays import (
    get_all_holidays, get_holiday, update_holiday_override,
    list_music_files, MUSIC_DIR, create_custom_holiday,
    update_custom_holiday, delete_custom_holiday,
    get_background_music, update_background_music
)
from helpers.active_note import get_active_note, set_active_note, clear_active_note
from models_notes import Note
from werkzeug.utils import secure_filename


@bp.route('/admin/holidays', methods=['GET'])
def admin_holidays():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('admin_holidays.html', holidays=get_all_holidays(), canciones=list_music_files(), background_music=get_background_music(), notes=Note.query.order_by(Note.updated_at.desc()).all(), active_note=get_active_note())


@bp.route('/api/holidays', methods=['GET'])
def api_holidays():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    return jsonify({'holidays': get_all_holidays()})


@bp.route('/api/holidays/<holiday_id>', methods=['POST'])
def api_update_holiday(holiday_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    h = get_holiday(holiday_id)
    if h is None:
        return jsonify({'error': 'Feriado no encontrado'}), 404

    data = request.form
    song = data.get('song')
    uploaded = request.files.get('song_file')

    if uploaded and uploaded.filename:
        filename = secure_filename(uploaded.filename)
        if not os.path.isdir(MUSIC_DIR):
            os.makedirs(MUSIC_DIR, exist_ok=True)
        uploaded.save(os.path.join(MUSIC_DIR, filename))
        song = filename

    enabled = data.get('enabled', '').strip().lower() in ('true', '1', 'on')
    autoplay = data.get('autoplay', '').strip().lower() in ('true', '1', 'on')
    show_confetti = data.get('show_confetti', '').strip().lower() in ('true', '1', 'on')
    custom_message = data.get('custom_message', '').strip()
    show_player = data.get('show_player', '').strip().lower() in ('true', '1', 'on')
    superuser_only = data.get('superuser_only', '').strip().lower() in ('true', '1', 'on')
    link_url = data.get('link_url', '').strip()
    link_enabled = data.get('link_enabled', '').strip().lower() in ('true', '1', 'on')
    song = data.get('song', '').strip()

    if h.get('custom'):
        update_custom_holiday(
            holiday_id,
            {
                'title': data.get('title'),
                'subtitle': data.get('subtitle'),
                'icon': data.get('icon'),
                'month': data.get('month'),
                'day': data.get('day'),
                'end_month': data.get('end_month') or None,
                'end_day': data.get('end_day') or None,
                'enabled': enabled,
                'autoplay': 'true' if autoplay else 'false',
                'show_confetti': 'true' if show_confetti else 'false',
                'custom_message': custom_message,
                'show_player': 'true' if show_player else 'false',
                'superuser_only': 'true' if superuser_only else 'false',
                'link_url': link_url,
                'link_enabled': 'true' if link_enabled else 'false',
                'song': song
            }
        )
    else:
        update_holiday_override(
            holiday_id,
            enabled=enabled,
            autoplay=autoplay,
            show_confetti=show_confetti,
            custom_message=custom_message,
            show_player=show_player,
            end_month=data.get('end_month') or None,
            end_day=data.get('end_day') or None,
            superuser_only=superuser_only,
            link_url=link_url,
            link_enabled=link_enabled,
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            icon=data.get('icon'),
            song=song
        )
    return jsonify({'ok': True, 'holiday': get_holiday(holiday_id)})


@bp.route('/api/holidays/<holiday_id>/toggle', methods=['POST'])
def api_toggle_holiday(holiday_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    h = get_holiday(holiday_id)
    if h is None:
        return jsonify({'error': 'Feriado no encontrado'}), 404
    new_state = not h.get('enabled', True)
    if h.get('custom'):
        update_custom_holiday(holiday_id, {'enabled': new_state})
    else:
        update_holiday_override(holiday_id, enabled=new_state)
    return jsonify({'ok': True, 'enabled': new_state})


@bp.route('/api/holidays/custom', methods=['POST'])
def api_create_custom_holiday():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.form
    uploaded = request.files.get('song_file')
    song = data.get('song') or None
    if uploaded and uploaded.filename:
        filename = secure_filename(uploaded.filename)
        if not os.path.isdir(MUSIC_DIR):
            os.makedirs(MUSIC_DIR, exist_ok=True)
        uploaded.save(os.path.join(MUSIC_DIR, filename))
        song = filename
    new = create_custom_holiday({
        'title': data.get('title'),
        'subtitle': data.get('subtitle'),
        'icon': data.get('icon'),
        'month': data.get('month'),
        'day': data.get('day'),
        'end_month': data.get('end_month') or None,
        'end_day': data.get('end_day') or None,
        'enabled': data.get('enabled', '').strip().lower() in ('true', '1', 'on'),
        'autoplay': 'true' if data.get('autoplay', '').strip().lower() in ('true', '1', 'on') else 'false',
        'show_confetti': 'true' if data.get('show_confetti', '').strip().lower() in ('true', '1', 'on') else 'false',
        'custom_message': data.get('custom_message', '').strip(),
        'show_player': 'true' if data.get('show_player', '').strip().lower() in ('true', '1', 'on') else 'false',
        'superuser_only': 'true' if data.get('superuser_only', '').strip().lower() in ('true', '1', 'on') else 'false',
        'link_url': data.get('link_url', '').strip(),
        'link_enabled': 'true' if data.get('link_enabled', '').strip().lower() in ('true', '1', 'on') else 'false',
        'song': song
    })
    return jsonify({'ok': True, 'holiday': new})


@bp.route('/api/holidays/custom/<holiday_id>', methods=['DELETE'])
def api_delete_custom_holiday(holiday_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if delete_custom_holiday(holiday_id):
        return jsonify({'ok': True})
    return jsonify({'error': 'Feriado no encontrado'}), 404


@bp.route('/api/active-note', methods=['GET'])
def api_get_active_note():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    return jsonify({'ok': True, 'active_note': get_active_note()})


@bp.route('/api/active-note', methods=['POST'])
def api_set_active_note():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json() or request.form
    note_id = data.get('note_id')
    if not note_id:
        clear_active_note()
        return jsonify({'ok': True, 'active_note': None})
    is_public = str(data.get('is_public', '')).strip().lower() in ('true', '1', 'on')
    result = set_active_note(note_id, is_public)
    if not result:
        return jsonify({'error': 'Nota no encontrada'}), 404
    return jsonify({'ok': True, 'active_note': result})


@bp.route('/api/active-note', methods=['DELETE'])
def api_clear_active_note():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    clear_active_note()
    return jsonify({'ok': True})


@bp.route('/api/background-music', methods=['GET'])
def api_get_background_music():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    return jsonify({'ok': True, 'music': get_background_music()})


@bp.route('/api/background-music', methods=['POST'])
def api_update_background_music():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.form
    songs = request.form.getlist('songs')
    enabled = data.get('enabled', '').strip().lower() in ('true', '1', 'on')
    random = data.get('random', '').strip().lower() in ('true', '1', 'on')
    return jsonify({'ok': True, 'music': update_background_music(enabled=enabled, songs=songs, random=random)})
