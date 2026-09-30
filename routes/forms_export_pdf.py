# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""Exportación de respuestas de formularios a PDF (reportlab)."""
from io import BytesIO
from flask import request, jsonify, send_file
from routes.forms_responses_utils import _build_answers_map, _fmt_tel


def _export_pdf(form, fields, responses, add_membrete, include_fecha,
                include_ficha_medica):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()

        # Estilo personalizado para el membrete
        membrete_style = ParagraphStyle(
            'Membrete', parent=styles['Normal'], fontName='Helvetica-Bold',
            fontSize=12, alignment=TA_CENTER, spaceAfter=12)

        # Estilo para el título
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'], fontName='Helvetica-Bold',
            fontSize=16, alignment=TA_CENTER, spaceAfter=12)

        # Agregar membrete si está activado
        if add_membrete:
            membrete = Paragraph("La Tribu de Los Libres<br/>Cartago, La Unión, San Diego<br/>86227500<br/><br/>Responsables<br/>Kenneth Ruiz Matamoros - 86227500<br/>Jenny Ceciliano Cordoba - 86520937<br/>lthikingcr@gmail.com", membrete_style)
            story.append(membrete)
            story.append(Spacer(1, 0.2 * inch))

        # Título del formulario
        story.append(Paragraph(f"FORMULARIO: {form.name}", title_style))

        # Cantidad de respuestas
        count_style = ParagraphStyle(
            'Count', parent=styles['Normal'], fontName='Helvetica',
            fontSize=11, alignment=TA_CENTER, spaceAfter=12)
        story.append(Paragraph(f"Cantidad Personas == {len(responses)} Respuestas", count_style))

        # Números de reserva si existen (desde parámetro)
        reservation_numbers = request.args.get('reservation_numbers', '')
        if reservation_numbers:
            reservation_style = ParagraphStyle(
                'Reservation', parent=styles['Normal'], fontName='Helvetica',
                fontSize=10, alignment=TA_CENTER, spaceAfter=12)
            story.append(Paragraph(f"Números de Reserva: {reservation_numbers}", reservation_style))

        story.append(Spacer(1, 0.2 * inch))

        # Estilo para encabezados de respuesta
        response_header_style = ParagraphStyle(
            'ResponseHeader', parent=styles['Heading2'], fontName='Helvetica-Bold',
            fontSize=12, alignment=TA_LEFT, spaceAfter=6, spaceBefore=12)

        # Estilo para campos de respuesta
        field_style = ParagraphStyle(
            'Field', parent=styles['Normal'], fontName='Helvetica',
            fontSize=10, alignment=TA_LEFT, leftIndent=20, spaceAfter=2)

        # Generar lista de respuestas
        for i, r in enumerate(responses, 1):
            # Encabezado de la respuesta
            reserva_text = f" (Reserva: {r.reservation_number})" if r.reservation_number else ""
            story.append(Paragraph(f"<b>#{i} - {r.nombre_completo or 'Sin nombre'}{reserva_text}</b>", response_header_style))

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
