# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""Ruta de exportación de respuestas: json/xlsx/pdf/whatsapp/txt/singlepage."""
import json
from io import BytesIO
from flask import request, jsonify, session, send_file, Response
from models import Form, FormField, FormResponse
from routes import bp
from routes.forms_responses_utils import _build_answers_map, _fmt_tel
from routes.forms_export_pdf import _export_pdf
from routes.forms_export_singlepage import _export_singlepage_offline


# ── EXPORTAR RESPUESTAS ──────────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/export/<fmt>')
def api_export_responses(form_id, fmt):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form      = Form.query.get_or_404(form_id)
    fields    = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(
                FormResponse.submitted_at.desc()).all()

    add_membrete = request.args.get('membrete', 'true').lower() == 'true'
    include_fecha = request.args.get('include_fecha', 'true').lower() == 'true'
    include_ficha_medica = request.args.get('include_ficha_medica', 'true').lower() == 'true'

    if fmt == 'json':
        rows = []
        for r in responses:
            row = {'nombre': r.nombre_completo}
            if form.show_cedula:
                row['cedula'] = r.cedula or ''
            row['reservation_number'] = r.reservation_number or ''
            row.update({'email': r.email, 'telefono': _fmt_tel(r.telefono, form),
                        'edad': r.edad, 'fecha': r.submitted_at.isoformat() if r.submitted_at else '',
                        'score': r.score})
            if form.show_ficha_medica:
                row.update({'tipo_sangre': r.tipo_sangre or '', 'alergias': r.alergias or '',
                            'enfermedades_cronicas': r.enfermedades_cronicas or '',
                            'contacto_emergencia_nombre': r.contacto_emergencia_nombre or '',
                            'contacto_emergencia_telefono': _fmt_tel(r.contacto_emergencia_telefono, form)})
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
            headers.append('Número de Reserva')
            headers += ['Email', 'Teléfono', 'Edad', 'Fecha']
            if form.form_type == 'examen':
                headers.append('Calificación')
            if form.show_ficha_medica:
                headers += ['Tipo de Sangre', 'Alergias', 'Enfermedades Crónicas',
                            'Contacto Emergencia Nombre', 'Contacto Emergencia Teléfono']
            headers += [f.label for f in fields]
            ws.append(headers)
            for r in responses:
                row = [r.nombre_completo]
                if form.show_cedula:
                    row.append(r.cedula or '')
                row.append(r.reservation_number or '')
                row += [r.email, _fmt_tel(r.telefono, form), r.edad,
                        r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '']
                if form.form_type == 'examen':
                    row.append(f"{r.score}%" if r.score is not None else '')
                if form.show_ficha_medica:
                    row += [r.tipo_sangre or '', r.alergias or '', r.enfermedades_cronicas or '',
                           r.contacto_emergencia_nombre or '', _fmt_tel(r.contacto_emergencia_telefono, form)]
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

    if fmt == 'pdf':
        return _export_pdf(form, fields, responses, add_membrete,
                           include_fecha, include_ficha_medica)

    if fmt == 'whatsapp':
        lines = [f"*{form.name}*", f"Respuestas: {len(responses)}", ""]
        for i, r in enumerate(responses[:50], 1):
            lines.append(f"*{i}. {r.nombre_completo or 'Anónimo'}*")
            if r.reservation_number:
                lines.append(f"   - Número de Reserva: {r.reservation_number}")
            if include_fecha and r.submitted_at:
                lines.append(f"   - Fecha: {r.submitted_at.strftime('%d/%m/%Y %H:%M')}")
            if form.form_type == 'examen' and r.score is not None:
                lines.append(f"   - Nota: {r.score}%")
            if include_ficha_medica and form.show_ficha_medica:
                if r.tipo_sangre:
                    lines.append(f"   - Tipo Sangre: {r.tipo_sangre}")
                if r.alergias:
                    lines.append(f"   - Alergias: {r.alergias}")
                if r.enfermedades_cronicas:
                    lines.append(f"   - Enf. Crónicas: {r.enfermedades_cronicas}")
                if r.contacto_emergencia_nombre:
                    lines.append(f"   - Contacto Emergencia: {r.contacto_emergencia_nombre} {_fmt_tel(r.contacto_emergencia_telefono, form)}")
            for f in fields:
                val = _build_answers_map(r, [f]).get(str(f.id), '')
                if isinstance(val, list):
                    val = ', '.join(val)
                lines.append(f"   - {f.label}: {val}")
            lines.append("")
        return jsonify({'text': '\n'.join(lines)})

    if fmt == 'txt':
        lines = []
        if add_membrete:
            lines.append("=" * 60)
            lines.append("La Tribu de Los Libres")
            lines.append("Cartago, La Unión, San Diego")
            lines.append("86227500 -")
            lines.append("")
            lines.append("Responsables")
            lines.append("Kenneth Ruiz Matamoros - 86227500")
            lines.append("Jenny Ceciliano Cordoba - 86520937")
            lines.append("lthikingcr@gmail.com")
            lines.append("")
            lines.append("=" * 60)
            lines.append("")
        lines.append(f"FORMULARIO: {form.name}")
        lines.append(f"Cantidad Personas == {len(responses)} Respuestas")
        # Números de reserva si existen (desde parámetro)
        reservation_numbers = request.args.get('reservation_numbers', '')
        if reservation_numbers:
            lines.append(f"Números de Reserva: {reservation_numbers}")
        lines.append("=" * 60)
        lines.append("")

        for i, r in enumerate(responses, 1):
            lines.append(f"#{i} - {r.nombre_completo or 'Sin nombre'}")
            if r.reservation_number:
                lines.append(f"Número de Reserva: {r.reservation_number}")
            if form.show_cedula and r.cedula:
                lines.append(f"Cédula: {r.cedula}")
            if r.email:
                lines.append(f"Email: {r.email}")
            if r.telefono:
                lines.append(f"Teléfono: {_fmt_tel(r.telefono, form)}")
            if include_fecha and r.edad:
                lines.append(f"Edad: {r.edad}")
            if include_fecha and r.submitted_at:
                lines.append(f"Fecha: {r.submitted_at.strftime('%d/%m/%Y %H:%M')}")
            if form.form_type == 'examen' and r.score is not None:
                lines.append(f"Calificación: {r.score}%")
            if include_ficha_medica and form.show_ficha_medica:
                lines.append("Ficha Médica:")
                if r.tipo_sangre:
                    lines.append(f"  Tipo de Sangre: {r.tipo_sangre}")
                if r.alergias:
                    lines.append(f"  Alergias: {r.alergias}")
                if r.enfermedades_cronicas:
                    lines.append(f"  Enfermedades Crónicas: {r.enfermedades_cronicas}")
                if r.contacto_emergencia_nombre:
                    lines.append(f"  Contacto Emergencia: {r.contacto_emergencia_nombre} {_fmt_tel(r.contacto_emergencia_telefono, form)}")
            for f in fields:
                val = _build_answers_map(r, [f]).get(str(f.id), '')
                if isinstance(val, list):
                    val = ', '.join(val)
                if val:
                    lines.append(f"{f.label}: {val}")
            lines.append("-" * 40)
            lines.append("")

        content = '\n'.join(lines)
        return Response(content, mimetype='text/plain',
                        headers={'Content-Disposition': f'attachment; filename="{form.name}.txt"'})

    if fmt == 'singlepage':
        return _export_singlepage_offline(form, fields, responses)

    return jsonify({'error': 'Formato no soportado'}), 400
