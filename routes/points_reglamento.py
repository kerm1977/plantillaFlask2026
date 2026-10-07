# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_reglamento.py - Reglamento de puntos: compartir (WhatsApp/TXT/PDF) y edición (superusuario)
from flask import Response, jsonify, redirect, request, session, url_for
from modules import reglamento as rg, reglamento_export as ex
from routes import bp


@bp.app_context_processor
def _inject_reglamento():
    return {'reglamento_html': rg.obtener_html}


@bp.route('/reglamento-puntos.txt')
def reglamento_txt():
    return Response(ex.a_texto(rg.bloques()), mimetype='text/plain; charset=utf-8',
                    headers={'Content-Disposition': 'attachment; filename=reglamento_puntos_la_tribu.txt'})


@bp.route('/reglamento-puntos.pdf')
def reglamento_pdf():
    return Response(ex.a_pdf(rg.bloques()), mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment; filename=reglamento_puntos_la_tribu.pdf'})


@bp.route('/reglamento-puntos/whatsapp')
def reglamento_whatsapp():
    return redirect(ex.url_whatsapp(rg.bloques(), url_for('main.reglamento_pdf', _external=True),
                                    url_for('main.mis_puntos', _external=True)))


@bp.route('/admin/reglamento', methods=['POST'])
def reglamento_guardar():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    return jsonify(rg.guardar_html(data.get('html') or ''))
