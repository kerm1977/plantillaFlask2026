# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/points_helpers.py - Helpers para el motor de puntos
from datetime import datetime, date
import hashlib
import hmac as _hmac


def descargar_token(cedula):
    """Token firmado (HMAC) para enlaces de descarga del carnet/estado de cuenta.
    Permite descargar aunque la sesión haya expirado o la página venga del caché PWA."""
    from flask import current_app
    secret = (current_app.config.get('SECRET_KEY') or 'dev-secret-change-me').encode()
    return _hmac.new(secret, ('dl:' + str(cedula)).encode(), hashlib.sha256).hexdigest()[:32]


def token_descarga_ok(cedula, token):
    return bool(token) and _hmac.compare_digest(str(token), descargar_token(cedula))


def build_estado_cuenta_whatsapp(cedula, hiker=None, plain=False):
    """Estado de cuenta de puntos para WhatsApp (reutilizable). plain=True: sin marcas de formato (TXT)."""
    from modules.points_engine import get_points_engine
    engine = get_points_engine()
    b = (lambda s: s) if plain else (lambda s: f'*{s}*')
    i = (lambda s: s) if plain else (lambda s: f'_{s}_')
    sep = '-' * 30
    history = engine.history_with_names(cedula)
    ganados = sum(r['puntos'] for r in history if r['puntos'] > 0)
    usados = -sum(r['puntos'] for r in history if r['puntos'] < 0)
    lines = [b('ESTADO DE CUENTA DE PUNTOS'), i('La Tribu de los Libres'), sep,
             f'{b("Nombre:")} {hiker.nombre_completo if hiker else ""}', f'{b("Cédula:")} {cedula}',
             b(f'TOTAL: {engine.total_by_cedula(cedula)} puntos'),
             f'Ganados: {ganados} | Usados: {usados}',
             f'Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}', sep, b('MOVIMIENTOS')]
    for row in history:
        f = (row.get('creado_at') or '')[:10]
        f = f'{f[8:10]}/{f[5:7]}/{f[0:4]}' if len(f) == 10 else 'Sin fecha'
        actividad = row.get('evento_nombre') or (row.get('tipo') or '').replace('_', ' ').capitalize()
        pts = f'{row.get("puntos", 0):+d}'
        lines.append(f'{f} | {actividad} | {b(pts)}')
        if row.get('detalle'):
            lines.append(f'   {i(row["detalle"])}')
    if not history:
        lines.append('Sin movimientos registrados.')
    return '\n'.join(lines)


def is_past_event(event):
    today = date.today()
    for attr in ('fecha_unica', 'fecha_inicio', 'fecha_regreso'):
        val = getattr(event, attr, None)
        if not val:
            continue
        try:
            parsed = datetime.strptime(val.strip(), '%Y-%m-%d').date()
            if parsed < today:
                return True
        except (ValueError, AttributeError):
            continue
    return False


def get_puntos_password():
    from models import SiteContent
    row = SiteContent.query.filter_by(key='puntos_global_password').first()
    return row.value if row else ''


def set_puntos_password(value):
    from db import db
    from models import SiteContent
    row = SiteContent.query.filter_by(key='puntos_global_password').first()
    if row:
        row.value = value
    else:
        db.session.add(SiteContent(key='puntos_global_password', value=value))
    db.session.commit()


def get_puntos_admin_visible():
    from models import SiteContent
    row = SiteContent.query.filter_by(key='puntos_admin_pwd_visible').first()
    return row.value == '1' if row else True


def set_puntos_admin_visible(visible):
    from db import db
    from models import SiteContent
    row = SiteContent.query.filter_by(key='puntos_admin_pwd_visible').first()
    val = '1' if visible else '0'
    if row:
        row.value = val
    else:
        db.session.add(SiteContent(key='puntos_admin_pwd_visible', value=val))
    db.session.commit()


def get_notif_cutoff(cedula):
    from models import SiteContent
    row = SiteContent.query.filter_by(key='notif_cleared_' + cedula).first()
    return row.value if row else ''


def set_notif_cleared(cedula):
    from db import db
    from models import SiteContent
    key = 'notif_cleared_' + cedula
    row = SiteContent.query.filter_by(key=key).first()
    if row:
        row.value = datetime.utcnow().isoformat()
    else:
        db.session.add(SiteContent(key=key, value=datetime.utcnow().isoformat()))
    db.session.commit()
