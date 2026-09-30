# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# (datos estáticos en holidays_data.py, CRUD custom en holidays_admin.py)
from datetime import date
import json
from db import db
from models_core import Holiday, BackgroundMusic
from helpers.holidays_data import (nth_weekday, HOLIDAYS, _DEFAULT_CONFETTI,
                                   MUSIC_DIR, list_music_files)


_UNSET = object()


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
        'autoplay': row.autoplay,
        'show_confetti': row.show_confetti if row.show_confetti is not None else True,
        'custom_message': row.custom_message or '',
        'show_player': row.show_player if row.show_player is not None else True,
        'end_month': row.end_month,
        'end_day': row.end_day,
        'superuser_only': row.superuser_only if row.superuser_only is not None else False,
        'link_url': row.link_url or '',
        'link_enabled': row.link_enabled if row.link_enabled is not None else False,
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
                autoplay=False,
                show_confetti=True,
                custom_message='',
                show_player=True,
                end_month=None,
                end_day=None,
                superuser_only=False,
                link_url='',
                link_enabled=False,
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


def update_holiday_override(holiday_id, enabled=None, autoplay=None, show_confetti=None, custom_message=_UNSET, show_player=None, end_month=None, end_day=None, superuser_only=None, link_url=_UNSET, link_enabled=None, title=None, subtitle=None, icon=None, song=_UNSET):
    """Actualiza un feriado en la base de datos. Campos con _UNSET se ignoran."""
    _ensure_base_holidays()
    row = Holiday.query.get(holiday_id)
    if not row:
        return None
    if enabled is not None:
        row.enabled = bool(enabled)
    if autoplay is not None:
        row.autoplay = bool(autoplay)
    if show_confetti is not None:
        row.show_confetti = bool(show_confetti)
    if custom_message is not _UNSET:
        row.custom_message = str(custom_message).strip() or None
    if show_player is not None:
        row.show_player = bool(show_player)
    if end_month is not None:
        row.end_month = int(end_month) if end_month else None
    if end_day is not None:
        row.end_day = int(end_day) if end_day else None
    if superuser_only is not None:
        row.superuser_only = bool(superuser_only)
    if link_url is not _UNSET:
        row.link_url = str(link_url).strip() or None
    if link_enabled is not None:
        row.link_enabled = bool(link_enabled)
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


def _is_in_holiday_range(today, month, day, end_month, end_day):
    """Retorna True si hoy cae dentro del rango de fechas."""
    if end_month is None or end_day is None:
        return today.month == month and today.day == day
    year = today.year
    start = date(year, month, day)
    end = date(year, end_month, end_day)
    if end < start:
        end = date(year + 1, end_month, end_day)
    return start <= today <= end


def get_today_holiday(today):
    """Retorna el dict del feriado activo que corresponde a la fecha dada, o None."""
    _ensure_base_holidays()
    for row in Holiday.query.filter_by(enabled=True).all():
        h = _holiday_to_dict(row)
        if h.get('day') is not None:
            if _is_in_holiday_range(today, h['month'], h['day'], h.get('end_month'), h.get('end_day')):
                return h
        if h.get('nth_weekday') and today == nth_weekday(today.year, h['month'], h['nth_weekday'][1], h['nth_weekday'][0]):
            return h
    return None


def _music_to_dict(row):
    return {
        'id': row.id,
        'enabled': row.enabled,
        'songs': json.loads(row.songs) if row.songs else [],
        'random': row.random,
    }


def get_background_music():
    """Retorna la configuración de música de fondo."""
    row = BackgroundMusic.query.filter_by(id=1).first()
    if not row:
        row = BackgroundMusic(id=1, enabled=False, songs='[]', random=True)
        db.session.add(row)
        db.session.commit()
    return _music_to_dict(row)


def update_background_music(enabled=None, songs=None, random=None):
    """Actualiza la configuración de música de fondo."""
    row = BackgroundMusic.query.filter_by(id=1).first()
    if not row:
        row = BackgroundMusic(id=1)
        db.session.add(row)
    if enabled is not None:
        row.enabled = bool(enabled)
    if songs is not None:
        row.songs = json.dumps(songs)
    if random is not None:
        row.random = bool(random)
    db.session.commit()
    return _music_to_dict(row)
