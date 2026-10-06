# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_pdf.py - Descarga del estado de cuenta en PDF (Mis puntos)
from flask import request, session, Response, jsonify
from models import Hiker
from modules.estado_cuenta_pdf import build_estado_cuenta_pdf
from routes import bp


@bp.route('/mis-puntos/estado-cuenta.pdf', methods=['GET'])
def estado_cuenta_pdf():
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    if session.get('role') != 'Superusuario' and session.get('mis_puntos_ok') != cedula:
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'error': 'Usuario no encontrado'}), 404
    pdf = build_estado_cuenta_pdf(cedula, hiker)
    return Response(pdf, mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.pdf'})
