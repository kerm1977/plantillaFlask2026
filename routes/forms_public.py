import os
import json
import uuid
from urllib.parse import quote
from flask import request, jsonify, render_template
from werkzeug.utils import secure_filename
from models import Form, FormField, FormResponse, FormAnswer, Hiker
from db import db
from routes import bp, _PROJECT_ROOT

FORM_UPLOADS = os.path.join(_PROJECT_ROOT, 'static', 'uploads', 'forms')


# ── VISTAS PÚBLICAS ──────────────────────────────────────────────────────────

@bp.route('/form/<path:slug>/editar/<token>')
def public_form_edit(slug, token):
    resp = FormResponse.query.filter_by(edit_token=token).first_or_404()
    form = Form.query.get_or_404(resp.form_id)
    if form.form_type == 'examen' or not form.allow_edit:
        return render_template('form_closed.html', form=form)
    return render_template('form_public.html', form=form, edit_token=token, edit_response_id=resp.id)


@bp.route('/form/<path:slug>')
def public_form(slug):
    form = Form.query.get_or_404(int(slug)) if slug.isdigit() else \
           Form.query.filter_by(slug=slug).first_or_404()
    if not form.is_active:
        return render_template('form_closed.html', form=form)
    return render_template('form_public.html', form=form)


# ── ENVIAR RESPUESTA ─────────────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/submit', methods=['POST'])
def api_submit_form(form_id):
    form = Form.query.get_or_404(form_id)
    if not form.is_active:
        return jsonify({'error': 'Este formulario está cerrado'}), 403
    data         = request.get_json() or {}
    answers_data = data.get('answers', {})
    edit_token   = uuid.uuid4().hex
    cedula_valor = data.get('cedula', '').strip()
    nombre_valor = data.get('nombre_completo', '').strip()
    response = FormResponse(
        form_id=form_id, edit_token=edit_token,
        nombre_completo=nombre_valor,
        cedula=cedula_valor or None,
        email=data.get('email', ''),
        telefono=data.get('telefono', ''),
        edad=int(data.get('edad')) if data.get('edad') else None,
        tipo_sangre=data.get('tipo_sangre', '') or None,
        alergias=data.get('alergias', '') or None,
        enfermedades_cronicas=data.get('enfermedades_cronicas', '') or None,
        contacto_emergencia_nombre=data.get('contacto_emergencia_nombre', '') or None,
        contacto_emergencia_telefono=data.get('contacto_emergencia_telefono', '') or None,
        pasaporte=data.get('pasaporte', '') or None,
        fecha_nacimiento_dia=int(data.get('fecha_nacimiento_dia')) if data.get('fecha_nacimiento_dia') else None,
        fecha_nacimiento_mes=int(data.get('fecha_nacimiento_mes')) if data.get('fecha_nacimiento_mes') else None,
        fecha_nacimiento_anio=int(data.get('fecha_nacimiento_anio')) if data.get('fecha_nacimiento_anio') else None,
    )
    # Guardar/actualizar en agenda Hiker si hay cédula y nombre
    if cedula_valor and nombre_valor:
        hiker = Hiker.query.filter_by(cedula=cedula_valor).first()
        # Convertir fecha de nacimiento a formato Date
        fecha_nacimiento = None
        if data.get('fecha_nacimiento_dia') and data.get('fecha_nacimiento_mes') and data.get('fecha_nacimiento_anio'):
            from datetime import date
            try:
                fecha_nacimiento = date(
                    int(data.get('fecha_nacimiento_anio')),
                    int(data.get('fecha_nacimiento_mes')),
                    int(data.get('fecha_nacimiento_dia'))
                )
            except ValueError:
                pass
        
        if not hiker:
            hiker = Hiker(
                cedula=cedula_valor,
                nombre_completo=nombre_valor,
                telefono=data.get('telefono', '') or None,
                pasaporte=data.get('pasaporte', '') or None,
                tipo_sangre=data.get('tipo_sangre', '') or None,
                fecha_nacimiento=fecha_nacimiento,
                alergias=data.get('alergias', '') or None,
                enfermedades_cronicas=data.get('enfermedades_cronicas', '') or None,
                contacto_emergencia_nombre=data.get('contacto_emergencia_nombre', '') or None,
                contacto_emergencia_telefono=data.get('contacto_emergencia_telefono', '') or None
            )
            db.session.add(hiker)
        else:
            # Actualizar campos si están vacíos
            if data.get('telefono') and not hiker.telefono:
                hiker.telefono = data.get('telefono')
            if data.get('pasaporte') and not hiker.pasaporte:
                hiker.pasaporte = data.get('pasaporte')
            if data.get('tipo_sangre') and not hiker.tipo_sangre:
                hiker.tipo_sangre = data.get('tipo_sangre')
            if fecha_nacimiento and not hiker.fecha_nacimiento:
                hiker.fecha_nacimiento = fecha_nacimiento
            if data.get('alergias') and not hiker.alergias:
                hiker.alergias = data.get('alergias')
            if data.get('enfermedades_cronicas') and not hiker.enfermedades_cronicas:
                hiker.enfermedades_cronicas = data.get('enfermedades_cronicas')
            if data.get('contacto_emergencia_nombre') and not hiker.contacto_emergencia_nombre:
                hiker.contacto_emergencia_nombre = data.get('contacto_emergencia_nombre')
            if data.get('contacto_emergencia_telefono') and not hiker.contacto_emergencia_telefono:
                hiker.contacto_emergencia_telefono = data.get('contacto_emergencia_telefono')
    score = total_graded = 0
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        answer = FormAnswer(
            field_id=field.id,
            value=json.dumps(answer_value, ensure_ascii=False)
                  if isinstance(answer_value, list) else str(answer_value)
        )
        response.answers.append(answer)
        if form.form_type == 'examen' and field.correct_answer:
            total_graded += 1
            if field.field_type == 'checkbox':
                correct = sorted(json.loads(field.correct_answer)) if field.correct_answer else []
                given   = sorted(answer_value) if isinstance(answer_value, list) else []
                if correct == given:
                    score += 1
            elif str(answer_value).strip().lower() == field.correct_answer.strip().lower():
                score += 1
    if form.form_type == 'examen' and total_graded > 0:
        response.score           = round((score / total_graded) * 100, 1)
        response.total_questions = total_graded
    db.session.add(response)
    db.session.commit()

    # Resumen de respuestas
    summary_lines = []
    for field in fields:
        v = answers_data.get(str(field.id), '')
        display = ', '.join(v) if isinstance(v, list) else str(v)
        if display:
            summary_lines.append(f"• {field.label}: {display}")
    summary_text = '\n'.join(summary_lines)
    nombre   = data.get('nombre_completo', '')
    edit_url = f"{request.host_url}form/{form.slug or form.id}/editar/{response.edit_token}"

    result = {'ok': True, 'response_id': response.id, 'edit_token': response.edit_token,
               'answers_summary': summary_text, 'nombre': nombre}
    if form.form_type == 'examen':
        result.update({'score': response.score, 'correct': score, 'total': total_graded})

    # WhatsApp auto-send
    telefono = data.get('telefono', '').strip().replace(' ', '').replace('-', '')
    if telefono and telefono[0] in ('6', '7', '8'):
        msg = f"📋 *{form.name}*\n\nHola *{nombre or 'participante'}*, este mensaje es para ti.\n"
        msg += f"El sistema ya registró tu selección:\n\n{summary_text}\n\n"
        if form.form_type == 'examen':
            msg += f"📊 Calificación: {score}/{total_graded} ({response.score}%)\n\n"
        if form.allow_edit and form.form_type != 'examen':
            msg += f"✏️ Si deseas cambiar tu selección, usa este enlace:\n{edit_url}\n\n"
        msg += "✅ Gracias por completar el formulario."
        if not telefono.startswith('+'):
            telefono = '506' + telefono
        result['whatsapp_url'] = f"https://wa.me/{telefono}?text={quote(msg)}"

    admin_msg = f"📋 *{form.name}*\nRespuesta de: *{nombre or 'Anónimo'}*\n\n{summary_text}\n"
    if form.form_type == 'examen' and response.score is not None:
        admin_msg += f"\n📊 Nota: {response.score}%\n"
    result['admin_msg'] = quote(admin_msg)
    return jsonify(result)


# ── SUBIR ARCHIVO ────────────────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/submit_file', methods=['POST'])
def api_submit_file(form_id):
    form = Form.query.get_or_404(form_id)
    if not form.is_active:
        return jsonify({'error': 'Formulario cerrado'}), 403
    file     = request.files.get('file')
    field_id = request.form.get('field_id')
    if not file or not field_id:
        return jsonify({'error': 'Datos incompletos'}), 400
    os.makedirs(FORM_UPLOADS, exist_ok=True)
    filename = secure_filename(f"f{form_id}_{field_id}_{file.filename}")
    file.save(os.path.join(FORM_UPLOADS, filename))
    return jsonify({'ok': True, 'path': f"uploads/forms/{filename}"})


# ── BUSCAR HIKERS (AUTOCOMPLETE EN FORMULARIOS) ──────────────────────────────

@bp.route('/api/forms/search_hikers')
def api_search_hikers():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    hikers = (Hiker.query.filter(Hiker.cedula.contains(q)).limit(10).all()
              if q.isdigit() else
              Hiker.query.filter(Hiker.nombre_completo.ilike(f'%{q}%')).limit(10).all())
    return jsonify([{'cedula': h.cedula, 'nombre_completo': h.nombre_completo,
                     'telefono': h.telefono or '', 'email': ''} for h in hikers])
