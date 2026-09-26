# ══ BLINDADO — DESCARGAS (herramienta de videos, solo superusuario) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Motor en descargas_dl.py (yt-dlp + ffmpeg). Solo superusuarios.
from flask import (render_template, session, request, jsonify,
                   send_file, redirect, url_for)
from routes import bp
import descargas_dl as dl


def _super():
    return session.get('role') == 'Superusuario'


@bp.route('/herramientas/descargas')
def descargas_pagina():
    if not _super():
        return redirect(url_for('main.home'))
    return render_template('descargas.html', formatos=dl.FORMATOS,
                           page_title='Descargar videos')


@bp.route('/api/descargas/iniciar', methods=['POST'])
def descargas_iniciar():
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    formato = data.get('formato') or 'mp4'
    if not dl.url_valida(url):
        return jsonify({'error': 'Enlace no válido'}), 400
    if formato not in dl.FORMATOS:
        return jsonify({'error': 'Formato no válido'}), 400
    return jsonify({'ok': True, 'job': dl.iniciar(url, formato)})


@bp.route('/api/descargas/estado/<jid>')
def descargas_estado(jid):
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    est = dl.estado(jid)
    if est is None:
        return jsonify({'error': 'Trabajo no encontrado'}), 404
    return jsonify({'ok': True, **est})


@bp.route('/api/descargas/archivo/<jid>')
def descargas_archivo(jid):
    if not _super():
        return redirect(url_for('main.home'))
    res = dl.archivo(jid)
    if not res:
        return redirect(url_for('main.descargas_pagina'))
    ruta, nombre = res
    return send_file(ruta, as_attachment=True, download_name=nombre)
