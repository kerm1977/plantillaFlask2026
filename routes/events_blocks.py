# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/events_blocks.py - Itinerario, bloques y métodos de pago de caminatas
import os
import hashlib
from flask import request, jsonify, session
from models import Event, CaminataBlock, PaymentMethod
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS

ALLOWED_CAMINATA_MEDIA_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | {'mp4','m4v','mov','wmv','avi','mkv','webm','mpv','mpg','mpeg','3gp','3g2'}


@bp.route('/api/caminatas-2027/<int:event_id>/upload-image', methods=['POST'])
def upload_caminata_2027_image(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    evento = Event.query.get_or_404(event_id)
    file = request.files.get('media')
    if not file or file.filename == '':
        return jsonify({"error": "No se envió archivo"}), 400
    if not allowed_file(file.filename, ALLOWED_CAMINATA_MEDIA_EXTENSIONS):
        return jsonify({"error": "Formato no permitido"}), 400

    try:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        kind = 'video' if ext in {'mp4','m4v','mov','wmv','avi','mkv','webm','mpv','mpg','mpeg'} else 'image'

        filename = secure_filename(f"caminata2027_{event_id}_{os.urandom(4).hex()}_{file.filename}")
        upload_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', 'caminatas_2027')
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))
        return jsonify({"ok": True, "url": f"/static/uploads/caminatas_2027/{filename}", "kind": kind})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno al subir: " + str(e)}), 500


@bp.route('/api/caminatas-2027/<int:event_id>/save-itinerario', methods=['POST'])
def save_caminata_2027_itinerario(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    evento = Event.query.get_or_404(event_id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "JSON no recibido"}), 400

    current_hash = hashlib.md5((evento.itinerario or '').encode('utf-8')).hexdigest()
    client_hash = data.get('hash')
    if client_hash != current_hash:
        return jsonify({"ok": False, "stale": True, "error": "El contenido cambió. Recargá la página."}), 409

    evento.itinerario = data.get('itinerario', evento.itinerario)
    db.session.commit()
    new_hash = hashlib.md5((evento.itinerario or '').encode('utf-8')).hexdigest()
    return jsonify({"ok": True, "hash": new_hash})


@bp.route('/api/caminatas-2027/blocks', methods=['POST'])
def create_caminata_block():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "JSON no recibido"}), 400

    block = CaminataBlock(
        page='caminatas_2027',
        order=data.get('order', 0),
        content=data.get('content', '')
    )
    db.session.add(block)
    db.session.commit()
    return jsonify({"ok": True, "id": block.id})


@bp.route('/api/caminatas-2027/blocks/<int:block_id>', methods=['PUT'])
def update_caminata_block(block_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    block = CaminataBlock.query.get_or_404(block_id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "JSON no recibido"}), 400

    block.content = data.get('content', block.content)
    db.session.commit()
    return jsonify({"ok": True})


@bp.route('/api/caminatas-2027/blocks/<int:block_id>', methods=['DELETE'])
def delete_caminata_block(block_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    block = CaminataBlock.query.get_or_404(block_id)
    db.session.delete(block)
    db.session.commit()
    return jsonify({"ok": True})


@bp.route('/api/caminatas-2027/blocks/upload-image', methods=['POST'])
def upload_caminata_block_image():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    file = request.files.get('image')
    if not file or file.filename == '':
        return jsonify({"error": "No se envió imagen"}), 400
    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Formato de imagen no permitido"}), 400

    filename = secure_filename(f"caminata2027_block_{os.urandom(4).hex()}_{file.filename}")
    upload_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', 'caminatas_2027')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return jsonify({"ok": True, "url": f"/static/uploads/caminatas_2027/{filename}"})


@bp.route('/api/payment_methods', methods=['GET'])
def get_payment_methods():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    metodos = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.orden, PaymentMethod.id).all()
    return jsonify({
        "sinpe": [{"id": m.id, "display": m.display()} for m in metodos if m.tipo == 'sinpe'],
        "cuenta": [{"id": m.id, "display": m.display()} for m in metodos if m.tipo == 'cuenta']
    })


@bp.route('/api/payment_methods', methods=['POST'])
def create_payment_method():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    data = request.get_json(silent=True) or request.form
    tipo = (data.get('tipo') or '').strip().lower()
    titular = (data.get('titular') or '').strip()
    numero = (data.get('numero') or '').strip()
    detalle = (data.get('detalle') or '').strip()
    if tipo not in ('sinpe', 'cuenta') or not titular or not numero:
        return jsonify({"error": "Datos incompletos"}), 400
    ultimo = PaymentMethod.query.filter_by(tipo=tipo).order_by(PaymentMethod.orden.desc()).first()
    orden = (ultimo.orden + 1) if ultimo else 1
    metodo = PaymentMethod(tipo=tipo, titular=titular, numero=numero, detalle=detalle, orden=orden)
    db.session.add(metodo)
    db.session.commit()
    from helpers.req_cache import invalidate
    invalidate('payment_methods')
    return jsonify({"ok": True, "id": metodo.id, "display": metodo.display(), "tipo": metodo.tipo})
