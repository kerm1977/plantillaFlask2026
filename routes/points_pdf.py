# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_pdf.py - Descarga del estado de cuenta en PDF (Mis puntos)
from flask import request, session, Response, jsonify
from models import Hiker
from modules.estado_cuenta_pdf import build_estado_cuenta_pdf
from modules.points_helpers import build_estado_cuenta_whatsapp
from routes import bp


def _hiker_autorizado():
    """Devuelve (cedula, hiker, error_response). Autoriza superusuario o persona verificada con su PIN."""
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return None, None, (jsonify({'ok': False, 'error': 'Falta la cedula'}), 400)
    if session.get('role') != 'Superusuario' and session.get('mis_puntos_ok') != cedula:
        return None, None, (jsonify({'ok': False, 'error': 'No autorizado'}), 403)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return None, None, (jsonify({'ok': False, 'error': 'Usuario no encontrado'}), 404)
    return cedula, hiker, None


@bp.route('/mis-puntos/estado-cuenta.pdf', methods=['GET'])
def estado_cuenta_pdf():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    return Response(build_estado_cuenta_pdf(cedula, hiker), mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.pdf'})


@bp.route('/mis-puntos/estado-cuenta-simple.txt', methods=['GET'])
def estado_cuenta_txt():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    text = build_estado_cuenta_whatsapp(cedula, hiker, plain=True)
    return Response(text, mimetype='text/plain; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.txt'})
