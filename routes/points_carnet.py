# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_carnet.py - Descarga del carnet con QR (PNG/JPG/PDF).
# Autoriza al superusuario o a la persona que verifico su PIN en Mis puntos.
from flask import request, session, jsonify, send_file, url_for

from models import Hiker
from modules.carnet import build_carnet_image, carnet_bytes, ensure_card_email
from modules.points_engine import get_points_engine
from routes import bp


def _autorizado():
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return None, None, (jsonify({'ok': False, 'error': 'Falta la cedula'}), 400)
    if session.get('role') != 'Superusuario' and session.get('mis_puntos_ok') != cedula:
        return None, None, (jsonify({'ok': False, 'error': 'No autorizado'}), 403)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return None, None, (jsonify({'ok': False, 'error': 'Usuario no encontrado'}), 404)
    return cedula, hiker, None


@bp.route('/mis-puntos/carnet.<fmt>', methods=['GET'])
def mis_puntos_carnet(fmt):
    cedula, hiker, err = _autorizado()
    if err:
        return err
    if fmt not in ('png', 'jpg', 'pdf'):
        return jsonify({'ok': False, 'error': 'Formato no valido'}), 400
    email = ensure_card_email(hiker)
    tarjeta_url = url_for('main.tarjeta', cedula=cedula, email=email, _external=True)
    img = build_carnet_image(hiker, get_points_engine().total_by_cedula(cedula), tarjeta_url)
    buf, mime, ext = carnet_bytes(img, fmt)
    inline = request.args.get('inline') == '1'
    return send_file(buf, mimetype=mime, as_attachment=not inline,
                     download_name=f'carnet_{cedula}.{ext}')
