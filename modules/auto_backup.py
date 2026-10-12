# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/auto_backup.py — Respaldo automático de TODA la base de datos
# en JSON cada 48 horas. Se guarda en backups/json_auto/ y conserva
# los últimos 20 archivos. El estado (último/próximo respaldo) se
# expone para el reloj de la sección de puntos.
import os
import json
import time
from datetime import datetime, timedelta

INTERVAL = timedelta(hours=48)
_CHECK_SECONDS = 300          # revisa cada 5 min si ya toca respaldar
_KEEP = 20                    # conserva los últimos N respaldos
_DIR_NAME = os.path.join('backups', 'json_auto')
_STATE_FILE = 'estado.json'


def _dir():
    from routes import _PROJECT_ROOT
    return os.path.join(_PROJECT_ROOT, _DIR_NAME)


def _state_path():
    return os.path.join(_dir(), _STATE_FILE)


def _read_state():
    try:
        with open(_state_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write_state(state):
    os.makedirs(_dir(), exist_ok=True)
    with open(_state_path(), 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def ultimo_respaldo():
    """datetime del último respaldo automático (o None)."""
    ts = _read_state().get('ultimo')
    if ts:
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return None
    return None


def proximo_respaldo():
    """datetime del próximo respaldo programado."""
    ult = ultimo_respaldo()
    return (ult + INTERVAL) if ult else datetime.now()


def estado():
    ult = ultimo_respaldo()
    return {
        'ultimo': ult.isoformat() if ult else None,
        'proximo': proximo_respaldo().isoformat(),
        'archivos': sorted(f for f in os.listdir(_dir())
                           if f.startswith('db_auto_') and f.endswith('.json'))
        if os.path.isdir(_dir()) else []
    }


def ejecutar_respaldo(app):
    """Genera el JSON completo de la BD ahora. Devuelve el nombre del archivo."""
    with app.app_context():
        from routes.db_export import _db_payload
        payload = _db_payload()
        payload['auto'] = True
        os.makedirs(_dir(), exist_ok=True)
        fname = 'db_auto_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json'
        path = os.path.join(_dir(), fname)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Rotación: conserva solo los últimos _KEEP
        files = sorted(x for x in os.listdir(_dir())
                       if x.startswith('db_auto_') and x.endswith('.json'))
        for viejo in files[:-_KEEP]:
            try:
                os.remove(os.path.join(_dir(), viejo))
            except OSError:
                pass
        _write_state({'ultimo': datetime.now().isoformat(), 'archivo': fname})
        return fname


def _loop(app):
    while True:
        try:
            if datetime.now() >= proximo_respaldo():
                ejecutar_respaldo(app)
        except Exception:
            pass
        time.sleep(_CHECK_SECONDS)


_started = False


def iniciar(app):
    """Arranca el hilo de respaldo automático (una sola vez por proceso)."""
    global _started
    if _started:
        return
    _started = True
    try:
        import eventlet.patcher as _ep
        threading = _ep.original('threading')  # hilo real, no greenlet
    except Exception:
        import threading
    t = threading.Thread(target=_loop, args=(app,), daemon=True)
    t.start()
