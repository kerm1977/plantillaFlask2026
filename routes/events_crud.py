import os
import hashlib
from flask import request, jsonify, session
from models import Event, CaminataBlock, PaymentMethod
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS

ALLOWED_CAMINATA_MEDIA_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | {'mp4','m4v','mov','wmv','avi','mkv','webm','mpv','mpg','mpeg','3gp','3g2'}


@bp.route('/api/create_event', methods=['POST'])
def create_event():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    
    try:
        file = request.files.get('poster')
        filename = "default_event.png"
        
        # Validación de seguridad: Extensión permitida
        if file and file.filename != '':
            if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
                
            filename = secure_filename(f"event_{os.urandom(4).hex()}_{file.filename}")
            upload_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))

        destino_db = request.form.get('destinoInternacional') if request.form.get('actividad') == 'Internacional' else request.form.get('lugarSalida')

        km_raw = request.form.get('kilometros', '').strip().replace(',', '.')
        try:
            kilometros = float(km_raw) if km_raw else None
        except ValueError:
            kilometros = None

        try:
            precio_buseta = int(request.form.get('precioBuseta')) if request.form.get('precioBuseta') else None
        except (ValueError, TypeError):
            precio_buseta = None

        new_event = Event(
            poster=filename,
            nombre_lugar=request.form.get('nombreLugar'),
            dificultad=request.form.get('dificultad'),
            tipo_terreno=request.form.get('tipoTerreno'),
            actividad=request.form.get('actividad'),
            moneda=request.form.get('moneda'),
            precio=int(request.form.get('precio', 0) if request.form.get('precio') else 0),
            precio_buseta=precio_buseta,
            kilometros=kilometros,
            reserva=int(request.form.get('reserva', 0) if request.form.get('reserva') else 0),
            tipo_caminata=request.form.get('tipoCaminata'),
            capacidad=request.form.get('capacidad'),
            sinpe=request.form.get('sinpe'),
            cuenta=request.form.get('cuenta'),
            solo_chat=request.form.get('solo_chat') == 'true',
            logistica_segura=request.form.get('logistica_segura') == 'true',
            zona_alto_riesgo=request.form.get('zona_alto_riesgo') == 'true',
            dias=int(request.form.get('dias', 1) if request.form.get('dias') else 1),
            fecha_unica=request.form.get('fechaUnica'),
            fecha_inicio=request.form.get('fechaInicio'),
            fecha_regreso=request.form.get('fechaRegreso'),
            hora_salida=request.form.get('horaSalida'),
            lugar_salida=destino_db,
            puntos_recogida=request.form.get('puntosRecogida'),
            itinerario=request.form.get('itinerario'),
            texto_referencia=request.form.get('textoReferencia'),
            incluye=request.form.get('incluye'),
            provincia=request.form.get('provincia'),
            visitado=(lambda e, a: a if e == 'Año' else e)(request.form.get('visitado', 'Pendiente'), request.form.get('anio', '2027')),
            enlace_extra=request.form.get('enlaceExtra'),
            puntos=int(request.form.get('puntos', 0) or 0)
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({"success": True, "event_id": new_event.id})
    except Exception as e:
        db.session.rollback()
        print(f"Error grave al guardar evento: {e}")
        return jsonify({"error": "Error interno del servidor al crear el evento"}), 500


@bp.route('/api/update_event/<int:event_id>', methods=['POST'])
def update_event(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    
    evento = Event.query.get_or_404(event_id)
    try:
        file = request.files.get('poster')
        if file and file.filename != '':
            if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
                
            filename = secure_filename(f"event_{os.urandom(4).hex()}_{file.filename}")
            upload_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            evento.poster = filename

        destino_db = request.form.get('destinoInternacional') if request.form.get('actividad') == 'Internacional' else request.form.get('lugarSalida')

        evento.nombre_lugar = request.form.get('nombreLugar', evento.nombre_lugar)
        evento.dificultad = request.form.get('dificultad', evento.dificultad)
        evento.tipo_terreno = request.form.get('tipoTerreno', evento.tipo_terreno)
        evento.tipo_caminata = request.form.get('tipoCaminata', evento.tipo_caminata)
        evento.actividad = request.form.get('actividad', evento.actividad)
        evento.moneda = request.form.get('moneda', evento.moneda)
        evento.precio = int(request.form.get('precio', evento.precio) if request.form.get('precio') else 0)
        try:
            evento.precio_buseta = int(request.form.get('precioBuseta')) if request.form.get('precioBuseta') else evento.precio_buseta
        except (ValueError, TypeError):
            evento.precio_buseta = evento.precio_buseta
        km_raw = request.form.get('kilometros', '').strip().replace(',', '.')
        try:
            evento.kilometros = float(km_raw) if km_raw else None
        except ValueError:
            evento.kilometros = evento.kilometros
        evento.reserva = int(request.form.get('reserva', evento.reserva) if request.form.get('reserva') else 0)
        evento.capacidad = request.form.get('capacidad', evento.capacidad)
        evento.sinpe = request.form.get('sinpe', evento.sinpe)
        evento.cuenta = request.form.get('cuenta', evento.cuenta)
        
        # Leemos los booleanos reales del form
        evento.solo_chat = request.form.get('solo_chat') == 'true'
        evento.logistica_segura = request.form.get('logistica_segura') == 'true'
        evento.zona_alto_riesgo = request.form.get('zona_alto_riesgo') == 'true'

        evento.dias = int(request.form.get('dias', evento.dias) if request.form.get('dias') else 1)
        evento.fecha_unica = request.form.get('fechaUnica', evento.fecha_unica)
        evento.fecha_inicio = request.form.get('fechaInicio', evento.fecha_inicio)
        evento.fecha_regreso = request.form.get('fechaRegreso', evento.fecha_regreso)
        evento.hora_salida = request.form.get('horaSalida', evento.hora_salida)
        evento.lugar_salida = destino_db if destino_db else evento.lugar_salida
        evento.puntos_recogida = request.form.get('puntosRecogida', evento.puntos_recogida)
        evento.itinerario = request.form.get('itinerario', evento.itinerario)
        evento.texto_referencia = request.form.get('textoReferencia', evento.texto_referencia)
        evento.incluye = request.form.get('incluye', evento.incluye)
        evento.provincia = request.form.get('provincia', evento.provincia)
        estado = request.form.get('visitado', evento.visitado)
        anio = request.form.get('anio', '2027')
        evento.visitado = anio if estado == 'Año' else estado
        evento.enlace_extra = request.form.get('enlaceExtra', evento.enlace_extra)
        try:
            evento.puntos = int(request.form.get('puntos', evento.puntos) if request.form.get('puntos') else 0)
        except (ValueError, TypeError):
            evento.puntos = evento.puntos or 0

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar evento: {e}")
        return jsonify({"error": "Error interno del servidor al actualizar"}), 500


@bp.route('/api/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    try:
        db.session.delete(evento)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar evento"}), 500


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
    return jsonify({"ok": True, "id": metodo.id, "display": metodo.display(), "tipo": metodo.tipo})
