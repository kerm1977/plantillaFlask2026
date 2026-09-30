# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
import json
from flask import request, jsonify, session
from models import Form, FormField, FormResponse
from models_forms import ReservationConfig
from db import db
from routes import bp
from routes.forms_responses_utils import _build_answers_map, _update_response_answers


@bp.route('/api/events/options')
def api_events_options():
    """Lista ligera de eventos para el selector de Single Page Offline."""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    from models import Event
    eventos = Event.query.order_by(Event.id.desc()).all()
    return jsonify([{'id': e.id, 'nombre_lugar': e.nombre_lugar or '',
                     'fecha': e.fecha_unica or e.fecha_inicio or '',
                     'actividad': e.actividad or ''} for e in eventos])


# ── CONFIGURACIÓN DE NÚMEROS DE RESERVA ─────────────────────────────────────

@bp.route('/api/reservation-config', methods=['GET'])
def api_get_reservation_config():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    config = ReservationConfig.query.first()
    if not config:
        config = ReservationConfig(reservation_numbers='')
        db.session.add(config)
        db.session.commit()
    return jsonify({'reservation_numbers': config.reservation_numbers or ''})

@bp.route('/api/reservation-config', methods=['POST'])
def api_save_reservation_config():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    reservation_numbers = data.get('reservation_numbers', '')

    config = ReservationConfig.query.first()
    if not config:
        config = ReservationConfig(reservation_numbers=reservation_numbers)
        db.session.add(config)
    else:
        config.reservation_numbers = reservation_numbers

    db.session.commit()
    return jsonify({'success': True, 'reservation_numbers': config.reservation_numbers})


@bp.route('/api/responses/<int:response_id>/reservation-number', methods=['POST'])
def api_assign_reservation_number(response_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    reservation_number = data.get('reservation_number', '')

    response = FormResponse.query.get_or_404(response_id)
    response.reservation_number = reservation_number
    db.session.commit()

    return jsonify({'success': True, 'reservation_number': response.reservation_number})


# ── LISTAR RESPUESTAS ────────────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/responses')
def api_get_responses(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form      = Form.query.get_or_404(form_id)
    fields    = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(
                FormResponse.submitted_at.desc()).all()
    output = []
    for r in responses:
        row = {'id': r.id, 'nombre_completo': r.nombre_completo, 'cedula': r.cedula or '',
               'email': r.email, 'telefono': r.telefono, 'edad': r.edad,
               'tipo_sangre': r.tipo_sangre or '', 'alergias': r.alergias or '',
               'enfermedades_cronicas': r.enfermedades_cronicas or '',
               'contacto_emergencia_nombre': r.contacto_emergencia_nombre or '',
               'contacto_emergencia_telefono': r.contacto_emergencia_telefono or '',
               'pasaporte': r.pasaporte or '',
               'fecha_nacimiento_dia': r.fecha_nacimiento_dia,
               'fecha_nacimiento_mes': r.fecha_nacimiento_mes,
               'fecha_nacimiento_anio': r.fecha_nacimiento_anio,
               'reservation_number': r.reservation_number or '',
               'submitted_at': r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '',
               'score': r.score, 'total_questions': r.total_questions,
               'answers': _build_answers_map(r, fields)}
        output.append(row)
    fields_info = [{'id': f.id, 'label': f.label, 'field_type': f.field_type,
                    'options': json.loads(f.options) if f.options else []} for f in fields]
    return jsonify({'fields': fields_info, 'responses': output,
                    'form_name': form.name,
                    'show_cedula': form.show_cedula, 'show_ficha_medica': form.show_ficha_medica,
                    'show_pasaporte': form.show_pasaporte, 'show_fecha_nacimiento': form.show_fecha_nacimiento})


# ── ELIMINAR RESPUESTA ───────────────────────────────────────────────────────

@bp.route('/api/forms/responses/<int:response_id>', methods=['DELETE'])
def api_delete_response(response_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    resp = FormResponse.query.get_or_404(response_id)
    db.session.delete(resp)
    db.session.commit()
    return jsonify({'ok': True})


# ── EDITAR RESPUESTA (público con allow_edit) ────────────────────────────────

@bp.route('/api/forms/<int:form_id>/response/<int:response_id>', methods=['PUT'])
def api_update_response(form_id, response_id):
    form = Form.query.get_or_404(form_id)
    if form.form_type == 'examen':
        return jsonify({'error': 'No se puede editar un examen enviado'}), 403
    if not form.allow_edit:
        return jsonify({'error': 'Este formulario no permite editar respuestas'}), 403
    resp = FormResponse.query.get_or_404(response_id)
    if resp.form_id != form_id:
        return jsonify({'error': 'Respuesta no pertenece a este formulario'}), 400
    data         = request.get_json() or {}
    answers_data = data.get('answers', {})
    resp.nombre_completo = data.get('nombre_completo', resp.nombre_completo)
    resp.email           = data.get('email', resp.email)
    resp.telefono        = data.get('telefono', resp.telefono)
    resp.edad            = int(data.get('edad')) if data.get('edad') else resp.edad
    resp.tipo_sangre                  = data.get('tipo_sangre', resp.tipo_sangre)
    resp.alergias                     = data.get('alergias', resp.alergias)
    resp.enfermedades_cronicas        = data.get('enfermedades_cronicas', resp.enfermedades_cronicas)
    resp.contacto_emergencia_nombre   = data.get('contacto_emergencia_nombre', resp.contacto_emergencia_nombre)
    resp.contacto_emergencia_telefono = data.get('contacto_emergencia_telefono', resp.contacto_emergencia_telefono)
    resp.pasaporte                    = data.get('pasaporte', resp.pasaporte)
    resp.fecha_nacimiento_dia         = int(data.get('fecha_nacimiento_dia')) if data.get('fecha_nacimiento_dia') else resp.fecha_nacimiento_dia
    resp.fecha_nacimiento_mes         = int(data.get('fecha_nacimiento_mes')) if data.get('fecha_nacimiento_mes') else resp.fecha_nacimiento_mes
    resp.fecha_nacimiento_anio        = int(data.get('fecha_nacimiento_anio')) if data.get('fecha_nacimiento_anio') else resp.fecha_nacimiento_anio
    _update_response_answers(resp, answers_data, form_id)
    db.session.commit()
    return jsonify({'ok': True})


# ── BUSCAR RESPUESTA PROPIA ──────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/my_response')
def api_get_my_response(form_id):
    nombre = request.args.get('nombre', '').strip()
    if not nombre:
        return jsonify({'found': False})
    resp = FormResponse.query.filter_by(form_id=form_id, nombre_completo=nombre).first()
    if not resp:
        return jsonify({'found': False})
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    return jsonify({'found': True, 'response_id': resp.id,
                    'nombre_completo': resp.nombre_completo, 'cedula': resp.cedula or '',
                    'email': resp.email or '', 'telefono': resp.telefono or '',
                    'edad': resp.edad,
                    'tipo_sangre': resp.tipo_sangre or '', 'alergias': resp.alergias or '',
                    'enfermedades_cronicas': resp.enfermedades_cronicas or '',
                    'contacto_emergencia_nombre': resp.contacto_emergencia_nombre or '',
                    'contacto_emergencia_telefono': resp.contacto_emergencia_telefono or '',
                    'pasaporte': resp.pasaporte or '',
                    'fecha_nacimiento_dia': resp.fecha_nacimiento_dia,
                    'fecha_nacimiento_mes': resp.fecha_nacimiento_mes,
                    'fecha_nacimiento_anio': resp.fecha_nacimiento_anio,
                    'submitted_at': resp.submitted_at.strftime('%d/%m/%Y %H:%M') if resp.submitted_at else '',
                    'answers': _build_answers_map(resp, fields)})


# ── EDITAR RESPUESTA (superusuario) ─────────────────────────────────────────

@bp.route('/api/forms/admin/responses/<int:response_id>', methods=['PUT'])
def api_admin_update_response(response_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    resp         = FormResponse.query.get_or_404(response_id)
    data         = request.get_json() or {}
    answers_data = data.get('answers', {})
    resp.nombre_completo = data.get('nombre_completo', resp.nombre_completo)
    resp.cedula          = data.get('cedula', resp.cedula)
    resp.email           = data.get('email', resp.email)
    resp.telefono        = data.get('telefono', resp.telefono)
    if data.get('edad'):
        resp.edad = int(data['edad'])
    resp.tipo_sangre                  = data.get('tipo_sangre', resp.tipo_sangre)
    resp.alergias                     = data.get('alergias', resp.alergias)
    resp.enfermedades_cronicas        = data.get('enfermedades_cronicas', resp.enfermedades_cronicas)
    resp.contacto_emergencia_nombre   = data.get('contacto_emergencia_nombre', resp.contacto_emergencia_nombre)
    resp.contacto_emergencia_telefono = data.get('contacto_emergencia_telefono', resp.contacto_emergencia_telefono)
    resp.pasaporte                    = data.get('pasaporte', resp.pasaporte)
    resp.fecha_nacimiento_dia         = int(data.get('fecha_nacimiento_dia')) if data.get('fecha_nacimiento_dia') else resp.fecha_nacimiento_dia
    resp.fecha_nacimiento_mes         = int(data.get('fecha_nacimiento_mes')) if data.get('fecha_nacimiento_mes') else resp.fecha_nacimiento_mes
    resp.fecha_nacimiento_anio        = int(data.get('fecha_nacimiento_anio')) if data.get('fecha_nacimiento_anio') else resp.fecha_nacimiento_anio
    # Campos de cotizador
    resp.cotizador_lugar              = data.get('cotizador_lugar', resp.cotizador_lugar)
    resp.cotizador_maps_ida           = data.get('cotizador_maps_ida', resp.cotizador_maps_ida)
    resp.cotizador_maps_regreso       = data.get('cotizador_maps_regreso', resp.cotizador_maps_regreso)
    resp.cotizador_fecha              = data.get('cotizador_fecha', resp.cotizador_fecha)
    resp.cotizador_hora_salida        = data.get('cotizador_hora_salida', resp.cotizador_hora_salida)
    resp.cotizador_moneda             = data.get('cotizador_moneda', resp.cotizador_moneda) or 'colones'
    resp.cotizador_precio             = float(data.get('cotizador_precio')) if data.get('cotizador_precio') else resp.cotizador_precio
    resp.cotizador_precios_json  = json.dumps(data.get('cotizador_precios', {})) if data.get('cotizador_precios') else resp.cotizador_precios_json
    _update_response_answers(resp, answers_data, resp.form_id)
    db.session.commit()
    return jsonify({'ok': True})


# ── OBTENER RESPUESTA POR TOKEN ──────────────────────────────────────────────

@bp.route('/api/forms/response_by_token/<token>')
def api_get_response_by_token(token):
    resp = FormResponse.query.filter_by(edit_token=token).first()
    if not resp:
        return jsonify({'found': False})
    fields = FormField.query.filter_by(form_id=resp.form_id).order_by(FormField.order).all()
    return jsonify({'found': True, 'response_id': resp.id,
                    'nombre_completo': resp.nombre_completo, 'cedula': resp.cedula or '',
                    'email': resp.email or '', 'telefono': resp.telefono or '',
                    'edad': resp.edad,
                    'tipo_sangre': resp.tipo_sangre or '', 'alergias': resp.alergias or '',
                    'enfermedades_cronicas': resp.enfermedades_cronicas or '',
                    'contacto_emergencia_nombre': resp.contacto_emergencia_nombre or '',
                    'contacto_emergencia_telefono': resp.contacto_emergencia_telefono or '',
                    'pasaporte': resp.pasaporte or '',
                    'fecha_nacimiento_dia': resp.fecha_nacimiento_dia,
                    'fecha_nacimiento_mes': resp.fecha_nacimiento_mes,
                    'fecha_nacimiento_anio': resp.fecha_nacimiento_anio,
                    'answers': _build_answers_map(resp, fields)})
