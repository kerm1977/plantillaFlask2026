import re
import json
from flask import request, jsonify, session, render_template, redirect, url_for
from models import Form, FormField, FormResponse
from models_forms import ReservationConfig, CotizadorLugar
from db import db
from routes import bp


def _slugify(text):
    text = text.lower().strip()
    for src, dst in [('[áàäâ]','a'),('[éèëê]','e'),('[íìïî]','i'),('[óòöô]','o'),('[úùüû]','u'),('[ñ]','n')]:
        text = re.sub(src, dst, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


def _unique_slug(name, exclude_id=None):
    slug = base = _slugify(name)
    counter = 1
    query = Form.query.filter_by(slug=slug)
    if exclude_id:
        query = query.filter(Form.id != exclude_id)
    while query.first():
        slug = f"{base}-{counter}"
        counter += 1
        query = Form.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(Form.id != exclude_id)
    return slug


# ── VISTA ADMIN ──────────────────────────────────────────────────────────────

@bp.route('/formularios')
def formularios():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('formularios.html')


# ── API CRUD FORMULARIOS ─────────────────────────────────────────────────────

@bp.route('/api/forms', methods=['GET'])
def api_list_forms():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    forms = Form.query.order_by(Form.created_at.desc()).all()
    return jsonify([{
        'id': f.id, 'name': f.name, 'slug': f.slug, 'form_type': f.form_type,
        'is_active': f.is_active, 'allow_edit': f.allow_edit,
        'show_nombre': f.show_nombre, 'show_cedula': f.show_cedula,
        'show_fecha': f.show_fecha, 'show_email': f.show_email,
        'show_edad': f.show_edad, 'show_telefono': f.show_telefono,
        'show_ficha_medica': f.show_ficha_medica,
        'created_at': f.created_at.strftime('%d/%m/%Y %H:%M') if f.created_at else '',
        'fields_count': len(f.fields), 'responses_count': len(f.responses),
        'reservation_numbers': (f.reservation_numbers or '').strip()
    } for f in forms])


@bp.route('/api/forms', methods=['POST'])
def api_create_form():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    # Escribir logs a archivo para debug
    with open('debug_backend.log', 'a') as f:
        f.write(f'[DEBUG BACKEND] Payload recibido completo: {data}\n')
        f.write(f'[DEBUG BACKEND] Keys en payload: {list(data.keys())}\n')
    print(f'[DEBUG BACKEND] Payload recibido completo: {data}')
    print(f'[DEBUG BACKEND] Keys en payload: {list(data.keys())}')
    name = data.get('name', 'Formulario sin título')
    form = Form(
        name=name, slug=_unique_slug(name),
        form_type=data.get('form_type', 'registro'),
        allow_edit=data.get('allow_edit', False),
        has_reservation_numbers=data.get('has_reservation_numbers', False),
        reservation_numbers=data.get('reservation_numbers', ''),
        show_nombre=data.get('show_nombre', True),
        show_cedula=data.get('show_cedula', False),
        show_fecha=data.get('show_fecha', False),
        show_email=data.get('show_email', False),
        show_edad=data.get('show_edad', False),
        show_telefono=data.get('show_telefono', False),
        show_ficha_medica=data.get('show_ficha_medica', False),
        show_pasaporte=data.get('show_pasaporte', False),
        show_fecha_nacimiento=data.get('show_fecha_nacimiento', False),
    )
    db.session.add(form)
    db.session.commit()
    
    # Guardar lugares del cotizador
    lugares_data = data.get('cotizador_lugares', [])
    with open('debug_backend.log', 'a') as f:
        f.write(f'[DEBUG BACKEND] Lugares recibidos: {lugares_data}\n')
        f.write(f'[DEBUG BACKEND] Cantidad de lugares: {len(lugares_data)}\n')
    print(f'[DEBUG BACKEND] Lugares recibidos: {lugares_data}')
    print(f'[DEBUG BACKEND] Cantidad de lugares: {len(lugares_data)}')
    for lugar_data in lugares_data:
        with open('debug_backend.log', 'a') as f:
            f.write(f'[DEBUG BACKEND] Lugar individual: {lugar_data}\n')
        print(f'[DEBUG BACKEND] Lugar individual: {lugar_data}')
        # Solo guardar si tiene nombre (obligatorio)
        if lugar_data.get('nombre'):
            lugar = CotizadorLugar(
                form_id=form.id,
                nombre=lugar_data.get('nombre', ''),
                maps_ida=lugar_data.get('maps_ida', ''),
                maps_regreso=lugar_data.get('maps_regreso', ''),
                fecha=lugar_data.get('fecha', ''),
                hora_salida=lugar_data.get('hora_salida', ''),
                moneda=lugar_data.get('moneda', 'colones'),
                order=lugar_data.get('order', 0)
            )
            db.session.add(lugar)
            with open('debug_backend.log', 'a') as f:
                f.write(f'[DEBUG BACKEND] Lugar agregado a session: {lugar.nombre}\n')
            print(f'[DEBUG BACKEND] Lugar agregado a session: {lugar.nombre}')
        else:
            with open('debug_backend.log', 'a') as f:
                f.write(f'[DEBUG BACKEND] Lugar sin nombre, no se guarda: {lugar_data}\n')
            print(f'[DEBUG BACKEND] Lugar sin nombre, no se guarda: {lugar_data}')
    db.session.commit()
    with open('debug_backend.log', 'a') as f:
        f.write(f'[DEBUG BACKEND] Commit realizado para formulario {form.id}\n')
    print(f'[DEBUG BACKEND] Commit realizado para formulario {form.id}')
    
    return jsonify({'ok': True, 'id': form.id, 'slug': form.slug})


@bp.route('/api/forms/<int:form_id>', methods=['GET'])
def api_get_form(form_id):
    form = Form.query.get_or_404(form_id)
    fields = [{'id': f.id, 'field_type': f.field_type, 'label': f.label,
                'options': json.loads(f.options) if f.options else [],
                'order': f.order, 'correct_answer': f.correct_answer}
               for f in form.fields]
    cotizador_lugares = [{'id': l.id, 'nombre': l.nombre, 'maps_ida': l.maps_ida,
                          'maps_regreso': l.maps_regreso, 'fecha': l.fecha,
                          'hora_salida': l.hora_salida, 'moneda': l.moneda, 'order': l.order}
                         for l in form.cotizador_lugares.order_by(CotizadorLugar.order)]
    print(f'[DEBUG] Cargando formulario {form_id}, lugares encontrados: {len(cotizador_lugares)}')
    for l in cotizador_lugares:
        print(f'[DEBUG] Lugar cargado: {l["nombre"]}')
    return jsonify({
        'id': form.id, 'name': form.name, 'slug': form.slug,
        'form_type': form.form_type, 'is_active': form.is_active,
        'allow_edit': form.allow_edit, 'has_reservation_numbers': form.has_reservation_numbers,
        'reservation_numbers': form.reservation_numbers,
        'show_nombre': form.show_nombre,
        'show_cedula': form.show_cedula, 'show_fecha': form.show_fecha,
        'show_email': form.show_email, 'show_edad': form.show_edad,
        'show_telefono': form.show_telefono, 'show_ficha_medica': form.show_ficha_medica,
        'show_pasaporte': form.show_pasaporte, 'show_fecha_nacimiento': form.show_fecha_nacimiento,
        'created_at': form.created_at.strftime('%d/%m/%Y %H:%M') if form.created_at else '',
        'fields': fields, 'responses_count': len(form.responses),
        'cotizador_lugares': cotizador_lugares
    })


@bp.route('/api/forms/<int:form_id>', methods=['PUT'])
def api_update_form(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    data = request.get_json()
    new_name = data.get('name', form.name)
    if new_name != form.name:
        form.name = new_name
        form.slug = _unique_slug(new_name, exclude_id=form.id)
    form.form_type    = data.get('form_type', form.form_type)
    form.is_active    = data.get('is_active', form.is_active)
    form.allow_edit   = data.get('allow_edit', form.allow_edit)
    form.has_reservation_numbers = data.get('has_reservation_numbers', form.has_reservation_numbers)
    form.reservation_numbers = data.get('reservation_numbers', form.reservation_numbers)
    form.show_nombre  = data.get('show_nombre', form.show_nombre)
    form.show_cedula  = data.get('show_cedula', form.show_cedula)
    form.show_fecha   = data.get('show_fecha', form.show_fecha)
    form.show_email   = data.get('show_email', form.show_email)
    form.show_edad    = data.get('show_edad', form.show_edad)
    form.show_telefono= data.get('show_telefono', form.show_telefono)
    form.show_ficha_medica = data.get('show_ficha_medica', form.show_ficha_medica)
    form.show_pasaporte = data.get('show_pasaporte', form.show_pasaporte)
    form.show_fecha_nacimiento = data.get('show_fecha_nacimiento', form.show_fecha_nacimiento)
    
    # Actualizar lugares del cotizador
    CotizadorLugar.query.filter_by(form_id=form_id).delete()
    lugares_data = data.get('cotizador_lugares', [])
    print(f'[DEBUG] Actualizando {len(lugares_data)} lugares para formulario {form_id}')
    for lugar_data in lugares_data:
        # Solo guardar si tiene nombre (obligatorio)
        if lugar_data.get('nombre'):
            lugar = CotizadorLugar(
                form_id=form_id,
                nombre=lugar_data.get('nombre', ''),
                maps_ida=lugar_data.get('maps_ida', ''),
                maps_regreso=lugar_data.get('maps_regreso', ''),
                fecha=lugar_data.get('fecha', ''),
                hora_salida=lugar_data.get('hora_salida', ''),
                moneda=lugar_data.get('moneda', 'colones'),
                order=lugar_data.get('order', 0)
            )
            db.session.add(lugar)
            print(f'[DEBUG] Lugar actualizado: {lugar.nombre}')
    
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/forms/<int:form_id>', methods=['DELETE'])
def api_delete_form(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    db.session.delete(form)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/forms/<int:form_id>/fields', methods=['POST'])
def api_save_fields(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    Form.query.get_or_404(form_id)
    data = request.get_json()
    FormField.query.filter_by(form_id=form_id).delete()
    for i, fd in enumerate(data.get('fields', [])):
        db.session.add(FormField(
            form_id=form_id,
            field_type=fd.get('field_type', 'text'),
            label=fd.get('label', ''),
            options=json.dumps(fd.get('options', []), ensure_ascii=False),
            order=i,
            correct_answer=fd.get('correct_answer', '')
        ))
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/forms/<int:form_id>/reservation-numbers', methods=['GET'])
def api_get_form_reservation_numbers(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    return jsonify({'reservation_numbers': form.reservation_numbers or ''})


@bp.route('/api/forms/<int:form_id>/reservation-numbers', methods=['POST'])
def api_save_form_reservation_numbers(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    data = request.get_json()
    reservation_numbers = (data.get('reservation_numbers', '') or '').strip()
    form.reservation_numbers = reservation_numbers
    form.has_reservation_numbers = bool(reservation_numbers)
    db.session.commit()
    return jsonify({'success': True, 'reservation_numbers': reservation_numbers})
