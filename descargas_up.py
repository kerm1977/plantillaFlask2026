# ══ BLINDADO — DESCARGAS (actualización de yt-dlp) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Consulta la última versión en PyPI y actualiza con pip.
import json
import sys
import urllib.request
import importlib.metadata as md

# subprocess/hilos REALES — eventlet congela subprocess (ver descargas_run).
try:
    import eventlet.patcher as _ep
    subprocess = _ep.original('subprocess')
    threading = _ep.original('threading')
except Exception:
    import subprocess
    import threading

UP = {'running': False, 'salida': '', 'version': ''}


def version_actual():
    try:
        return md.version('yt-dlp')
    except Exception:
        return ''


def version_remota():
    """Última versión publicada en PyPI ('' si no hay red)."""
    try:
        with urllib.request.urlopen(
                'https://pypi.org/pypi/yt-dlp/json', timeout=8) as r:
            return json.load(r)['info']['version']
    except Exception:
        return ''


def actualizar():
    """Actualiza yt-dlp con pip en segundo plano."""
    if UP['running']:
        return
    UP['running'] = True
    UP['salida'] = 'Actualizando…'

    def _run():
        try:
            r = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade',
                 'yt-dlp'], capture_output=True, text=True, timeout=300)
            UP['salida'] = (r.stdout or r.stderr or '')[-400:]
            UP['version'] = version_actual()
        except Exception as e:
            UP['salida'] = 'Error: ' + str(e)[:200]
        UP['running'] = False

    threading.Thread(target=_run, daemon=True).start()


def estado():
    return {'running': UP['running'], 'salida': UP['salida'],
            'version': UP['version'] or version_actual()}
