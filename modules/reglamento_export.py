# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/reglamento_export.py - Reglamento de puntos en TXT, WhatsApp y PDF
import re
from io import BytesIO
from urllib.parse import quote
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

LIMITE_URL = 7000
TITULO = 'Reglamento Oficial del Sistema de Puntos - La Tribu de los Libres'


def _inline(segs, b=lambda s: s, i=lambda s: s):
    out = ''
    for t, bo, it, _u in segs:
        core = t.strip()
        if not core:
            out += t
            continue
        w = i(b(core) if bo else core) if it else (b(core) if bo else core)
        out += t[:len(t) - len(t.lstrip())] + w + t[len(t.rstrip()):]
    return re.sub(r'[ \t]+', ' ', out).strip()


def _texto(bloques, b=lambda s: s, i=lambda s: s, mayus=True):
    lineas = []
    for bl in bloques:
        txt = _inline(bl['segs'], b, i)
        if bl['kind'] in ('titulo', 'capitulo'):
            lineas += ['', b(txt.upper() if mayus else txt)]
        elif bl['kind'] == 'li':
            lineas.append(f'{bl["marker"]} {txt}')
        else:
            lineas += ['', txt]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lineas)).strip()


def a_texto(bloques):
    return _texto(bloques)


def a_whatsapp(bloques):
    return _texto(bloques, b=lambda s: f'*{s}*', i=lambda s: f'_{s}_', mayus=False)


def url_whatsapp(bloques, url_pdf, url_pagina):
    """Texto completo si cabe en el enlace; si no, resumen de capítulos con enlaces al PDF y la página."""
    url = 'https://wa.me/?text=' + quote(a_whatsapp(bloques))
    if len(url) <= LIMITE_URL:
        return url
    caps = [_inline(b['segs']) for b in bloques if b['kind'] == 'capitulo']
    resumen = '\n'.join(f'• {c}' for c in caps)
    texto = f'*{TITULO}*\n\n{resumen}\n\nLeelo completo aquí:\n{url_pagina}\n\nPDF: {url_pdf}'
    return 'https://wa.me/?text=' + quote(texto)


def a_pdf(bloques):
    base = ParagraphStyle('base', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=6)
    estilos = {
        'titulo': ParagraphStyle('t', parent=base, fontName='Helvetica-Bold', fontSize=16, leading=20, alignment=1),
        'capitulo': ParagraphStyle('c', parent=base, fontName='Helvetica-Bold', fontSize=12, leading=16,
                                   textColor=colors.HexColor('#ff8c00'), spaceBefore=10),
        'p': base,
        'li': ParagraphStyle('l', parent=base, leftIndent=20, bulletIndent=8, spaceAfter=3),
    }
    alin = {'left': 0, 'center': 1, 'right': 2, 'justify': 4}
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                            bottomMargin=2 * cm, title=TITULO)
    story = []
    for bl in bloques:
        est = estilos.get(bl['kind'], base)
        if bl['align'] != 'left':
            est = ParagraphStyle('x', parent=est, alignment=alin.get(bl['align'], 0))
        html = ''
        for t, bo, it, un in bl['segs']:
            h = escape(t).replace('\n', '<br/>')
            h = f'<b>{h}</b>' if bo else h
            h = f'<i>{h}</i>' if it else h
            html += f'<u>{h}</u>' if un else h
        story.append(Paragraph(html.strip(), est, bulletText=bl['marker'] or None))
    if not story:
        story.append(Spacer(1, 1))
    doc.build(story)
    return buf.getvalue()
