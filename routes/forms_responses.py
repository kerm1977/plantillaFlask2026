import json
import os
import base64
from io import BytesIO
from flask import request, jsonify, session, send_file, Response, render_template, current_app
from models import Form, FormField, FormResponse
from models_forms import ReservationConfig
from db import db
from routes import bp
from routes.forms_responses_utils import _build_answers_map, _update_response_answers


def _fmt_tel(tel, form):
    """Antepone +506 a teléfonos cuando el formulario solicita pasaporte."""
    if not tel:
        return ''
    if not form.show_pasaporte:
        return tel
    digits = ''.join(ch for ch in str(tel) if ch.isdigit())
    if not digits:
        return tel
    rest = digits[3:] if digits.startswith('506') else digits
    return f'+506 {rest}'


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
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            story = []
            styles = getSampleStyleSheet()
            
            # Estilo personalizado para el membrete
            membrete_style = ParagraphStyle(
                'Membrete',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            # Estilo para el título
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            # Agregar membrete si está activado
            if add_membrete:
                membrete = Paragraph("La Tribu de Los Libres<br/>Cartago, La Unión, San Diego<br/>86227500<br/><br/>Responsables<br/>Kenneth Ruiz Matamoros - 86227500<br/>Jenny Ceciliano Cordoba - 86520937<br/>lthikingcr@gmail.com", membrete_style)
                story.append(membrete)
                story.append(Spacer(1, 0.2 * inch))
            
            # Título del formulario
            title = Paragraph(f"FORMULARIO: {form.name}", title_style)
            story.append(title)
            
            # Cantidad de respuestas
            count_style = ParagraphStyle(
                'Count',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=11,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            count = Paragraph(f"Cantidad Personas == {len(responses)} Respuestas", count_style)
            story.append(count)
            
            # Números de reserva si existen (desde parámetro)
            reservation_numbers = request.args.get('reservation_numbers', '')
            if reservation_numbers:
                reservation_style = ParagraphStyle(
                    'Reservation',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=10,
                    alignment=TA_CENTER,
                    spaceAfter=12
                )
                reservation = Paragraph(f"Números de Reserva: {reservation_numbers}", reservation_style)
                story.append(reservation)
            
            story.append(Spacer(1, 0.2 * inch))
            
            # Estilo para encabezados de respuesta
            response_header_style = ParagraphStyle(
                'ResponseHeader',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=6,
                spaceBefore=12
            )
            
            # Estilo para campos de respuesta
            field_style = ParagraphStyle(
                'Field',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                alignment=TA_LEFT,
                leftIndent=20,
                spaceAfter=2
            )
            
            # Generar lista de respuestas
            for i, r in enumerate(responses, 1):
                # Encabezado de la respuesta
                reserva_text = f" (Reserva: {r.reservation_number})" if r.reservation_number else ""
                header = Paragraph(f"<b>#{i} - {r.nombre_completo or 'Sin nombre'}{reserva_text}</b>", response_header_style)
                story.append(header)
                
                # Campos de la respuesta
                if form.show_cedula and r.cedula:
                    story.append(Paragraph(f"<b>Cédula:</b> {r.cedula}", field_style))
                if r.email:
                    story.append(Paragraph(f"<b>Email:</b> {r.email}", field_style))
                if r.telefono:
                    story.append(Paragraph(f"<b>Teléfono:</b> {_fmt_tel(r.telefono, form)}", field_style))
                if include_fecha and r.edad:
                    story.append(Paragraph(f"<b>Edad:</b> {r.edad}", field_style))
                if include_fecha and r.submitted_at:
                    story.append(Paragraph(f"<b>Fecha:</b> {r.submitted_at.strftime('%d/%m/%Y %H:%M')}", field_style))
                if form.form_type == 'examen' and r.score is not None:
                    story.append(Paragraph(f"<b>Calificación:</b> {r.score}%", field_style))
                if include_ficha_medica and form.show_ficha_medica:
                    story.append(Paragraph("<b>Ficha Médica:</b>", field_style))
                    if r.tipo_sangre:
                        story.append(Paragraph(f"  <i>Tipo de Sangre:</i> {r.tipo_sangre}", field_style))
                    if r.alergias:
                        story.append(Paragraph(f"  <i>Alergias:</i> {r.alergias}", field_style))
                    if r.enfermedades_cronicas:
                        story.append(Paragraph(f"  <i>Enfermedades Crónicas:</i> {r.enfermedades_cronicas}", field_style))
                    if r.contacto_emergencia_nombre:
                        story.append(Paragraph(f"  <i>Contacto Emergencia:</i> {r.contacto_emergencia_nombre} {_fmt_tel(r.contacto_emergencia_telefono, form)}", field_style))
                for f in fields:
                    val = _build_answers_map(r, [f]).get(str(f.id), '')
                    if isinstance(val, list):
                        val = ', '.join(val)
                    if val:
                        story.append(Paragraph(f"<b>{f.label}:</b> {val}", field_style))
                
                # Línea separadora
                story.append(Paragraph("<hr/>", field_style))
            
            doc.build(story)
            
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{form.name}.pdf",
                             mimetype='application/pdf')
        except ImportError:
            return jsonify({'error': 'reportlab no instalado. Ejecute: pip install reportlab'}), 500

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

    if fmt == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            story = []
            styles = getSampleStyleSheet()
            
            # Estilo personalizado para el membrete
            membrete_style = ParagraphStyle(
                'Membrete',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            # Estilo para el título
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            # Agregar membrete si está activado
            if add_membrete:
                membrete = Paragraph("La Tribu de Los Libres<br/>Cartago, La Unión, San Diego<br/>86227500<br/><br/>Responsables<br/>Kenneth Ruiz Matamoros - 86227500<br/>Jenny Ceciliano Cordoba - 86520937<br/>lthikingcr@gmail.com", membrete_style)
                story.append(membrete)
                story.append(Spacer(1, 0.2 * inch))
            
            # Título del formulario
            title = Paragraph(f"FORMULARIO: {form.name}", title_style)
            story.append(title)
            
            # Cantidad de respuestas
            count_style = ParagraphStyle(
                'Count',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=11,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            count = Paragraph(f"Cantidad Personas == {len(responses)} Respuestas", count_style)
            story.append(count)
            
            # Números de reserva si existen (desde parámetro)
            reservation_numbers = request.args.get('reservation_numbers', '')
            if reservation_numbers:
                reservation_style = ParagraphStyle(
                    'Reservation',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=10,
                    alignment=TA_CENTER,
                    spaceAfter=12
                )
                reservation = Paragraph(f"Números de Reserva: {reservation_numbers}", reservation_style)
                story.append(reservation)
            
            story.append(Spacer(1, 0.2 * inch))
            
            # Estilo para encabezados de respuesta
            response_header_style = ParagraphStyle(
                'ResponseHeader',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=6,
                spaceBefore=12
            )
            
            # Estilo para campos de respuesta
            field_style = ParagraphStyle(
                'Field',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                alignment=TA_LEFT,
                leftIndent=20,
                spaceAfter=2
            )
            
            # Generar lista de respuestas
            for i, r in enumerate(responses, 1):
                # Encabezado de la respuesta
                reserva_text = f" (Reserva: {r.reservation_number})" if r.reservation_number else ""
                header = Paragraph(f"<b>#{i} - {r.nombre_completo or 'Sin nombre'}{reserva_text}</b>", response_header_style)
                story.append(header)
                
                # Campos de la respuesta
                if form.show_cedula and r.cedula:
                    story.append(Paragraph(f"<b>Cédula:</b> {r.cedula}", field_style))
                if r.email:
                    story.append(Paragraph(f"<b>Email:</b> {r.email}", field_style))
                if r.telefono:
                    story.append(Paragraph(f"<b>Teléfono:</b> {_fmt_tel(r.telefono, form)}", field_style))
                if include_fecha and r.edad:
                    story.append(Paragraph(f"<b>Edad:</b> {r.edad}", field_style))
                if include_fecha and r.submitted_at:
                    story.append(Paragraph(f"<b>Fecha:</b> {r.submitted_at.strftime('%d/%m/%Y %H:%M')}", field_style))
                if form.form_type == 'examen' and r.score is not None:
                    story.append(Paragraph(f"<b>Calificación:</b> {r.score}%", field_style))
                if include_ficha_medica and form.show_ficha_medica:
                    story.append(Paragraph("<b>Ficha Médica:</b>", field_style))
                    if r.tipo_sangre:
                        story.append(Paragraph(f"  <i>Tipo de Sangre:</i> {r.tipo_sangre}", field_style))
                    if r.alergias:
                        story.append(Paragraph(f"  <i>Alergias:</i> {r.alergias}", field_style))
                    if r.enfermedades_cronicas:
                        story.append(Paragraph(f"  <i>Enfermedades Crónicas:</i> {r.enfermedades_cronicas}", field_style))
                    if r.contacto_emergencia_nombre:
                        story.append(Paragraph(f"  <i>Contacto Emergencia:</i> {r.contacto_emergencia_nombre} {_fmt_tel(r.contacto_emergencia_telefono, form)}", field_style))
                for f in fields:
                    val = _build_answers_map(r, [f]).get(str(f.id), '')
                    if isinstance(val, list):
                        val = ', '.join(val)
                    if val:
                        story.append(Paragraph(f"<b>{f.label}:</b> {val}", field_style))
                
                # Línea separadora
                story.append(Paragraph("<hr/>", field_style))
            
            doc.build(story)
            
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{form.name}.pdf",
                             mimetype='application/pdf')
        except ImportError:
            return jsonify({'error': 'reportlab no instalado. Ejecute: pip install reportlab'}), 500

    if fmt == 'singlepage':
        return _export_singlepage_offline(form, fields, responses)

    return jsonify({'error': 'Formato no soportado'}), 400


def _static_img_b64(rel_path):
    """Devuelve una imagen de static/ como data URI base64, o None si no existe."""
    if not rel_path:
        return None
    path = os.path.join(current_app.static_folder, rel_path)
    if not os.path.exists(path):
        return None
    ext = 'png' if rel_path.lower().endswith('.png') else 'jpeg'
    with open(path, 'rb') as fh:
        return f'data:image/{ext};base64,' + base64.b64encode(fh.read()).decode()


def _export_singlepage_offline(form, fields, responses):
    """Genera una página HTML offline con buscador y la tarjeta QR de agenda
    (logo, foto, puntos, datos y código QR) para cada persona que respondió."""
    import re
    from datetime import datetime
    from models import Hiker, User
    from routes.admin_actions import _tarjeta_url, _generar_qr_usuario
    from modules.points_engine import get_points_engine

    engine = get_points_engine()
    logo_b64 = _static_img_b64('logo.png')
    default_avatar_b64 = _static_img_b64('default.png')

    def _resolver_user(hiker, bound_email):
        user = None
        if bound_email:
            user = User.query.filter(db.func.lower(User.email) == bound_email).first()
        if not user and hiker and hiker.telefono:
            user = User.query.filter_by(phone=hiker.telefono).first()
        if not user and hiker and hiker.nombre_completo:
            objetivo = hiker.nombre_completo.strip().lower()
            for u in User.query.all():
                if f'{u.name} {u.last_name_1} {u.last_name_2}'.strip().lower() == objetivo:
                    user = u
                    break
        return user

    personas = []
    for r in responses:
        cedula_limpia = re.sub(r'\D', '', str(r.cedula or ''))
        hiker = None
        if cedula_limpia:
            for h in Hiker.query.all():
                if h.cedula and re.sub(r'\D', '', str(h.cedula)) == cedula_limpia:
                    hiker = h
                    break
        bound_email = (hiker.card_email or '').strip().lower() if hiker else ''
        user = _resolver_user(hiker, bound_email)

        # QR: mismo enlace inmutable que el QR de la agenda (requiere expediente)
        qr_b64, card_url = None, ''
        if hiker:
            card_url = _tarjeta_url(user, hiker)
            qr_b64 = _generar_qr_usuario(user, hiker)
            bound_email = (hiker.card_email or '').strip().lower()

        # Foto: avatar del usuario si existe, si no, default
        avatar_file = (user.avatar if user else None) or 'default.png'
        if avatar_file != 'default.png' and not avatar_file.startswith('uploads/'):
            avatar_file = 'uploads/' + avatar_file
        avatar_b64 = _static_img_b64(avatar_file) or default_avatar_b64

        nacimiento = ''
        if user and user.dob:
            nacimiento = user.dob.strftime('%d/%m/%Y')
        elif hiker and hiker.fecha_nacimiento:
            nacimiento = hiker.fecha_nacimiento.strftime('%d/%m/%Y')
        elif r.fecha_nacimiento_dia and r.fecha_nacimiento_mes and r.fecha_nacimiento_anio:
            nacimiento = f'{r.fecha_nacimiento_dia}/{r.fecha_nacimiento_mes}/{r.fecha_nacimiento_anio}'

        telefono = (hiker.telefono if hiker else '') or r.telefono or (user.phone if user else '') or ''
        phone_code = (user.phone_code or '') if user else ''
        if phone_code:
            telefono = f'{phone_code} {telefono}'.strip()
        else:
            telefono = _fmt_tel(telefono, form)

        email_display = bound_email if bound_email and '@' in bound_email else (r.email or '')

        cedula_puntos = (hiker.cedula if hiker else '') or r.cedula or ''
        puntos_total = engine.total_by_cedula(cedula_puntos) if cedula_puntos else 0

        nombre = (hiker.nombre_completo if hiker else '') or r.nombre_completo or 'Sin nombre'
        personas.append({
            'nombre': nombre,
            'cedula': (hiker.cedula if hiker else '') or r.cedula or '',
            'email': email_display,
            'telefono': telefono,
            'tipo_sangre': (hiker.tipo_sangre if hiker else '') or r.tipo_sangre or '?',
            'nacimiento': nacimiento,
            'pasaporte': (hiker.pasaporte if hiker else '') or r.pasaporte or '',
            'alergias': (hiker.alergias if hiker else '') or r.alergias or 'Ninguna',
            'cronicas': (hiker.enfermedades_cronicas if hiker else '') or r.enfermedades_cronicas or 'Ninguna',
            'emerg_nombre': (hiker.contacto_emergencia_nombre if hiker else '') or r.contacto_emergencia_nombre or '',
            'emerg_tel': _fmt_tel((hiker.contacto_emergencia_telefono if hiker else '') or r.contacto_emergencia_telefono or '', form),
            'whatsapp': (user.whatsapp if user else '') or '',
            'direccion': (user.address if user else '') or '',
            'institucion': (user.institution if user else '') or '',
            'info_adicional': (user.other_info if user else '') or '',
            'reserva': r.reservation_number or '',
            'puntos': puntos_total,
            'qr_b64': qr_b64,
            'card_url': card_url,
            'avatar_b64': avatar_b64,
            'search': ' '.join([nombre, (hiker.cedula if hiker else '') or r.cedula or '',
                                (hiker.pasaporte if hiker else '') or r.pasaporte or '',
                                telefono, email_display]).lower(),
        })

    html = render_template('singlepage_offline.html', form=form, personas=personas,
                           logo_b64=logo_b64, generado=datetime.now().strftime('%d/%m/%Y %H:%M'))
    return Response(html, mimetype='text/html',
                    headers={'Content-Disposition': f'attachment; filename="{form.name} - offline.html"'})


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
