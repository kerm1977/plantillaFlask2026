from datetime import date, timedelta
import json
import os
from db import db
from models_core import Holiday


_UNSET = object()


def nth_weekday(year, month, weekday, n):
    """Devuelve el n-ésimo día de la semana del mes (n empieza en 1).
    weekday: 0=lunes, 6=domingo
    """
    first = date(year, month, 1)
    delta = (weekday - first.weekday() + 7) % 7
    return first + timedelta(days=delta + (n - 1) * 7)


HOLIDAYS = [
    {
        'id': 'mothers_day',
        'month': 8,
        'day': 15,
        'title': '¡Feliz Día de la Madre!',
        'subtitle': 'A todas las madres de Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '🌹',
        'confetti_colors': ['#ff69b4', '#ffc107', '#ff4081', '#ffd700', '#ffffff'],
        'song': 'DIA DE LA MADRE.mp3',
    },
    {
        'id': 'new_year',
        'month': 1,
        'day': 1,
        'title': '¡Feliz Año Nuevo!',
        'subtitle': 'Te lo desea La Tribu de Los Libres',
        'emoji': '🎉',
        'confetti_colors': ['#ff69b4', '#ffc107', '#00bcd4', '#4caf50', '#ff4081'],
    },
    {
        'id': 'new_years_eve',
        'month': 12,
        'day': 31,
        'title': '¡Feliz Fin de Año!',
        'subtitle': 'Te lo desea La Tribu de Los Libres',
        'emoji': '🥂',
        'confetti_colors': ['#ffd700', '#ffffff', '#ff4081', '#00bcd4', '#4caf50'],
    },
    {
        'id': 'fathers_day',
        'month': 6,
        'nth_weekday': (3, 6),  # tercer domingo de junio
        'title': '¡Feliz Día del Padre!',
        'subtitle': 'A todos los padres de Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '👔',
        'confetti_colors': ['#1e88e5', '#4caf50', '#ffc107', '#8d6e63', '#ffffff'],
        'song': 'PADRES DE LA TRIBU.mp3',
    },
    {
        'id': 'childrens_day',
        'month': 6,
        'day': 1,
        'title': '¡Feliz Día del Niño!',
        'subtitle': 'A todos los niños de Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '🎈',
        'confetti_colors': ['#ff69b4', '#00bcd4', '#ffeb3b', '#4caf50', '#ff9800'],
    },
    {
        'id': 'parks_day',
        'month': 8,
        'day': 24,
        'title': '¡Feliz Día de los Parques Nacionales!',
        'subtitle': 'Celebremos nuestra naturaleza, La Tribu de Los Libres',
        'emoji': '🌲',
        'confetti_colors': ['#2e7d32', '#66bb6a', '#ffffff', '#8d6e63'],
    },
    {
        'id': 'independence',
        'month': 9,
        'day': 15,
        'title': '¡Feliz Día de la Independencia!',
        'subtitle': 'Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '🇨🇷',
        'confetti_colors': ['#002b7f', '#ffffff', '#ce1126'],
        'background': 'rgba(0, 43, 127, 0.12)',
        'border': 'rgba(0, 43, 127, 0.4)',
    },
    {
        'id': 'christmas',
        'month': 12,
        'day': 25,
        'title': '¡Feliz Navidad!',
        'subtitle': 'Te lo desea La Tribu de Los Libres',
        'emoji': '🎄',
        'confetti_colors': ['#ff0000', '#00ff00', '#ffffff', '#ffd700'],
    },
]


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_OVERRIDE_FILE = os.path.join(_PROJECT_ROOT, 'data', 'holidays.json')
MUSIC_DIR = os.path.join(_PROJECT_ROOT, 'static', 'musica')


def list_music_files():
    """Retorna la lista de archivos de música disponibles."""
    if not os.path.isdir(MUSIC_DIR):
        return []
    return sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))])


def _load_overrides():
    if not os.path.exists(_OVERRIDE_FILE):
        return {}
    try:
        with open(_OVERRIDE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_overrides(overrides):
    os.makedirs(os.path.dirname(_OVERRIDE_FILE), exist_ok=True)
    with open(_OVERRIDE_FILE, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)


_CUSTOM_FILE = os.path.join(_PROJECT_ROOT, 'data', 'custom_holidays.json')


def _load_custom_holidays():
    if not os.path.exists(_CUSTOM_FILE):
        return []
    try:
        with open(_CUSTOM_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_custom_holidays(holidays):
    os.makedirs(os.path.dirname(_CUSTOM_FILE), exist_ok=True)
    with open(_CUSTOM_FILE, 'w', encoding='utf-8') as f:
        json.dump(holidays, f, ensure_ascii=False, indent=2)


def _holiday_matches(h, today):
    if 'day' in h:
        return today.month == h['month'] and today.day == h['day']
    if 'nth_weekday' in h:
        n, weekday = h['nth_weekday']
        return today == nth_weekday(today.year, h['month'], weekday, n)
    return False


def _apply_override(h, overrides):
    result = dict(h)
    ov = overrides.get(h['id'], {})
    result['enabled'] = bool(ov.get('enabled', True))
    if ov.get('title'):
        result['title'] = ov['title']
    if ov.get('subtitle'):
        result['subtitle'] = ov['subtitle']
    if ov.get('icon'):
        result['icon'] = ov['icon']
    if 'song' in ov:
        if ov['song']:
            result['song'] = ov['song']
        elif 'song' in result:
            del result['song']
    return result


_DEFAULT_CONFETTI = ['#ff69b4', '#ffc107', '#00bcd4', '#4caf50', '#ff4081']


def _holiday_to_dict(row):
    result = {
        'id': row.id,
        'month': row.month,
        'day': row.day,
        'title': row.title,
        'subtitle': row.subtitle or '',
        'icon': row.icon or '',
        'confetti_colors': json.loads(row.confetti_colors) if row.confetti_colors else list(_DEFAULT_CONFETTI),
        'song': row.song or '',
        'enabled': row.enabled,
        'custom': row.is_custom,
    }
    if row.nth_weekday_n is not None and row.nth_weekday_weekday is not None:
        result['nth_weekday'] = (row.nth_weekday_n, row.nth_weekday_weekday)
    if row.background:
        result['background'] = row.background
    if row.border:
        result['border'] = row.border
    if result['song'] == '':
        del result['song']
    return result


def _ensure_base_holidays():
    """Inserta los feriados base en la base de datos si aún no existen."""
    existing = {h.id for h in Holiday.query.filter_by(is_custom=False).all()}
    added = False
    for h in HOLIDAYS:
        if h['id'] not in existing:
            row = Holiday(
                id=h['id'],
                month=h['month'],
                day=h.get('day'),
                nth_weekday_n=h.get('nth_weekday', [None, None])[0] if h.get('nth_weekday') else None,
                nth_weekday_weekday=h.get('nth_weekday', [None, None])[1] if h.get('nth_weekday') else None,
                title=h['title'],
                subtitle=h.get('subtitle', ''),
                icon=h.get('emoji') or h.get('icon', ''),
                confetti_colors=json.dumps(h.get('confetti_colors', _DEFAULT_CONFETTI)),
                song=h.get('song', ''),
                enabled=True,
                is_custom=False,
                background=h.get('background'),
                border=h.get('border'),
            )
            db.session.add(row)
            added = True
    if added:
        db.session.commit()


def get_all_holidays():
    """Retorna todos los feriados desde la base de datos."""
    _ensure_base_holidays()
    return [_holiday_to_dict(h) for h in Holiday.query.order_by(Holiday.month, Holiday.day).all()]


def get_holiday(holiday_id):
    """Retorna un feriado específico, o None."""
    _ensure_base_holidays()
    row = Holiday.query.get(holiday_id)
    return _holiday_to_dict(row) if row else None


def update_holiday_override(holiday_id, enabled=None, title=None, subtitle=None, icon=None, song=_UNSET):
    """Actualiza un feriado en la base de datos. Campos con _UNSET se ignoran."""
    _ensure_base_holidays()
    row = Holiday.query.get(holiday_id)
    if not row:
        return None
    if enabled is not None:
        row.enabled = bool(enabled)
    if title is not None:
        row.title = str(title).strip()
    if subtitle is not None:
        row.subtitle = str(subtitle).strip() or None
    if icon is not None:
        row.icon = str(icon).strip() or None
    if song is not _UNSET:
        row.song = str(song).strip() or None
    db.session.commit()
    return _holiday_to_dict(row)


def get_today_holiday(today):
    """Retorna el dict del feriado activo que corresponde a la fecha dada, o None."""
    _ensure_base_holidays()
    for row in Holiday.query.filter_by(enabled=True).all():
        h = _holiday_to_dict(row)
        if h.get('day') is not None and today.month == h['month'] and today.day == h['day']:
            return h
        if h.get('nth_weekday') and today == nth_weekday(today.year, h['month'], h['nth_weekday'][1], h['nth_weekday'][0]):
            return h
    return None


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
