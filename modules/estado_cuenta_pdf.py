# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/estado_cuenta_pdf.py - Estado de cuenta de puntos en PDF
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape
from modules.points_engine import get_points_engine

ORANGE = colors.HexColor('#ff8c00')


def _tipo(t):
    return (t or '').replace('_', ' ').capitalize()


def build_estado_cuenta_pdf(cedula, hiker=None):
    engine = get_points_engine()
    history = engine.history_with_names(cedula)
    total = engine.total_by_cedula(cedula)
    ganados = sum(r['puntos'] for r in history if r['puntos'] > 0)
    usados = -sum(r['puntos'] for r in history if r['puntos'] < 0)
    ss = getSampleStyleSheet()
    title = ParagraphStyle('t', parent=ss['Title'], textColor=ORANGE, fontSize=18, spaceAfter=2)
    sub = ParagraphStyle('s', parent=ss['Normal'], alignment=1, textColor=colors.grey, fontSize=9)
    cell = ParagraphStyle('c', parent=ss['Normal'], fontSize=8, leading=10)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm, title='Estado de cuenta de puntos')
    nombre = escape(hiker.nombre_completo if hiker and hiker.nombre_completo else '')
    story = [Paragraph('Estado de cuenta de puntos', title),
             Paragraph('La Tribu de los Libres', sub), Spacer(1, 12),
             Paragraph(f'<b>Nombre:</b> {nombre}<br/><b>Cédula:</b> {escape(str(cedula))}<br/>'
                       f'<b>Generado:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}', ss['Normal']),
             Spacer(1, 10)]
    resumen = Table([['Total actual', 'Ganados', 'Usados / restados'],
                     [f'{total:,}', f'{ganados:,}', f'{usados:,}']], colWidths=[6 * cm] * 3)
    resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, 1), 14), ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 6)]))
    story += [resumen, Spacer(1, 14), Paragraph('<b>Movimientos</b>', ss['Heading3'])]
    rows = [['Fecha', 'Actividad', 'Tipo', 'Detalle', 'Puntos']]
    for r in history:
        f = (r.get('creado_at') or '')[:10]
        f = f'{f[8:10]}/{f[5:7]}/{f[0:4]}' if len(f) == 10 else ''
        rows.append([f, Paragraph(escape(r.get('evento_nombre') or 'Actividad general'), cell),
                     Paragraph(escape(_tipo(r.get('tipo'))), cell), Paragraph(escape(r.get('detalle') or ''), cell),
                     f'{r["puntos"]:+,}'])
    if len(rows) == 1:
        rows.append(['', 'Sin movimientos registrados', '', '', ''])
    tabla = Table(rows, colWidths=[2.2 * cm, 4.6 * cm, 2.8 * cm, 6.2 * cm, 2.2 * cm], repeatRows=1)
    style = [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#444444')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8),
             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
             ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
             ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf6f0')])]
    for i, r in enumerate(history, start=1):
        style.append(('TEXTCOLOR', (-1, i), (-1, i), colors.HexColor('#c62828' if r['puntos'] < 0 else '#2e7d32')))
    tabla.setStyle(TableStyle(style))
    story.append(tabla)
    doc.build(story)
    return buf.getvalue()
