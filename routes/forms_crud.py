import re
import json
from flask import request, jsonify, session, render_template, redirect, url_for
from models import Form, FormField, FormResponse
from models_forms import ReservationConfig
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
    )
    db.session.add(form)
    db.session.commit()
    return jsonify({'ok': True, 'id': form.id, 'slug': form.slug})


@bp.route('/api/forms/<int:form_id>', methods=['GET'])
def api_get_form(form_id):
    form = Form.query.get_or_404(form_id)
    fields = [{'id': f.id, 'field_type': f.field_type, 'label': f.label,
                'options': json.loads(f.options) if f.options else [],
                'order': f.order, 'correct_answer': f.correct_answer}
               for f in form.fields]
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
        'fields': fields, 'responses_count': len(form.responses)
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
