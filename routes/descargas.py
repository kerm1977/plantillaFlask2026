# ══ BLINDADO — DESCARGAS (herramienta de videos, solo superusuario) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Motor: descargas_dl.py (cola) + descargas_run.py (procesos)
#      + descargas_up.py (actualización). Solo superusuarios.
from flask import (render_template, session, request, jsonify,
                   send_file, redirect, url_for)
from routes import bp
import descargas_dl as dl
import descargas_up as up


def _super():
    return session.get('role') == 'Superusuario'


@bp.route('/herramientas/descargas')
def descargas_pagina():
    if not _super():
        return redirect(url_for('main.home'))
    return render_template('descargas.html', formatos=dl.FORMATOS,
                           max_sim=dl.MAX_SIMULTANEAS,
                           version=up.version_actual(),
                           page_title='Descargar videos')


@bp.route('/api/descargas/iniciar', methods=['POST'])
def descargas_iniciar():
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    data = request.get_json(silent=True) or {}
    urls = [u.strip() for u in (data.get('urls') or [])
            if dl.url_valida(u.strip())]
    formato = data.get('formato') or 'mp4'
    if not urls:
        return jsonify({'error': 'Pegá al menos un enlace válido'}), 400
    if formato not in dl.FORMATOS:
        return jsonify({'error': 'Formato no válido'}), 400
    lid = dl.iniciar_lote(urls[:50], formato,
                          data.get('extra') or '',
                          data.get('max_par') or 2)
    return jsonify({'ok': True, 'lote': lid})


@bp.route('/api/descargas/lote/<lid>')
def descargas_lote(lid):
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    jobs = dl.lote(lid)
    if jobs is None:
        return jsonify({'error': 'Lote no encontrado'}), 404
    return jsonify({'ok': True, 'jobs': jobs})


@bp.route('/api/descargas/archivo/<jid>')
def descargas_archivo(jid):
    if not _super():
        return redirect(url_for('main.home'))
    res = dl.archivo(jid)
    if not res:
        return redirect(url_for('main.descargas_pagina'))
    ruta, nombre = res
    return send_file(ruta, as_attachment=True, download_name=nombre)


@bp.route('/api/descargas/version')
def descargas_version():
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    return jsonify({'ok': True, 'actual': up.version_actual(),
                    'disponible': up.version_remota()})


@bp.route('/api/descargas/actualizar', methods=['POST'])
def descargas_actualizar():
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    up.actualizar()
    return jsonify({'ok': True})


@bp.route('/api/descargas/update-estado')
def descargas_update_estado():
    if not _super():
        return jsonify({'error': 'Sin permiso'}), 403
    return jsonify({'ok': True, **up.estado()})
