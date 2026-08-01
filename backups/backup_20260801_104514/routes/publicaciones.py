import os, json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import request, jsonify, session, render_template, redirect, url_for
from models import Publicacion, Raffle
from db import db
from routes import bp, _PROJECT_ROOT

_UPLOAD = os.path.join(_PROJECT_ROOT, 'static', 'uploads', 'publicaciones')
_MUSIC  = os.path.join(_PROJECT_ROOT, 'static', 'musica')
os.makedirs(_UPLOAD, exist_ok=True)
_IMG_EXT = {'png', 'jpg', 'jpeg', 'webp'}


def _save_img(file, prefix='img'):
    if not file or not file.filename: return None
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in _IMG_EXT: return None
    fn = secure_filename(f"{prefix}_{int(datetime.utcnow().timestamp())}.{ext}")
    file.save(os.path.join(_UPLOAD, fn))
    return fn


def _mp3_list():
    if not os.path.exists(_MUSIC): return []
    return sorted([f for f in os.listdir(_MUSIC) if f.lower().endswith('.mp3')])


def _pub_dict(p):
    return {
        'id': p.id, 'nombre': p.nombre or '',
        'logo_filename': p.logo_filename or '', 'flyer_filename': p.flyer_filename or '',
        'audio_filename': p.audio_filename or '',
        'fecha_inicio': p.fecha_inicio.strftime('%Y-%m-%d') if p.fecha_inicio else '',
        'fecha_fin': p.fecha_fin.strftime('%Y-%m-%d') if p.fecha_fin else '',
        'descripcion': p.descripcion or '', 'tipo_evento': p.tipo_evento or '',
        'rifa_url': p.rifa_url or '', 'rifa_url_2': p.rifa_url_2 or '',
        'lugar': p.lugar or '',
        'punto_salida': p.punto_salida or '', 'hora_encuentro': p.hora_encuentro or '',
        'recomendaciones': p.recomendaciones or '', 'desc_caminata': p.desc_caminata or '',
        'direccion': p.direccion or '', 'url_externa': p.url_externa or '',
        'mostrar': p.mostrar or '[]', 'sinpe_info': p.sinpe_info or '',
        'cuenta_info': p.cuenta_info or '',
        'colaborar_detalle': p.colaborar_detalle or 'Apoyo Sueños de Vida',
        'telefono': p.telefono or '', 'whatsapp': p.whatsapp or '',
        'facebook': p.facebook or '', 'instagram': p.instagram or '',
        'tiktok': p.tiktok or '', 'youtube': p.youtube or '',
    }


# ── ADMIN ─────────────────────────────────────────────────────────────────────
@bp.route('/admin/publicaciones')
def admin_publicaciones():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    items = Publicacion.query.order_by(Publicacion.fecha_inicio.desc()).all()
    rifas = Raffle.query.filter_by(is_active=True).order_by(Raffle.raffle_date.asc()).all()
    return render_template('publicaciones_admin.html',
                           items=items, rifas=rifas, mp3_files=_mp3_list())


@bp.route('/api/publicaciones', methods=['POST'])
def api_pub_create():
    if session.get('role') != 'Superusuario': return jsonify({'error': 'No autorizado'}), 403
    f = request.form
    if not f.get('nombre', '').strip(): return jsonify({'error': 'El nombre es obligatorio'}), 400
    try:
        fi = datetime.strptime(f['fecha_inicio'], '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Fecha de inicio inválida'}), 400
    pub = Publicacion(
        nombre=f['nombre'].strip(), fecha_inicio=fi,
        fecha_fin=datetime.strptime(f['fecha_fin'], '%Y-%m-%d').date() if f.get('fecha_fin') else None,
        descripcion=f.get('descripcion', ''), tipo_evento=f.get('tipo_evento', ''),
        rifa_url=f.get('rifa_url', ''), rifa_url_2=f.get('rifa_url_2', ''),
        lugar=f.get('lugar', ''),
        punto_salida=f.get('punto_salida', ''), hora_encuentro=f.get('hora_encuentro', ''),
        recomendaciones=f.get('recomendaciones', ''), desc_caminata=f.get('desc_caminata', ''),
        direccion=f.get('direccion', ''), url_externa=f.get('url_externa', ''),
        mostrar=f.get('mostrar', '[]'),
        sinpe_info=f.get('sinpe_info', ''), sinpe_info_2=f.get('sinpe_info_2', ''),
        sinpe_info_3=f.get('sinpe_info_3', ''), sinpe_info_4=f.get('sinpe_info_4', ''),
        cuenta_info=f.get('cuenta_info', ''), cuenta_info_2=f.get('cuenta_info_2', ''),
        cuenta_info_3=f.get('cuenta_info_3', ''), cuenta_info_4=f.get('cuenta_info_4', ''),
        audio_filename=f.get('audio_filename', ''),
        colaborar_detalle=f.get('colaborar_detalle', 'Apoyo Sueños de Vida'),
        telefono=f.get('telefono', ''), whatsapp=f.get('whatsapp', ''),
        facebook=f.get('facebook', ''), instagram=f.get('instagram', ''),
        tiktok=f.get('tiktok', ''), youtube=f.get('youtube', ''),
    )
    pub.logo_filename  = _save_img(request.files.get('logo'),  'logo')
    pub.flyer_filename = _save_img(request.files.get('flyer'), 'flyer')
    db.session.add(pub); db.session.commit()
    return jsonify({'ok': True, 'id': pub.id})


@bp.route('/api/publicaciones/<int:pid>', methods=['GET'])
def api_pub_get(pid):
    if session.get('role') != 'Superusuario': return jsonify({'error': 'No autorizado'}), 403
    return jsonify(_pub_dict(Publicacion.query.get_or_404(pid)))


@bp.route('/api/publicaciones/<int:pid>', methods=['PUT'])
def api_pub_update(pid):
    if session.get('role') != 'Superusuario': return jsonify({'error': 'No autorizado'}), 403
    p = Publicacion.query.get_or_404(pid)
    f = request.form
    for field in ['nombre', 'descripcion', 'tipo_evento', 'rifa_url', 'lugar', 'punto_salida',
                  'hora_encuentro', 'recomendaciones', 'desc_caminata', 'direccion',
                  'url_externa', 'mostrar', 'sinpe_info', 'sinpe_info_2', 'sinpe_info_3', 'sinpe_info_4',
                  'cuenta_info', 'cuenta_info_2', 'cuenta_info_3', 'cuenta_info_4', 'audio_filename',
                  'telefono', 'whatsapp', 'facebook', 'instagram', 'tiktok', 'youtube',
                  'rifa_url_2', 'colaborar_detalle']:
        if f.get(field) is not None:
            setattr(p, field, f.get(field))
    if f.get('fecha_inicio'):
        p.fecha_inicio = datetime.strptime(f['fecha_inicio'], '%Y-%m-%d').date()
    p.fecha_fin = datetime.strptime(f['fecha_fin'], '%Y-%m-%d').date() if f.get('fecha_fin') else None
    logo  = request.files.get('logo')
    flyer = request.files.get('flyer')
    if logo  and logo.filename:  p.logo_filename  = _save_img(logo,  'logo')
    if flyer and flyer.filename: p.flyer_filename = _save_img(flyer, 'flyer')
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/publicaciones/<int:pid>', methods=['DELETE'])
def api_pub_delete(pid):
    if session.get('role') != 'Superusuario': return jsonify({'error': 'No autorizado'}), 403
    db.session.delete(Publicacion.query.get_or_404(pid))
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/publicaciones/<int:pid>/toggle', methods=['POST'])
def api_pub_toggle(pid):
    if session.get('role') != 'Superusuario': return jsonify({'error': 'No autorizado'}), 403
    p = Publicacion.query.get_or_404(pid)
    p.is_active = not p.is_active
    db.session.commit()
    return jsonify({'ok': True, 'is_active': p.is_active})


# ── PÚBLICA ────────────────────────────────────────────────────────────────────
@bp.route('/eventos/<int:pid>')
def evento_detalle_pub(pid):
    pub = Publicacion.query.filter_by(id=pid, is_active=True).first_or_404()
    try:
        mostrar = json.loads(pub.mostrar or '[]')
    except Exception:
        mostrar = []
    rifas = Raffle.query.filter_by(is_active=True).order_by(Raffle.raffle_date.asc()).all()
    
    # Generar enlace de Google Calendar
    from helpers.google_calendar import generate_google_calendar_link_pub
    google_calendar_link = generate_google_calendar_link_pub(pub)
    
    return render_template('evento_detalle.html', pub=pub, mostrar=mostrar, rifas=rifas, mp3_files=_mp3_list(), google_calendar_link=google_calendar_link)


@bp.route('/eventos')
def eventos_publicos():
    items = Publicacion.query.filter_by(is_active=True).order_by(Publicacion.fecha_inicio.asc()).all()
    
    # Generar enlaces de Google Calendar para cada evento
    from helpers.google_calendar import generate_google_calendar_link_pub
    for item in items:
        item.google_calendar_link = generate_google_calendar_link_pub(item)
    
    return render_template('eventos_lista.html', items=items)


@bp.route('/api/publicaciones/<int:pid>/monto-recaudado', methods=['POST'])
def api_pub_monto_recaudado(pid):
    if session.get('role') != 'Superusuario': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    p = Publicacion.query.get_or_404(pid)
    p.monto_recaudado = data.get('monto', 0.0)
    p.payment_justification = data.get('justification', '')
    db.session.commit()
    return jsonify({'ok': True, 'monto': p.monto_recaudado})
