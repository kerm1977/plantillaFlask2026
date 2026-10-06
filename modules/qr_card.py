# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/qr_card.py - PNG del recuadro de puntos completo: replica
# la tarjeta que muestra scan_qr.html (fondo oscuro, QR, nombre,
# puntos y nota) para descargar/compartir como imagen.
import io
import math
import textwrap

import qrcode
from PIL import Image, ImageDraw, ImageFont

W, H = 800, 1150
CARD = (70, 60, 730, 1090)
AMARILLO = (255, 193, 7)
BLANCO = (255, 255, 255)
GRIS = (185, 185, 200)


def _font(size, bold=False):
    candidatos = [
        r'C:\Windows\Fonts\arialbd.ttf' if bold else r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\segoeuib.ttf' if bold else r'C:\Windows\Fonts\segoeui.ttf',
        'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
    ]
    for path in candidatos:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _gradiente():
    grad = Image.new('RGB', (1, H))
    d = ImageDraw.Draw(grad)
    top, bot = (26, 26, 46), (22, 33, 62)
    for y in range(H):
        t = y / H
        d.point((0, y), fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return grad.resize((W, H))


def _center(draw, y, texto, font, fill):
    bbox = draw.textbbox((0, 0), texto, font=font)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, y), texto, font=font, fill=fill)
    return bbox[3] - bbox[1]


def _bloque(draw, y, texto, font, fill, ancho):
    """Escribe texto centrado en varias líneas; devuelve la y siguiente."""
    for linea in textwrap.wrap(texto, width=ancho) or ['']:
        h = _center(draw, y, linea, font, fill)
        y += h + 12
    return y


def _star(cx, cy, r):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _icono_qr(draw, cx, cy):
    """Mini glifo tipo bi-qr-code: tres marcos amarillos."""
    s, g, lw = 22, 8, 4
    for dx, dy in [(-1.5 * (s + g), -s / 2 - g), (s / 2 + g / 2, -s / 2 - g), (-1.5 * (s + g), s / 2 + g)]:
        x0, y0 = cx + dx, cy + dy
        draw.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=4, outline=AMARILLO, width=lw)
        draw.rectangle([x0 + 7, y0 + 7, x0 + s - 7, y0 + s - 7], fill=AMARILLO)
    draw.rectangle([cx + s / 2 + g, cy + s / 2 + g, cx + s / 2 + g + 12, cy + s / 2 + g + 12], fill=AMARILLO)


def build_card_png(titulo, subtitulo, puntos, url):
    """Devuelve BytesIO con el PNG del recuadro de puntos completo."""
    img = _gradiente().convert('RGBA')

    # Tarjeta translúcida con borde (rgba(255,255,255,0.08) + borde 0.15)
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(CARD, radius=38, fill=(255, 255, 255, 20),
                         outline=(255, 255, 255, 38), width=2)
    img.alpha_composite(overlay)
    draw = ImageDraw.Draw(img)

    _icono_qr(draw, W // 2, 130)
    y = _bloque(draw, 185, titulo or '', _font(44, bold=True), BLANCO, 24)
    if subtitulo:
        y = _bloque(draw, y + 4, subtitulo, _font(26), GRIS, 36)

    # QR sobre tarjeta blanca redondeada
    qr = qrcode.make(url, box_size=10, border=2).convert('RGB').resize((430, 430))
    qx, qy = (W - 430) // 2, y + 18
    draw.rounded_rectangle([qx - 22, qy - 22, qx + 452, qy + 452], radius=24, fill=BLANCO)
    img.paste(qr, (qx, qy))
    y = qy + 474

    if puntos:
        star = _star(0, 0, 20)
        texto = f'{puntos} puntos'
        f_pts = _font(38, bold=True)
        tw = draw.textbbox((0, 0), texto, font=f_pts)[2]
        sx = (W - (tw + 44)) / 2
        draw.polygon([(px + sx + 18, py + y + 22) for px, py in star], fill=AMARILLO)
        draw.text((sx + 44, y), texto, font=f_pts, fill=AMARILLO)
        y += 62

    _bloque(draw, y + 10, 'Presentá este código al ingresar a la actividad para registrar tu participación.',
            _font(21), GRIS, 42)

    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='PNG')
    buf.seek(0)
    return buf
