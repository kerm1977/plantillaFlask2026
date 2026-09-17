# modules/points_helpers.py - Helpers para el motor de puntos
from datetime import datetime, date


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
