# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
import os
from datetime import datetime, timedelta
from flask import request, jsonify, session
from models import Event
from models_core import EventDateChange
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS

@bp.route('/api/create_event', methods=['POST'])
def create_event():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403

    try:
        nombre = (request.form.get('nombreLugar') or '').strip()
        if not nombre:
            return jsonify({"error": "Falta el nombre del lugar"}), 400
        es_programado = request.form.get('visitado') == 'Programados'
        if es_programado:
            hoy_cr = (datetime.utcnow() - timedelta(hours=6)).date().isoformat()
            fecha_ev = request.form.get('fechaUnica') or request.form.get('fechaInicio') or ''
            if not fecha_ev:
                return jsonify({"error": "Falta la fecha de la actividad"}), 400
            if fecha_ev < hoy_cr:
                return jsonify({"error": "La fecha no puede ser anterior a hoy"}), 400
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
            nombre_lugar=nombre,
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
        # Si llegó una fecha con estado Pendiente, pasa a Programados
        # (misma regla que el selector rápido de fecha de la lista).
        if (new_event.visitado or '') in ('Pendiente', 'No', '') and (new_event.fecha_unica or new_event.fecha_inicio):
            new_event.visitado = 'Programados'
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
        if file and file.filename != '':  # noqa: E501
            if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400

            filename = secure_filename(f"event_{os.urandom(4).hex()}_{file.filename}")
            upload_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            evento.poster = filename
            evento.flyer_bg = None  # el póster nuevo manda en detalle y generador de flyer

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
        # Si el formulario envió una fecha con estado Pendiente, pasa a Programados
        if (evento.visitado or '') in ('Pendiente', 'No', '') and (request.form.get('fechaUnica') or request.form.get('fechaInicio')):
            evento.visitado = 'Programados'
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


@bp.route('/api/eventos/ocupados/<fecha>')
def eventos_en_fecha(fecha):
    """Lista los eventos que ocupan una fecha (solo superusuario)."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except (ValueError, TypeError):
        return jsonify({"error": "Fecha inválida"}), 400
    from sqlalchemy import or_, and_
    evs = Event.query.filter(or_(
        Event.fecha_unica == fecha,
        and_(Event.fecha_inicio <= fecha, Event.fecha_regreso >= fecha)
    )).all()
    return jsonify({"ok": True, "eventos": [
        {"id": e.id, "nombre": e.nombre_lugar} for e in evs]})