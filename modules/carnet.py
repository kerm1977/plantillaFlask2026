# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/carnet.py - Carnet de identificación con QR (PNG/JPG/PDF).
# La persona lo descarga desde Mis puntos y lo presenta en actividades.
# El QR apunta a su tarjeta pública (/tarjeta/<cedula>/<email>).
import io
import os
import secrets
import textwrap

import qrcode
from PIL import Image, ImageDraw, ImageFont

W, H = 800, 1180
NARANJA = (255, 140, 0)
OSCURO = (30, 30, 40)
GRIS = (110, 110, 125)
BLANCO = (255, 255, 255)


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


def _center(draw, y, texto, font, fill):
    bbox = draw.textbbox((0, 0), texto, font=font)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, y), texto, font=font, fill=fill)
    return bbox[3] - bbox[1]


def _bloque(draw, y, texto, font, fill, ancho):
    for linea in textwrap.wrap(texto, width=ancho) or ['']:
        h = _center(draw, y, linea, font, fill)
        y += h + 10
    return y


def ensure_card_email(hiker):
    """El QR necesita la URL de la tarjeta, que exige card_email.
    Si el hiker no tiene, se le asigna un token (igual que en admin_actions)."""
    if not (hiker.card_email or '').strip():
        from db import db
        hiker.card_email = secrets.token_hex(8)
        db.session.commit()
    return hiker.card_email.strip().lower()


def build_carnet_image(hiker, puntos, tarjeta_url):
    """Devuelve un PIL Image RGB del carnet."""
    img = Image.new('RGB', (W, H), (247, 248, 250))
    draw = ImageDraw.Draw(img)

    # Banda superior naranja con logo y nombre de la organización
    draw.rectangle([0, 0, W, 210], fill=NARANJA)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo.png')
    try:
        logo = Image.open(logo_path).convert('RGBA')
        ratio = 110 / logo.height
        logo = logo.resize((int(logo.width * ratio), 110))
        img.paste(logo, ((W - logo.width) // 2, 18), logo)
        y = 140
    except (OSError, IOError):
        y = 60
    _center(draw, y, 'LA TRIBU DE LOS LIBRES', _font(30, bold=True), BLANCO)
    _center(draw, y + 44, 'CARNET DE MIEMBRO', _font(19, bold=True), (255, 240, 215))

    # Datos de la persona
    y = _bloque(draw, 235, hiker.nombre_completo or '', _font(40, bold=True), OSCURO, 26)
    y = _center(draw, y + 6, f'Cédula: {hiker.cedula}', _font(28), GRIS) + y + 6

    fila_y = y + 18
    if hiker.tipo_sangre:
        sangre = f'Sangre: {hiker.tipo_sangre}'
        f_s = _font(24, bold=True)
        bb = draw.textbbox((0, 0), sangre, font=f_s)
        tw = bb[2] - bb[0]
        x0 = (W - tw) / 2 - 22
        draw.rounded_rectangle([x0, fila_y - 10, x0 + tw + 44, fila_y + 48], radius=24, fill=(220, 53, 69))
        draw.text((x0 + 22, fila_y), sangre, font=f_s, fill=BLANCO)
        fila_y += 70
    if hiker.telefono:
        fila_y += _center(draw, fila_y, f'Tel: {hiker.telefono}', _font(24), GRIS) + 12
    emerg = ' · '.join(x for x in [hiker.contacto_emergencia_nombre, hiker.contacto_emergencia_telefono] if x)
    if emerg:
        fila_y = _bloque(draw, fila_y + 4, f'Emergencia: {emerg}', _font(22), (180, 60, 60), 44) + 6

    # QR sobre tarjeta blanca
    qr = qrcode.make(tarjeta_url, box_size=10, border=2).convert('RGB').resize((390, 390))
    qx, qy = (W - 390) // 2, fila_y + 14
    if qy + 434 > H - 130:
        qy = H - 130 - 434
    draw.rounded_rectangle([qx - 20, qy - 20, qx + 410, qy + 410], radius=22, fill=BLANCO, outline=(225, 225, 230), width=2)
    img.paste(qr, (qx, qy))

    # Puntos y pie
    texto_pts = f'{puntos} puntos'
    f_p = _font(38, bold=True)
    bb = draw.textbbox((0, 0), texto_pts, font=f_p)
    draw.text(((W - (bb[2] - bb[0])) / 2, qy + 432), texto_pts, font=f_p, fill=NARANJA)
    _bloque(draw, H - 118, 'Presentá este carnet para identificarte en las actividades.',
            _font(21), GRIS, 46)
    draw.rectangle([0, H - 24, W, H], fill=NARANJA)
    _center(draw, H - 19, 'latribu.top', _font(13, bold=True), BLANCO)
    return img


def carnet_bytes(img, fmt):
    """Convierte la imagen a bytes en png, jpg o pdf."""
    buf = io.BytesIO()
    rgb = img.convert('RGB')
    if fmt == 'jpg':
        rgb.save(buf, format='JPEG', quality=95)
        mime, ext = 'image/jpeg', 'jpg'
    elif fmt == 'pdf':
        rgb.save(buf, format='PDF', resolution=150.0)
        mime, ext = 'application/pdf', 'pdf'
    else:
        rgb.save(buf, format='PNG')
        mime, ext = 'image/png', 'png'
    buf.seek(0)
    return buf, mime, ext
