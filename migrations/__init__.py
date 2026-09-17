

from .raffle import _migrate_raffle_selection
from .user import _migrate_user_reset
from .publicacion import _migrate_publicacion
from .forms import _migrate_forms_ficha_medica, _migrate_forms_pasaporte_fecha_nacimiento
from .hiker import _migrate_hiker_pasaporte, _migrate_hiker_card_email
from .form_response import _migrate_form_response_reservation_number
from .cotizador import _migrate_cotizador
from .event import _migrate_event_date_changes, _migrate_event_enlace_extra, _migrate_event_texto_referencia, _migrate_event_visitado, _migrate_visitado_to_estados, _migrate_event_zona_alto_riesgo, _migrate_event_tipo_terreno, _migrate_event_kilometros, _migrate_event_tipo_caminata, _migrate_event_precio_buseta
from .payment_methods import _seed_payment_methods
from .notes import _migrate_notes
from .holidays import _migrate_holidays_autoplay
from .background_music import _migrate_background_music
from .points import _migrate_event_puntos, _migrate_hiker_points


def run_migrations():
    """Ejecuta todas las migraciones manuales."""
    _migrate_raffle_selection()
    _migrate_user_reset()
    _migrate_publicacion()
    _migrate_forms_ficha_medica()
    _migrate_forms_pasaporte_fecha_nacimiento()
    _migrate_hiker_pasaporte()
    _migrate_hiker_card_email()
    _migrate_form_response_reservation_number()
    _migrate_cotizador()
    _migrate_event_date_changes()
    _migrate_event_enlace_extra()
    _migrate_event_texto_referencia()
    _migrate_event_visitado()
    _migrate_visitado_to_estados()
    _migrate_event_zona_alto_riesgo()
    _migrate_event_tipo_terreno()
    _migrate_event_kilometros()
    _migrate_event_tipo_caminata()
    _migrate_event_precio_buseta()
    _seed_payment_methods()
    _migrate_notes()
    _migrate_holidays_autoplay()
    _migrate_background_music()
    _migrate_event_puntos()
    _migrate_hiker_points()

