# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/reglamento.py - Reglamento de puntos editable: guardado, sanitizado y lectura por bloques
import re
from html import escape
from html.parser import HTMLParser
from flask import render_template
from db import db
from models import SiteContent

KEY = 'reglamento_puntos_html'
MAX_LEN = 80000
PERMITIDAS = {'h5', 'h6', 'p', 'ul', 'ol', 'li', 'b', 'strong', 'i', 'em', 'u', 'br', 'a'}
BLOQUES = {'h5', 'h6', 'p', 'ul', 'ol', 'li'}
ALINEA = re.compile(r'text-align\s*:\s*(left|right|center|justify)', re.I)
HREF_OK = re.compile(r'^(https?://|/)', re.I)


class _Limpia(HTMLParser):
    """Deja solo etiquetas permitidas (formato del reglamento); descarta scripts, estilos y atributos."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.abiertas, self.omitir = [], [], 0

    def _span(self, estilo):
        """El navegador a veces formatea con <span style>: se convierte a b/i/u."""
        marcas = [t for t, rx in (('b', r'font-weight\s*:\s*(bold|[6-9]00)'), ('i', r'font-style\s*:\s*italic'),
                                  ('u', r'text-decoration[^;]*underline')) if re.search(rx, estilo or '', re.I)]
        self.out.append(''.join(f'<{t}>' for t in marcas))
        self.abiertas.append(('span', ''.join(f'</{t}>' for t in reversed(marcas))))

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.omitir += 1
            return
        if tag == 'span' and not self.omitir:
            self._span(dict(attrs).get('style'))
            return
        tag = 'p' if tag == 'div' else tag
        if tag not in PERMITIDAS or self.omitir:
            return
        a = dict(attrs)
        if tag == 'br':
            self.out.append('<br>')
            return
        extra = ''
        if tag in BLOQUES:
            m = ALINEA.search(a.get('style') or '')
            extra = f' style="text-align:{m.group(1).lower()}"' if m else ''
        elif tag == 'a':
            href = (a.get('href') or '').strip()
            extra = f' href="{escape(href, True)}" rel="noopener"' if HREF_OK.match(href) else ''
        self.abiertas.append((tag, f'</{tag}>'))
        self.out.append(f'<{tag}{extra}>')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.omitir = max(0, self.omitir - 1)
            return
        tag = 'p' if tag == 'div' else tag
        if tag in [t for t, _ in self.abiertas] and not self.omitir:
            while self.abiertas:
                t, cierre = self.abiertas.pop()
                self.out.append(cierre)
                if t == tag:
                    break

    def handle_data(self, data):
        if not self.omitir:
            self.out.append(escape(data, False))


def limpiar(html):
    p = _Limpia()
    p.feed((html or '')[:MAX_LEN])
    p.close()
    while p.abiertas:
        p.out.append(p.abiertas.pop()[1])
    limpio = ''.join(p.out)
    return re.sub(r'<(p|h5|h6|li)(?: style="[^"]*")?>(?:\s|<br>)*</\1>', '', limpio).strip()


class _Bloques(HTMLParser):
    """Convierte el HTML limpio en bloques [{kind, align, marker, segs:[(texto, negrita, cursiva, subrayado)]}]."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bloques, self.cur, self.listas = [], None, []
        self.b = self.i = self.u = 0

    def _cerrar(self):
        if self.cur and any(s[0].strip() for s in self.cur['segs']):
            self.bloques.append(self.cur)
        self.cur = None

    def _abrir(self, kind, attrs, marker=''):
        self._cerrar()
        m = ALINEA.search(dict(attrs).get('style') or '')
        self.cur = {'kind': kind, 'align': m.group(1).lower() if m else 'left', 'marker': marker, 'segs': []}

    def handle_starttag(self, tag, attrs):
        if tag in ('h5', 'h6', 'p'):
            self._abrir({'h5': 'titulo', 'h6': 'capitulo', 'p': 'p'}[tag], attrs)
        elif tag in ('ul', 'ol'):
            self._cerrar()
            self.listas.append([tag, 0])
        elif tag == 'li':
            lista = self.listas[-1] if self.listas else ['ul', 0]
            lista[1] += 1
            self._abrir('li', attrs, f'{lista[1]}.' if lista[0] == 'ol' else '•')
        elif tag in ('b', 'strong'):
            self.b += 1
        elif tag in ('i', 'em'):
            self.i += 1
        elif tag == 'u':
            self.u += 1
        elif tag == 'br' and self.cur:
            self.cur['segs'].append(('\n', 0, 0, 0))

    def handle_endtag(self, tag):
        if tag in ('h5', 'h6', 'p', 'li'):
            self._cerrar()
        elif tag in ('ul', 'ol') and self.listas:
            self._cerrar()
            self.listas.pop()
        elif tag in ('b', 'strong'):
            self.b = max(0, self.b - 1)
        elif tag in ('i', 'em'):
            self.i = max(0, self.i - 1)
        elif tag == 'u':
            self.u = max(0, self.u - 1)

    def handle_data(self, data):
        if self.cur is None:
            if not data.strip():
                return
            self._abrir('p', {})
        self.cur['segs'].append((re.sub(r'\s+', ' ', data), self.b > 0, self.i > 0, self.u > 0))


def obtener_html():
    fila = SiteContent.query.filter_by(key=KEY).first()
    if fila and fila.value.strip():
        return fila.value
    return render_template('partials/reglamento_puntos_body.html')


def bloques():
    p = _Bloques()
    p.feed(obtener_html())
    p.close()
    p._cerrar()
    return p.bloques


def guardar_html(raw):
    """Guarda el reglamento sanitizado. Si queda vacío, se restaura el texto original."""
    limpio = limpiar(raw)
    fila = SiteContent.query.filter_by(key=KEY).first()
    if not re.sub(r'<[^>]+>|&nbsp;|\s', '', limpio):
        if fila:
            db.session.delete(fila)
            db.session.commit()
        return {'ok': True, 'html': obtener_html(), 'restaurado': True}
    if fila:
        fila.value = limpio
    else:
        db.session.add(SiteContent(key=KEY, value=limpio))
    db.session.commit()
    return {'ok': True, 'html': limpio, 'restaurado': False}
