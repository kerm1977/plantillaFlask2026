# ══ BLINDADO — DESCARGAS (motor yt-dlp + ffmpeg) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Descarga videos de YouTube/Facebook/TikTok/Instagram/web y convierte
# a mp4 (h264), mp3, gif, wmv o wma. Solo superusuario (ver rutas).
import os
import re
import sys
import time
import uuid
import threading
import subprocess

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'downloads')
os.makedirs(_DIR, exist_ok=True)

FORMATOS = ('mp4', 'mp3', 'gif', 'wmv', 'wma')
TIMEOUT = 900          # 15 min máximo por proceso
JOBS = {}              # id -> {status, msg, archivo, nombre, ts}


def _sweep():
    """Borra resultados y trabajos de más de 1 hora."""
    ahora = time.time()
    for jid, job in list(JOBS.items()):
        if ahora - job.get('ts', 0) > 3600:
            JOBS.pop(jid, None)
    for f in os.listdir(_DIR):
        p = os.path.join(_DIR, f)
        try:
            if os.path.isfile(p) and ahora - os.path.getmtime(p) > 3600:
                os.remove(p)
        except OSError:
            pass


def _ejecutar(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    return r.returncode == 0, (r.stderr or r.stdout or '')[-800:]


def _ytdlp(url, args):
    return [sys.executable, '-m', 'yt_dlp', '--no-playlist', '--no-warnings',
            '--ffmpeg-location', FFMPEG] + args + [url]


def _buscar(base):
    """Primer archivo del trabajo que empiece con el prefijo dado."""
    pref = os.path.basename(base)
    for f in sorted(os.listdir(_DIR)):
        if f.startswith(pref) and os.path.isfile(os.path.join(_DIR, f)):
            return os.path.join(_DIR, f)
    return None


def _audio(job, base, fmt, url):
    ok, log = _ejecutar(_ytdlp(url, ['-x', '--audio-format', fmt,
                                   '-o', base + '.%(ext)s']))
    tmp = _buscar(base)
    if not ok or not tmp:
        raise RuntimeError('yt-dlp falló: ' + log)
    return tmp


def _video(job, base, url):
    ok, log = _ejecutar(_ytdlp(url, ['-S', 'vcodec:h264',
                                     '--merge-output-format', 'mp4',
                                     '-o', base + '_v.%(ext)s']))
    tmp = _buscar(base + '_v')
    if not ok or not tmp:
        raise RuntimeError('yt-dlp falló: ' + log)
    return tmp


def _convertir(job, tmp, destino, args):
    job['msg'] = 'Convirtiendo…'
    ok, log = _ejecutar([FFMPEG, '-y', '-i', tmp] + args + [destino])
    if not ok or not os.path.exists(destino):
        raise RuntimeError('ffmpeg falló: ' + log)


def _trabajar(jid, url, formato):
    job = JOBS[jid]
    base = os.path.join(_DIR, jid)
    try:
        job['msg'] = 'Descargando…'
        if formato == 'mp3':
            final = _audio(job, base, 'mp3', url)
        elif formato == 'wma':
            tmp = _audio(job, base, 'wav', url)
            final = base + '.wma'
            _convertir(job, tmp, final, ['-vn', '-c:a', 'wmav2'])
            os.remove(tmp)
        else:
            tmp = _video(job, base, url)
            if formato == 'mp4':
                final = tmp
            elif formato == 'gif':
                final = base + '.gif'
                _convertir(job, tmp, final,
                           ['-vf', 'fps=10,scale=480:-1:flags=lanczos'])
                os.remove(tmp)
            else:  # wmv
                final = base + '.wmv'
                _convertir(job, tmp, final,
                           ['-c:v', 'wmv2', '-b:v', '2M', '-c:a', 'wmav2'])
                os.remove(tmp)
        job['status'] = 'listo'
        job['archivo'] = final
        job['nombre'] = 'descarga_' + jid[:8] + '.' + formato
        job['msg'] = 'Listo'
    except Exception as e:
        job['status'] = 'error'
        job['msg'] = str(e)[:300]
    job['ts'] = time.time()


def iniciar(url, formato):
    """Lanza el trabajo en segundo plano y devuelve su id."""
    _sweep()
    jid = uuid.uuid4().hex
    JOBS[jid] = {'status': 'procesando', 'msg': 'Iniciando…',
                 'archivo': None, 'nombre': '', 'ts': time.time()}
    threading.Thread(target=_trabajar, args=(jid, url, formato),
                     daemon=True).start()
    return jid


def estado(jid):
    job = JOBS.get(jid)
    if not job:
        return None
    return {'status': job['status'], 'msg': job['msg']}


def archivo(jid):
    """(ruta, nombre_descarga) o None si no está listo."""
    job = JOBS.get(jid)
    if not job or job['status'] != 'listo' or not job['archivo']:
        return None
    return job['archivo'], job['nombre']


def url_valida(url):
    return bool(re.match(r'^https?://\S+$', url or ''))
