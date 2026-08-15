import os
from flask import render_template, session, redirect, url_for, jsonify, request
from routes import bp
from helpers.holidays import (
    get_all_holidays, get_holiday, update_holiday_override,
    list_music_files, MUSIC_DIR, create_custom_holiday,
    update_custom_holiday, delete_custom_holiday
)
from werkzeug.utils import secure_filename


@bp.route('/admin/holidays', methods=['GET'])
def admin_holidays():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('admin_holidays.html', holidays=get_all_holidays(), canciones=list_music_files())


@bp.route('/api/holidays', methods=['GET'])
def api_holidays():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    return jsonify({'holidays': get_all_holidays()})


@bp.route('/api/holidays/<holiday_id>', methods=['POST'])
def api_update_holiday(holiday_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if get_holiday(holiday_id) is None:
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

    if h.get('custom'):
        update_custom_holiday(
            holiday_id,
            {
                'title': data.get('title'),
                'subtitle': data.get('subtitle'),
                'icon': data.get('icon'),
                'month': data.get('month'),
                'day': data.get('day'),
                'enabled': enabled,
                'song': song
            }
        )
    else:
        update_holiday_override(
            holiday_id,
            enabled=enabled,
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
        'enabled': data.get('enabled', '').strip().lower() in ('true', '1', 'on'),
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
