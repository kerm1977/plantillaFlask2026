

from .raffle import _migrate_raffle_selection
from .user import _migrate_user_reset
from .publicacion import _migrate_publicacion
from .forms import _migrate_forms_ficha_medica, _migrate_forms_pasaporte_fecha_nacimiento
from .hiker import _migrate_hiker_pasaporte
from .form_response import _migrate_form_response_reservation_number
from .cotizador import _migrate_cotizador
from .event import _migrate_event_date_changes, _migrate_event_enlace_extra, _migrate_event_texto_referencia
from .notes import _migrate_notes
from .holidays import _migrate_holidays_autoplay
from .background_music import _migrate_background_music


def run_migrations():
    """Ejecuta todas las migraciones manuales."""
    _migrate_raffle_selection()
    _migrate_user_reset()
    _migrate_publicacion()
    _migrate_forms_ficha_medica()
    _migrate_forms_pasaporte_fecha_nacimiento()
    _migrate_hiker_pasaporte()
    _migrate_form_response_reservation_number()
    _migrate_cotizador()
    _migrate_event_date_changes()
    _migrate_event_enlace_extra()
    _migrate_event_texto_referencia()
    _migrate_notes()
    _migrate_holidays_autoplay()
    _migrate_background_music()

