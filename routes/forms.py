import os
import re
import json
import uuid
import openpyxl
from io import BytesIO
from urllib.parse import quote
from flask import request, jsonify, session, render_template, redirect, url_for, send_file, Response
from models import Form, FormField, FormResponse, FormAnswer, Hiker
from db import db
from datetime import datetime
from werkzeug.utils import secure_filename
from routes import bp, _PROJECT_ROOT


def _slugify(text):
    """Convierte texto a slug URL-friendly."""
    text = text.lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text

# ==========================================
# SISTEMA DE FORMULARIOS DINÁMICOS - CRUD
# ==========================================

FORM_UPLOADS = os.path.join(_PROJECT_ROOT, 'static', 'uploads', 'forms')


@bp.route('/formularios')
def formularios():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('formularios.html')


@bp.route('/api/forms', methods=['GET'])
def api_list_forms():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    forms = Form.query.order_by(Form.created_at.desc()).all()
    output = []
    for f in forms:
        output.append({
            'id': f.id,
            'name': f.name,
            'slug': f.slug,
            'form_type': f.form_type,
            'is_active': f.is_active,
            'allow_edit': f.allow_edit,
            'show_nombre': f.show_nombre,
            'show_fecha': f.show_fecha,
            'show_email': f.show_email,
            'show_edad': f.show_edad,
            'show_telefono': f.show_telefono,
            'created_at': f.created_at.strftime('%d/%m/%Y %H:%M') if f.created_at else '',
            'fields_count': len(f.fields),
            'responses_count': len(f.responses)
        })
    return jsonify(output)


@bp.route('/api/forms', methods=['POST'])
def api_create_form():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    name = data.get('name', 'Formulario sin título')
    slug = _slugify(name)
    # Asegurar slug único
    base_slug = slug
    counter = 1
    while Form.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    form = Form(
        name=name,
        slug=slug,
        form_type=data.get('form_type', 'registro'),
        allow_edit=data.get('allow_edit', False),
        show_nombre=data.get('show_nombre', True),
        show_fecha=data.get('show_fecha', False),
        show_email=data.get('show_email', False),
        show_edad=data.get('show_edad', False),
        show_telefono=data.get('show_telefono', False),
    )
    db.session.add(form)
    db.session.commit()
    return jsonify({'ok': True, 'id': form.id, 'slug': form.slug})


@bp.route('/api/forms/<int:form_id>', methods=['GET'])
def api_get_form(form_id):
    form = Form.query.get_or_404(form_id)
    fields = []
    for f in form.fields:
        fields.append({
            'id': f.id,
            'field_type': f.field_type,
            'label': f.label,
            'options': json.loads(f.options) if f.options else [],
            'order': f.order,
            'correct_answer': f.correct_answer
        })
    return jsonify({
        'id': form.id,
        'name': form.name,
        'slug': form.slug,
        'form_type': form.form_type,
        'is_active': form.is_active,
        'allow_edit': form.allow_edit,
        'show_nombre': form.show_nombre,
        'show_fecha': form.show_fecha,
        'show_email': form.show_email,
        'show_edad': form.show_edad,
        'show_telefono': form.show_telefono,
        'created_at': form.created_at.strftime('%d/%m/%Y %H:%M') if form.created_at else '',
        'fields': fields,
        'responses_count': len(form.responses)
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
        form.slug = _slugify(new_name)
        base_slug = form.slug
        counter = 1
        while Form.query.filter(Form.slug == form.slug, Form.id != form.id).first():
            form.slug = f"{base_slug}-{counter}"
            counter += 1
    form.form_type = data.get('form_type', form.form_type)
    form.is_active = data.get('is_active', form.is_active)
    form.allow_edit = data.get('allow_edit', form.allow_edit)
    form.show_nombre = data.get('show_nombre', form.show_nombre)
    form.show_fecha = data.get('show_fecha', form.show_fecha)
    form.show_email = data.get('show_email', form.show_email)
    form.show_edad = data.get('show_edad', form.show_edad)
    form.show_telefono = data.get('show_telefono', form.show_telefono)
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
    form = Form.query.get_or_404(form_id)
    data = request.get_json()
    fields_data = data.get('fields', [])
    # Eliminar campos anteriores y recrear
    FormField.query.filter_by(form_id=form_id).delete()
    for i, fd in enumerate(fields_data):
        field = FormField(
            form_id=form_id,
            field_type=fd.get('field_type', 'text'),
            label=fd.get('label', ''),
            options=json.dumps(fd.get('options', []), ensure_ascii=False),
            order=i,
            correct_answer=fd.get('correct_answer', '')
        )
        db.session.add(field)
    db.session.commit()
    return jsonify({'ok': True})


# ==========================================
# FORMULARIO PÚBLICO - RESPONDER
# ==========================================

@bp.route('/form/<path:slug>/editar/<token>')
def public_form_edit(slug, token):
    """Editar respuesta con token único."""
    # Buscar la respuesta por token
    resp = FormResponse.query.filter_by(edit_token=token).first_or_404()
    form = Form.query.get_or_404(resp.form_id)
    if form.form_type == 'examen':
        return render_template('form_closed.html', form=form)
    if not form.allow_edit:
        return render_template('form_closed.html', form=form)
    return render_template('form_public.html', form=form, edit_token=token, edit_response_id=resp.id)


@bp.route('/form/<path:slug>')
def public_form(slug):
    # Soportar tanto slug como ID numérico (fallback)
    if slug.isdigit():
        form = Form.query.get_or_404(int(slug))
    else:
        form = Form.query.filter_by(slug=slug).first_or_404()
    if not form.is_active:
        return render_template('form_closed.html', form=form)
    return render_template('form_public.html', form=form)


@bp.route('/api/forms/<int:form_id>/submit', methods=['POST'])
def api_submit_form(form_id):
    form = Form.query.get_or_404(form_id)
    if not form.is_active:
        return jsonify({'error': 'Este formulario está cerrado'}), 403

    data = request.get_json() or {}
    answers_data = data.get('answers', {})

    # Crear respuesta con token único de edición
    edit_token = uuid.uuid4().hex
    response = FormResponse(
        form_id=form_id,
        edit_token=edit_token,
        nombre_completo=data.get('nombre_completo', ''),
        email=data.get('email', ''),
        telefono=data.get('telefono', ''),
        edad=int(data.get('edad')) if data.get('edad') else None,
    )

    # Calificación automática para exámenes
    score = 0
    total_graded = 0
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()

    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        answer = FormAnswer(
            field_id=field.id,
            value=json.dumps(answer_value, ensure_ascii=False) if isinstance(answer_value, list) else str(answer_value)
        )
        response.answers.append(answer)

        # Auto-grading
        if form.form_type == 'examen' and field.correct_answer:
            total_graded += 1
            if field.field_type == 'checkbox':
                # Para checkbox, comparar listas
                correct = sorted(json.loads(field.correct_answer)) if field.correct_answer else []
                given = sorted(answer_value) if isinstance(answer_value, list) else []
                if correct == given:
                    score += 1
            else:
                # Para text/radio, comparar strings
                if str(answer_value).strip().lower() == field.correct_answer.strip().lower():
                    score += 1

    if form.form_type == 'examen' and total_graded > 0:
        response.score = round((score / total_graded) * 100, 1)
        response.total_questions = total_graded

    db.session.add(response)
    db.session.commit()

    # Preparar resumen de respuestas
    answers_summary_lines = []
    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        display_val = ', '.join(answer_value) if isinstance(answer_value, list) else str(answer_value)
        if display_val:
            answers_summary_lines.append(f"• {field.label}: {display_val}")
    answers_summary_text = '\n'.join(answers_summary_lines)

    nombre = data.get('nombre_completo', '')

    # URL de edición con token
    edit_url = f"{request.host_url}form/{form.slug or form.id}/editar/{response.edit_token}"

    # Preparar resultado
    result = {'ok': True, 'response_id': response.id, 'edit_token': response.edit_token, 'answers_summary': answers_summary_text, 'nombre': nombre}
    if form.form_type == 'examen':
        result['score'] = response.score
        result['correct'] = score
        result['total'] = total_graded

    # WhatsApp auto-send al usuario: mensaje personalizado con resumen
    telefono = data.get('telefono', '').strip().replace(' ', '').replace('-', '')
    if telefono and telefono[0] in ('6', '7', '8'):
        msg = f"📋 *{form.name}*\n\n"
        msg += f"Hola *{nombre or 'participante'}*, este mensaje es para ti.\n"
        msg += f"El sistema ya registró tu selección:\n\n"
        msg += answers_summary_text + "\n\n"
        if form.form_type == 'examen':
            msg += f"📊 Calificación: {score}/{total_graded} ({response.score}%)\n\n"
        if form.allow_edit and form.form_type != 'examen':
            msg += f"✏️ Si deseas cambiar tu selección, usa este enlace:\n{edit_url}\n\n"
        msg += f"✅ Gracias por completar el formulario."
        # Formato internacional Costa Rica
        if not telefono.startswith('+'):
            telefono = '506' + telefono
        result['whatsapp_url'] = f"https://wa.me/{telefono}?text={quote(msg)}"

    # Generar texto base para reenviar a admins
    admin_msg = f"📋 *{form.name}*\n"
    admin_msg += f"Respuesta de: *{nombre or 'Anónimo'}*\n\n"
    admin_msg += answers_summary_text + "\n"
    if form.form_type == 'examen' and response.score is not None:
        admin_msg += f"\n📊 Nota: {response.score}%\n"
    result['admin_msg'] = quote(admin_msg)

    return jsonify(result)


@bp.route('/api/forms/<int:form_id>/submit_file', methods=['POST'])
def api_submit_file(form_id):
    """Endpoint separado para subir archivos de formulario."""
    form = Form.query.get_or_404(form_id)
    if not form.is_active:
        return jsonify({'error': 'Formulario cerrado'}), 403
    file = request.files.get('file')
    field_id = request.form.get('field_id')
    if not file or not field_id:
        return jsonify({'error': 'Datos incompletos'}), 400
    os.makedirs(FORM_UPLOADS, exist_ok=True)
    filename = secure_filename(f"f{form_id}_{field_id}_{file.filename}")
    file.save(os.path.join(FORM_UPLOADS, filename))
    return jsonify({'ok': True, 'path': f"uploads/forms/{filename}"})


# ==========================================
# VER RESPUESTAS Y EXPORTAR
# ==========================================

@bp.route('/api/forms/<int:form_id>/responses')
def api_get_responses(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(FormResponse.submitted_at.desc()).all()

    output = []
    for r in responses:
        answers_map = {a.field_id: a.value for a in r.answers}
        row = {
            'id': r.id,
            'nombre_completo': r.nombre_completo,
            'email': r.email,
            'telefono': r.telefono,
            'edad': r.edad,
            'submitted_at': r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '',
            'score': r.score,
            'total_questions': r.total_questions,
            'answers': {}
        }
        for f in fields:
            val = answers_map.get(f.id, '')
            try:
                val = json.loads(val)
            except:
                pass
            row['answers'][str(f.id)] = val
        output.append(row)

    fields_info = [{'id': f.id, 'label': f.label, 'field_type': f.field_type} for f in fields]
    return jsonify({'fields': fields_info, 'responses': output})


@bp.route('/api/forms/<int:form_id>/export/<fmt>')
def api_export_responses(form_id, fmt):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(FormResponse.submitted_at.desc()).all()

    if fmt == 'json':
        rows = []
        for r in responses:
            answers_map = {a.field_id: a.value for a in r.answers}
            row = {'nombre': r.nombre_completo, 'email': r.email, 'telefono': r.telefono, 'edad': r.edad,
                   'fecha': r.submitted_at.isoformat() if r.submitted_at else '', 'score': r.score}
            for f in fields:
                val = answers_map.get(f.id, '')
                try: val = json.loads(val)
                except: pass
                row[f.label] = val
            rows.append(row)
        raw = json.dumps(rows, ensure_ascii=False, indent=2)
        return Response(raw, mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename="{form.name}.json"'})

    elif fmt == 'xlsx':
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = form.name[:30]
            # Header
            headers = ['Nombre', 'Email', 'Teléfono', 'Edad', 'Fecha']
            if form.form_type == 'examen':
                headers.append('Calificación')
            for f in fields:
                headers.append(f.label)
            ws.append(headers)
            # Data
            for r in responses:
                answers_map = {a.field_id: a.value for a in r.answers}
                row = [r.nombre_completo, r.email, r.telefono, r.edad,
                       r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '']
                if form.form_type == 'examen':
                    row.append(f"{r.score}%" if r.score is not None else '')
                for f in fields:
                    val = answers_map.get(f.id, '')
                    try:
                        val = ', '.join(json.loads(val)) if val.startswith('[') else val
                    except: pass
                    row.append(val)
                ws.append(row)
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{form.name}.xlsx",
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except ImportError:
            return jsonify({'error': 'openpyxl no instalado. Ejecute: pip install openpyxl'}), 500

    elif fmt == 'whatsapp':
        # Generar texto para copiar y enviar por WhatsApp
        lines = [f"📋 *{form.name}*", f"Respuestas: {len(responses)}", ""]
        for i, r in enumerate(responses[:50], 1):
            answers_map = {a.field_id: a.value for a in r.answers}
            lines.append(f"*{i}. {r.nombre_completo or 'Anónimo'}*")
            if form.form_type == 'examen' and r.score is not None:
                lines.append(f"   Nota: {r.score}%")
            for f in fields:
                val = answers_map.get(f.id, '')
                try:
                    val = ', '.join(json.loads(val)) if val.startswith('[') else val
                except: pass
                lines.append(f"   • {f.label}: {val}")
            lines.append("")
        return jsonify({'text': '\n'.join(lines)})

    return jsonify({'error': 'Formato no soportado'}), 400


# ==========================================
# BUSCAR HIKERS PARA AUTOCOMPLETAR
# ==========================================

@bp.route('/api/forms/search_hikers')
def api_search_hikers():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    results = []
    # Buscar por cédula exacta o parcial
    if q.isdigit():
        hikers = Hiker.query.filter(Hiker.cedula.contains(q)).limit(10).all()
    else:
        hikers = Hiker.query.filter(Hiker.nombre_completo.ilike(f'%{q}%')).limit(10).all()
    for h in hikers:
        results.append({
            'cedula': h.cedula,
            'nombre_completo': h.nombre_completo,
            'telefono': h.telefono or '',
            'email': ''
        })
    return jsonify(results)


# ==========================================
# ELIMINAR RESPUESTA INDIVIDUAL
# ==========================================

@bp.route('/api/forms/responses/<int:response_id>', methods=['DELETE'])
def api_delete_response(response_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    resp = FormResponse.query.get_or_404(response_id)
    db.session.delete(resp)
    db.session.commit()
    return jsonify({'ok': True})


# ==========================================
# EDITAR RESPUESTA (solo registro, no examen)
# ==========================================

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

    data = request.get_json() or {}
    answers_data = data.get('answers', {})

    resp.nombre_completo = data.get('nombre_completo', resp.nombre_completo)
    resp.email = data.get('email', resp.email)
    resp.telefono = data.get('telefono', resp.telefono)
    resp.edad = int(data.get('edad')) if data.get('edad') else resp.edad

    # Actualizar respuestas
    existing = {a.field_id: a for a in resp.answers}
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        val = json.dumps(answer_value, ensure_ascii=False) if isinstance(answer_value, list) else str(answer_value)
        if field.id in existing:
            existing[field.id].value = val
        else:
            resp.answers.append(FormAnswer(field_id=field.id, value=val))

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/forms/<int:form_id>/my_response')
def api_get_my_response(form_id):
    """Buscar respuesta existente por nombre para permitir edición."""
    nombre = request.args.get('nombre', '').strip()
    if not nombre:
        return jsonify({'found': False})
    resp = FormResponse.query.filter_by(form_id=form_id, nombre_completo=nombre).first()
    if not resp:
        return jsonify({'found': False})
    answers_map = {}
    for a in resp.answers:
        try:
            answers_map[str(a.field_id)] = json.loads(a.value)
        except:
            answers_map[str(a.field_id)] = a.value
    return jsonify({
        'found': True,
        'response_id': resp.id,
        'nombre_completo': resp.nombre_completo,
        'email': resp.email or '',
        'telefono': resp.telefono or '',
        'edad': resp.edad,
        'answers': answers_map
    })


@bp.route('/api/forms/admin/responses/<int:response_id>', methods=['PUT'])
def api_admin_update_response(response_id):
    """Edición de respuesta por superusuario (sin restricción de allow_edit)."""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    resp = FormResponse.query.get_or_404(response_id)
    data = request.get_json() or {}
    answers_data = data.get('answers', {})

    resp.nombre_completo = data.get('nombre_completo', resp.nombre_completo)
    resp.email = data.get('email', resp.email)
    resp.telefono = data.get('telefono', resp.telefono)
    if data.get('edad'):
        resp.edad = int(data['edad'])

    existing = {a.field_id: a for a in resp.answers}
    fields = FormField.query.filter_by(form_id=resp.form_id).order_by(FormField.order).all()
    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        val = str(answer_value)
        if field.id in existing:
            existing[field.id].value = val
        else:
            resp.answers.append(FormAnswer(field_id=field.id, value=val))

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/forms/response_by_token/<token>')
def api_get_response_by_token(token):
    """Obtener respuesta por edit_token para precargar el formulario."""
    resp = FormResponse.query.filter_by(edit_token=token).first()
    if not resp:
        return jsonify({'found': False})
    answers_map = {}
    for a in resp.answers:
        try:
            answers_map[str(a.field_id)] = json.loads(a.value)
        except:
            answers_map[str(a.field_id)] = a.value
    return jsonify({
        'found': True,
        'response_id': resp.id,
        'nombre_completo': resp.nombre_completo,
        'email': resp.email or '',
        'telefono': resp.telefono or '',
        'edad': resp.edad,
        'answers': answers_map
    })
