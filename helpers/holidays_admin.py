# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""CRUD de feriados personalizados (admin)."""
import json
from db import db
from models_core import Holiday
from helpers.holidays_data import _DEFAULT_CONFETTI
from helpers.holidays import _ensure_base_holidays, _holiday_to_dict


def _slugify(text):
    text = str(text).strip().lower()
    import unicodedata
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('ñ', 'n').replace(' ', '_')
    text = ''.join(c if c.isalnum() or c == '_' else '_' for c in text)
    return text.rstrip('_') or 'custom'


def _custom_exists(holiday_id):
    return Holiday.query.filter_by(id=holiday_id).first() is not None


def _base_exists(holiday_id):
    return Holiday.query.filter_by(id=holiday_id, is_custom=False).first() is not None


def _generate_custom_id(title):
    base = _slugify(title)
    if not _custom_exists(base) and not _base_exists(base):
        return base
    n = 2
    while _custom_exists(f'{base}_{n}') or _base_exists(f'{base}_{n}'):
        n += 1
    return f'{base}_{n}'


def _normalize_to_row(data, holiday_id, is_custom=True, existing=None):
    row = existing or Holiday()
    row.id = holiday_id
    row.is_custom = is_custom
    row.month = int(data.get('month', 1))
    row.day = int(data.get('day', 1)) if data.get('day') is not None else None
    row.title = str(data.get('title', '')).strip()
    row.subtitle = str(data.get('subtitle', '')).strip() or None
    row.icon = str(data.get('icon', '🎉')).strip()
    colors = data.get('confetti_colors') or list(_DEFAULT_CONFETTI)
    row.confetti_colors = json.dumps(colors)
    row.enabled = bool(data.get('enabled', True))
    if 'autoplay' in data:
        row.autoplay = str(data['autoplay']).strip().lower() in ('true', '1', 'on')
    if 'show_confetti' in data:
        row.show_confetti = str(data['show_confetti']).strip().lower() in ('true', '1', 'on')
    if 'custom_message' in data:
        row.custom_message = str(data['custom_message']).strip() or None
    if 'show_player' in data:
        row.show_player = str(data['show_player']).strip().lower() in ('true', '1', 'on')
    if 'end_month' in data and data['end_month']:
        row.end_month = int(data['end_month'])
    else:
        row.end_month = None
    if 'end_day' in data and data['end_day']:
        row.end_day = int(data['end_day'])
    else:
        row.end_day = None
    if 'superuser_only' in data:
        row.superuser_only = str(data['superuser_only']).strip().lower() in ('true', '1', 'on')
    if 'link_url' in data:
        row.link_url = str(data['link_url']).strip() or None
    if 'link_enabled' in data:
        row.link_enabled = str(data['link_enabled']).strip().lower() in ('true', '1', 'on')
    row.song = str(data.get('song', '')).strip() or None
    row.nth_weekday_n = None
    row.nth_weekday_weekday = None
    if data.get('nth_weekday'):
        row.nth_weekday_n = int(data['nth_weekday'][0])
        row.nth_weekday_weekday = int(data['nth_weekday'][1])
    return row


def create_custom_holiday(data):
    _ensure_base_holidays()
    holiday_id = _generate_custom_id(data.get('title', 'custom'))
    row = _normalize_to_row(data, holiday_id, is_custom=True)
    db.session.add(row)
    db.session.commit()
    return _holiday_to_dict(row)


def update_custom_holiday(holiday_id, data):
    _ensure_base_holidays()
    row = Holiday.query.get(holiday_id)
    if not row:
        return None
    row = _normalize_to_row(data, holiday_id, is_custom=True, existing=row)
    db.session.commit()
    return _holiday_to_dict(row)


def delete_custom_holiday(holiday_id):
    _ensure_base_holidays()
    row = Holiday.query.get(holiday_id)
    if not row:
        return False
    db.session.delete(row)
    db.session.commit()
    return True
