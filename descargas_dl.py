# ══ BLINDADO — DESCARGAS (cola y trabajos) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Multi-enlace con cola y concurrencia configurable (1-10), progreso real,
# opciones avanzadas yt-dlp. Solo superusuario (ver routes/descargas.py).
# Ejecución en descargas_run.py; actualización en descargas_up.py.
import os
import re
import time
import uuid
import shlex

# Las descargas corren en hilos REALES del SO — los hilos verdes de
# eventlet congelan subprocess (ver descargas_run.py).
try:
    import eventlet.patcher as _ep
    threading = _ep.original('threading')
except Exception:
    import threading

import descargas_run as run

FORMATOS = ('mp4', 'mp3', 'gif', 'wmv', 'wma')
MAX_SIMULTANEAS = 10

JOBS = {}               # jid -> dict de trabajo
LOTES = {}              # lid -> [jids]
_COLA = []              # jids pendientes
_LOCK = threading.Lock()
_MAX_PAR = 2            # descargas simultáneas activas

# Flags no permitidos en opciones avanzadas (seguridad/salida controlada)
_ARGS_BLOQUEADOS = ('--exec', '-o', '--output', '--paths', '-P',
                    '--config', '--config-location', '--plugin-dirs',
                    '--batch-file', '-a')


def _sweep():
    """Borra trabajos y archivos de más de 1 hora."""
    ahora = time.time()
    for jid, job in list(JOBS.items()):
        if ahora - job.get('ts', 0) > 3600:
            JOBS.pop(jid, None)
    for lid in list(LOTES):
        LOTES[lid] = [j for j in LOTES[lid] if j in JOBS]
        if not LOTES[lid]:
            LOTES.pop(lid)
    for f in os.listdir(run.DIR):
        p = os.path.join(run.DIR, f)
        try:
            if os.path.isfile(p) and ahora - os.path.getmtime(p) > 3600:
                os.remove(p)
        except OSError:
            pass


def _extra_args(txt):
    """Opciones yt-dlp del usuario, menos flags bloqueados."""
    if not txt:
        return []
    try:
        args = shlex.split(txt)
    except ValueError:
        return []
    out = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in _ARGS_BLOQUEADOS:
            i += 2          # salta el flag y su valor
            continue
        if any(a.startswith(b + '=') for b in _ARGS_BLOQUEADOS):
            i += 1
            continue
        out.append(a)
        i += 1
    return out


def _activos():
    return sum(1 for j in JOBS.values()
               if j['status'] in ('descargando', 'convirtiendo'))


def _arrancar():
    with _LOCK:
        while _COLA and _activos() < _MAX_PAR:
            jid = _COLA.pop(0)
            JOBS[jid]['status'] = 'descargando'
            JOBS[jid]['msg'] = 'Descargando…'
            base = os.path.join(run.DIR, jid)
            threading.Thread(target=run.trabajar,
                             args=(JOBS[jid], base, _fin),
                             daemon=True).start()


def _fin():
    _arrancar()


def iniciar_lote(urls, formato, extra, max_par):
    """Encola los enlaces y devuelve el id del lote."""
    _sweep()
    global _MAX_PAR
    try:
        _MAX_PAR = max(1, min(MAX_SIMULTANEAS, int(max_par)))
    except (TypeError, ValueError):
        _MAX_PAR = 2
    extra = _extra_args(extra)
    lid = uuid.uuid4().hex[:12]
    jids = []
    for u in urls:
        jid = uuid.uuid4().hex
        JOBS[jid] = {'id': jid, 'url': u, 'formato': formato,
                     'status': 'pendiente', 'pct': 0,
                     'msg': 'En cola…', 'archivo': None,
                     'nombre': '', 'extra': extra, 'ts': time.time()}
        _COLA.append(jid)
        jids.append(jid)
    LOTES[lid] = jids
    _arrancar()
    return lid


def cancelar(jid):
    """Detiene un trabajo: lo saca de la cola o mata su proceso."""
    job = JOBS.get(jid)
    if not job:
        return False
    job['cancelar'] = True
    if job['status'] == 'pendiente':
        job['status'] = 'cancelado'
        job['msg'] = 'Detenido'
        with _LOCK:
            if jid in _COLA:
                _COLA.remove(jid)
    p = job.get('proc')
    if p:
        try:
            p.kill()
        except OSError:
            pass
    _arrancar()
    return True


def cancelar_todo():
    n = 0
    for jid, job in list(JOBS.items()):
        if job['status'] in ('pendiente', 'descargando', 'convirtiendo'):
            cancelar(jid)
            n += 1
    return n


def lote(lid):
    jids = LOTES.get(lid)
    if jids is None:
        return None
    keys = ('id', 'url', 'formato', 'status', 'pct', 'msg', 'nombre', 'log')
    return [{k: JOBS[j].get(k) for k in keys} for j in jids if j in JOBS]


def guardar_cookies(archivo):
    """Guarda el cookies.txt exportado del navegador (fix anti-bot)."""
    path = os.path.join(run.DIR, 'cookies.txt')
    archivo.save(path)
    return os.path.getsize(path) > 10


def archivo(jid):
    job = JOBS.get(jid)
    if not job or job['status'] != 'listo' or not job['archivo']:
        return None
    job['ts'] = time.time()
    return job['archivo'], job['nombre']


def url_valida(url):
    return bool(re.match(r'^https?://\S+$', url or ''))
