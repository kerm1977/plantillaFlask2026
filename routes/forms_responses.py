import json
from io import BytesIO
from flask import request, jsonify, session, send_file, Response
from models import Form, FormField, FormResponse
from db import db
from routes import bp
from routes.forms_responses_utils import _build_answers_map, _update_response_answers


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
               'submitted_at': r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '',
               'score': r.score, 'total_questions': r.total_questions,
               'answers': _build_answers_map(r, fields)}
        output.append(row)
    fields_info = [{'id': f.id, 'label': f.label, 'field_type': f.field_type,
                    'options': json.loads(f.options) if f.options else []} for f in fields]
    return jsonify({'fields': fields_info, 'responses': output,
                    'show_cedula': form.show_cedula})


# ── EXPORTAR RESPUESTAS ──────────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/export/<fmt>')
def api_export_responses(form_id, fmt):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form      = Form.query.get_or_404(form_id)
    fields    = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(
                FormResponse.submitted_at.desc()).all()

    if fmt == 'json':
        rows = []
        for r in responses:
            row = {'nombre': r.nombre_completo}
            if form.show_cedula:
                row['cedula'] = r.cedula or ''
            row.update({'email': r.email, 'telefono': r.telefono,
                        'edad': r.edad, 'fecha': r.submitted_at.isoformat() if r.submitted_at else '',
                        'score': r.score})
            for f in fields:
                val = _build_answers_map(r, [f]).get(str(f.id), '')
                row[f.label] = val
            rows.append(row)
        raw = json.dumps(rows, ensure_ascii=False, indent=2)
        return Response(raw, mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename="{form.name}.json"'})

    if fmt == 'xlsx':
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = form.name[:30]
            headers = ['Nombre']
            if form.show_cedula:
                headers.append('Cédula')
            headers += ['Email', 'Teléfono', 'Edad', 'Fecha']
            if form.form_type == 'examen':
                headers.append('Calificación')
            headers += [f.label for f in fields]
            ws.append(headers)
            for r in responses:
                row = [r.nombre_completo]
                if form.show_cedula:
                    row.append(r.cedula or '')
                row += [r.email, r.telefono, r.edad,
                        r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '']
                if form.form_type == 'examen':
                    row.append(f"{r.score}%" if r.score is not None else '')
                for f in fields:
                    val = _build_answers_map(r, [f]).get(str(f.id), '')
                    if isinstance(val, list):
                        val = ', '.join(val)
                    row.append(val)
                ws.append(row)
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{form.name}.xlsx",
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except ImportError:
            return jsonify({'error': 'openpyxl no instalado. Ejecute: pip install openpyxl'}), 500

    if fmt == 'whatsapp':
        lines = [f"📋 *{form.name}*", f"Respuestas: {len(responses)}", ""]
        for i, r in enumerate(responses[:50], 1):
            lines.append(f"*{i}. {r.nombre_completo or 'Anónimo'}*")
            if form.form_type == 'examen' and r.score is not None:
                lines.append(f"   Nota: {r.score}%")
            for f in fields:
                val = _build_answers_map(r, [f]).get(str(f.id), '')
                if isinstance(val, list):
                    val = ', '.join(val)
                lines.append(f"   • {f.label}: {val}")
            lines.append("")
        return jsonify({'text': '\n'.join(lines)})

    return jsonify({'error': 'Formato no soportado'}), 400


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
                    'edad': resp.edad, 'answers': _build_answers_map(resp, fields)})
