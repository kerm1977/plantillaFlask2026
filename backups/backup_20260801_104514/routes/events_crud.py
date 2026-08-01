import os
from flask import request, jsonify, session
from models import Event
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS


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

        new_event = Event(
            poster=filename,
            nombre_lugar=request.form.get('nombreLugar'),
            dificultad=request.form.get('dificultad'),
            actividad=request.form.get('actividad'),
            moneda=request.form.get('moneda'),
            precio=int(request.form.get('precio', 0) if request.form.get('precio') else 0),
            reserva=int(request.form.get('reserva', 0) if request.form.get('reserva') else 0),
            capacidad=request.form.get('capacidad'),
            sinpe=request.form.get('sinpe'),
            cuenta=request.form.get('cuenta'),
            solo_chat=request.form.get('solo_chat') == 'true',
            logistica_segura=request.form.get('logistica_segura') == 'true',
            dias=int(request.form.get('dias', 1) if request.form.get('dias') else 1),
            fecha_unica=request.form.get('fechaUnica'),
            fecha_inicio=request.form.get('fechaInicio'),
            fecha_regreso=request.form.get('fechaRegreso'),
            hora_salida=request.form.get('horaSalida'),
            lugar_salida=destino_db,
            puntos_recogida=request.form.get('puntosRecogida'),
            itinerario=request.form.get('itinerario'),
            incluye=request.form.get('incluye')
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
        evento.actividad = request.form.get('actividad', evento.actividad)
        evento.moneda = request.form.get('moneda', evento.moneda)
        evento.precio = int(request.form.get('precio', evento.precio) if request.form.get('precio') else 0)
        evento.reserva = int(request.form.get('reserva', evento.reserva) if request.form.get('reserva') else 0)
        evento.capacidad = request.form.get('capacidad', evento.capacidad)
        evento.sinpe = request.form.get('sinpe', evento.sinpe)
        evento.cuenta = request.form.get('cuenta', evento.cuenta)
        
        # Leemos los booleanos reales del form
        evento.solo_chat = request.form.get('solo_chat') == 'true'
        evento.logistica_segura = request.form.get('logistica_segura') == 'true'
        
        evento.dias = int(request.form.get('dias', evento.dias) if request.form.get('dias') else 1)
        evento.fecha_unica = request.form.get('fechaUnica', evento.fecha_unica)
        evento.fecha_inicio = request.form.get('fechaInicio', evento.fecha_inicio)
        evento.fecha_regreso = request.form.get('fechaRegreso', evento.fecha_regreso)
        evento.hora_salida = request.form.get('horaSalida', evento.hora_salida)
        evento.lugar_salida = destino_db if destino_db else evento.lugar_salida
        evento.puntos_recogida = request.form.get('puntosRecogida', evento.puntos_recogida)
        evento.itinerario = request.form.get('itinerario', evento.itinerario)
        evento.incluye = request.form.get('incluye', evento.incluye)

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
