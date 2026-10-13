# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_estado_global.py - Estado de cuenta global (todas las
# personas) y lista de personas del programa de fidelidad (VIP).
# Solo superusuario. Exportable a pagina imprimible, TXT, PDF y WhatsApp.
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from flask import request, session, render_template, redirect, url_for, jsonify, Response

from routes import bp
from modules.estado_global import resumen_global

_NO_STORE = {'Cache-Control': 'no-store, no-cache, must-revalidate', 'Pragma': 'no-cache'}


def _forbidden():
    return jsonify({'ok': False, 'error': 'No autorizado'}), 403


def _filas():
    """Personas del estado global; con ?vip=1 solo Activo/Exclusivo VIP."""
    filas = resumen_global()
    if request.args.get('vip'):
        filas = [f for f in filas if f.get('vip') in ('activo', 'exclusivo')]
    return filas


def _titulo(vip):
    return ('Programa de Fidelidad - Personas VIP' if vip
            else 'Estado de cuenta global')


def _texto(filas, vip):
    t = _titulo(vip)
    lineas = [t.upper(), 'La Tribu de los Libres',
              'Generado: ' + datetime.now().strftime('%d/%m/%Y %H:%M'), '=' * 70, '']
    total_puntos = 0
    for f in filas:
        total_puntos += f['total']
        lineas.append(
            f"{f['nombre']} ({f['cedula']}) - {f.get('vip_label', '')}\n"
            f"  Puntos: {f['total']}  |  Ganados: +{f['ganados']}  Perdidos: -{f['perdidos']}\n"
            f"  Caminatas: {len(f['caminatas_ok'])} participadas / {f.get('retiros', 0)} retiradas\n"
            f"  Donados: {f.get('donados', 0)}  Obsequiados: +{f.get('obsequiados', 0)}  Restados: -{f.get('restados', 0)}")
        lineas.append('-' * 70)
    lineas.append(f'TOTAL DE PUNTOS SUMADOS: {total_puntos}')
    lineas.append(f'Personas en esta lista: {len(filas)}')
    return '\n'.join(lineas)


def _pdf(filas, vip):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    ss = getSampleStyleSheet()
    title = ParagraphStyle('t', parent=ss['Title'], textColor=colors.HexColor('#ff8c00'), fontSize=16)
    sub = ParagraphStyle('s', parent=ss['Normal'], alignment=1, textColor=colors.grey, fontSize=8)
    cell = ParagraphStyle('c', parent=ss['Normal'], fontSize=6.5, leading=8)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1 * cm, rightMargin=1 * cm,
                            topMargin=1 * cm, bottomMargin=1 * cm, title=_titulo(vip))
    header = ['Persona', 'Cedula', 'VIP', 'Puntos', 'Ganados', 'Perdidos',
              'Caminatas', 'Retiros', 'Donados', 'Obsequiados', 'Restados']
    data = [[Paragraph(f'<b>{h}</b>', cell) for h in header]]
    total_puntos = 0
    for f in filas:
        total_puntos += f['total']
        data.append([Paragraph(escape(f['nombre']), cell), escape(str(f['cedula'])),
                     escape(f.get('vip_label', '')), str(f['total']),
                     f"+{f['ganados']}", f"-{f['perdidos']}",
                     str(len(f['caminatas_ok'])), str(f.get('retiros', 0)),
                     str(f.get('donados', 0)), f"+{f.get('obsequiados', 0)}",
                     f"-{f.get('restados', 0)}"])
    data.append(['', '', 'TOTAL', str(total_puntos), '', '', '', '', '', '', ''])
    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff8c00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fff6ea')]),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffe9cc')),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    doc.build([Paragraph(_titulo(vip), title),
               Paragraph('La Tribu de los Libres - Generado: ' +
                         datetime.now().strftime('%d/%m/%Y %H:%M'), sub),
               Spacer(1, 8), tbl])
    return buf.getvalue()


@bp.route('/mis-puntos/estado-global')
def estado_global_page():
    """Pagina imprimible del estado de cuenta global (o solo VIPs con ?vip=1)."""
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.mis_puntos'))
    vip = bool(request.args.get('vip'))
    filas = _filas()
    from urllib.parse import quote
    wa_txt = _texto(filas[:30], vip)
    if len(filas) > 30:
        wa_txt += f'\n… y {len(filas) - 30} personas mas. Ver detalle completo en el panel.'
    wa_url = 'https://wa.me/?text=' + quote(wa_txt)
    return render_template('estado_global.html', filas=filas, vip=vip,
                           titulo=_titulo(vip), wa_url=wa_url,
                           total_puntos=sum(f['total'] for f in filas))


@bp.route('/admin/puntos/estado-global-whatsapp')
def estado_global_whatsapp():
    """Redirige a wa.me con el texto del estado global (o lista VIP)."""
    if session.get('role') != 'Superusuario':
        return _forbidden()
    vip = bool(request.args.get('vip'))
    filas = _filas()
    from urllib.parse import quote
    txt = _texto(filas[:30], vip)
    if len(filas) > 30:
        txt += f'\n… y {len(filas) - 30} personas mas. Ver detalle completo en el panel.'
    return redirect('https://wa.me/?text=' + quote(txt))


@bp.route('/admin/puntos/estado-global.txt')
def estado_global_txt():
    if session.get('role') != 'Superusuario':
        return _forbidden()
    vip = bool(request.args.get('vip'))
    nombre = 'fidelidad_vip.txt' if vip else 'estado_global.txt'
    return Response(_texto(_filas(), vip), mimetype='text/plain; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename={nombre}', **_NO_STORE})


@bp.route('/admin/puntos/estado-global.pdf')
def estado_global_pdf():
    if session.get('role') != 'Superusuario':
        return _forbidden()
    vip = bool(request.args.get('vip'))
    nombre = 'fidelidad_vip.pdf' if vip else 'estado_global.pdf'
    return Response(_pdf(_filas(), vip), mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename={nombre}', **_NO_STORE})
