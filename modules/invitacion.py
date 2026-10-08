# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/invitacion.py - Invitación personalizada 9:16 (PNG).
# Flyer del evento de fondo + datos de la persona y puntos.
import io
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NARANJA = (255, 140, 0)
BLANCO = (255, 255, 255)
BASE = os.path.dirname(os.path.dirname(__file__))


def _font(size, bold=False):
    for path in [
        r'C:\Windows\Fonts\arialbd.ttf' if bold else r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\segoeuib.ttf' if bold else r'C:\Windows\Fonts\segoeui.ttf',
        'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _center(draw, y, texto, font, fill):
    bb = draw.textbbox((0, 0), texto, font=font)
    draw.text(((W - (bb[2] - bb[0])) / 2, y), texto, font=font, fill=fill)
    return bb[3] - bb[1]


def _wrap(draw, texto, font, ancho):
    lineas, actual = [], ''
    for pal in (texto or '').split():
        prueba = (actual + ' ' + pal).strip()
        bb = draw.textbbox((0, 0), prueba, font=font)
        if bb[2] - bb[0] <= ancho or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = pal
    if actual:
        lineas.append(actual)
    return lineas


def _flyer_path(event):
    for nombre in [event.flyer_bg, event.poster]:
        if nombre:
            p = os.path.join(BASE, 'static', 'uploads', nombre)
            if os.path.exists(p):
                return p
        if nombre:
            p = os.path.join(BASE, 'static', nombre)
            if os.path.exists(p):
                return p
    return None


def _cover(img, ancho, alto):
    """Recorta la imagen al centro cubriendo ancho x alto."""
    ratio = max(ancho / img.width, alto / img.height)
    img = img.resize((int(img.width * ratio + .5), int(img.height * ratio + .5)))
    x = (img.width - ancho) // 2
    y = (img.height - alto) // 3  # sesgo hacia arriba para no cortar caras
    return img.crop((x, y, x + ancho, y + alto))


def build_invitacion_image(event, hiker):
    """PNG 9:16: flyer del evento + invitación personalizada."""
    img = Image.new('RGB', (W, H), (18, 18, 24))
    flyer = _flyer_path(event)
    if flyer:
        try:
            f = Image.open(flyer).convert('RGB')
            img.paste(_cover(f, W, H), (0, 0))
        except (OSError, IOError):
            pass

    # Banda oscura inferior: los flyers ya traen su propio texto,
    # así que el mensaje va sobre una base casi opaca y legible.
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    y0 = int(H * 0.58)
    for y in range(y0, H):
        a = min(250, int(255 * (y - y0) / 150))
        od.line([(0, y), (W, y)], fill=(10, 10, 16, a))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # Marca
    try:
        logo = Image.open(os.path.join(BASE, 'static', 'logo.png')).convert('RGBA')
        r = 76 / logo.height
        logo = logo.resize((int(logo.width * r), 76))
        img.paste(logo, ((W - logo.width) // 2, y0 - 96), logo)
        draw = ImageDraw.Draw(img)
    except (OSError, IOError):
        pass

    y = y0 + 16
    y += _center(draw, y, '¡ESTÁS INVITADO(A)!', _font(56, bold=True), NARANJA) + 26
    nombre = (hiker.nombre_completo or '').strip() if hiker else ''
    for ln in _wrap(draw, nombre, _font(58, bold=True), W - 120):
        y += _center(draw, y, ln, _font(58, bold=True), BLANCO) + 10
    y += 18
    for ln in _wrap(draw, event.nombre_lugar or '', _font(44, bold=True), W - 140)[:2]:
        y += _center(draw, y, ln, _font(44, bold=True), (255, 205, 130)) + 8

    detalle = ' · '.join(x for x in [
        getattr(event, 'fecha_unica', None) or getattr(event, 'fecha_inicio', None) or '',
        getattr(event, 'lugar_salida', None) or '',
        getattr(event, 'provincia', None) or ''] if x)
    if detalle:
        for ln in _wrap(draw, detalle, _font(30), W - 160)[:2]:
            y += _center(draw, y + 4, ln, _font(30), (215, 215, 225)) + 4

    # Badge de puntos
    pts = getattr(event, 'puntos', 0) or 0
    if pts > 0:
        y += 34
        txt = f'Ganá {pts} puntos al participar'
        f_p = _font(36, bold=True)
        bb = draw.textbbox((0, 0), txt, font=f_p)
        pw = bb[2] - bb[0]
        x0 = (W - pw) / 2 - 34
        draw.rounded_rectangle([x0, y - 12, x0 + pw + 68, y + 60], radius=36, fill=NARANJA)
        draw.text((x0 + 34, y), txt, font=f_p, fill=BLANCO)
        y += 96

    _center(draw, H - 72, 'latribu.top', _font(24, bold=True), (200, 200, 210))
    return img


def invitacion_bytes(img):
    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='PNG')
    buf.seek(0)
    return buf
