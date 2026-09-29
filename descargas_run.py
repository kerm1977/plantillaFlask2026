# ══ BLINDADO — DESCARGAS (ejecución yt-dlp + ffmpeg) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Procesos REALES del SO (eventlet congela subprocess), watchdog anti-
# bucle, cancelación, impersonación de navegador con curl_cffi.
import os
import re
import sys
import time
import shutil

# subprocess y threading REALES — eventlet.monkey_patch los congela.
try:
    import eventlet.patcher as _ep
    subprocess = _ep.original('subprocess')
    threading = _ep.original('threading')
except Exception:
    import subprocess
    import threading

try:
    import imageio_ffmpeg; FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception: FFMPEG = shutil.which('ffmpeg') or 'ffmpeg'  # PATH
DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'downloads')
os.makedirs(DIR, exist_ok=True)

TIMEOUT = 1200          # 20 min máximo por proceso
SIN_SALIDA_MAX = 240    # 4 min sin producir salida → se mata el proceso
_PCT = re.compile(r'\[download\]\s+(\d+\.?\d*)%')

# curl_cffi habilita --impersonate (huella TLS de navegador real,
# evita bloqueos anti-bot de YouTube/Facebook/etc.)
try:
    import curl_cffi  # noqa: F401
    _IMPERSONATE = ['--impersonate', 'chrome']
except ImportError:
    _IMPERSONATE = []

# Reintentos robustos de yt-dlp (red, fragmentos, extractor)
_ROBUSTEZ = ['--retries', '10', '--fragment-retries', '10', '--retry-sleep',
             '3', '--extractor-retries', '5', '--file-access-retries', '5',
             '--geo-bypass']

# Node como runtime JS desbloquea formatos de YouTube (solución oficial EJS)
_JS_RT = ['--js-runtimes', 'node'] if shutil.which('node') else []

_COOKIES = os.path.join(DIR, 'cookies.txt')


def ytdlp_cmd(url, args, extra):
    # --match-filters rechaza transmisiones en vivo: el HLS de un stream
    # nunca termina y genera el "bucle infinito" que se vio en producción.
    cmd = [sys.executable, '-m', 'yt_dlp', '--no-playlist', '--newline',
           '--match-filters', '!is_live', '--ffmpeg-location', FFMPEG] \
           + _IMPERSONATE + _JS_RT + _ROBUSTEZ
    if os.path.exists(_COOKIES):
        cmd += ['--cookies', _COOKIES]
    return cmd + args + extra + [url]


def _vigilante(p, job):
    """Mata el proceso si se cancela o si no produce salida en 4 min."""
    while p.poll() is None:
        if job.get('cancelar') or \
           time.time() - job.get('t_act', time.time()) > SIN_SALIDA_MAX:
            try:
                p.kill()
            except OSError:
                pass
            return
        time.sleep(2)


def _proc(job, cmd):
    job['t_act'] = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    job['proc'] = p
    threading.Thread(target=_vigilante, args=(p, job), daemon=True).start()
    return p


def run_progreso(job, cmd):
    """Ejecuta yt-dlp leyendo el progreso línea a línea (0-90%)."""
    p = _proc(job, cmd)
    tail = []
    try:
        for line in p.stdout:
            job['t_act'] = time.time()
            for txt in line.split('\r'):   # ffmpeg avanza con \r, no \n
                txt = txt.strip()
                if len(txt) < 4:
                    continue
                tail.append(txt)
                del tail[:-20]
                job['log'] = '\n'.join(tail[-4:])  # últimas líneas visibles
                m = _PCT.search(txt)
                if m:
                    job['pct'] = int(float(m.group(1)) * 0.9)
                    job['msg'] = 'Descargando ' + m.group(1) + '%'
                else:
                    job['msg'] = txt[:120]  # extracción/reintentos en vivo
        p.wait(timeout=60)
    except Exception:
        pass
    if job.get('cancelar'):
        return False, 'Cancelado'
    if p.poll() is None:
        try:
            p.kill()
        except OSError:
            pass
    return p.returncode == 0, '\n'.join(tail)


def buscar(base):
    """Primer archivo del trabajo que empiece con el prefijo dado."""
    pref = os.path.basename(base)
    for f in sorted(os.listdir(DIR)):
        if f.startswith(pref) and os.path.isfile(os.path.join(DIR, f)):
            return os.path.join(DIR, f)
    return None


def convertir(job, tmp, destino, args):
    job['status'] = 'convirtiendo'
    job['msg'] = 'Convirtiendo…'
    job['pct'] = 92
    p = _proc(job, [FFMPEG, '-y', '-i', tmp] + args + [destino])
    tail = []
    try:
        for line in p.stdout:
            job['t_act'] = time.time()
            tail.append(line.rstrip())
            del tail[:-10]
        p.wait(timeout=60)
    except Exception:
        pass
    if job.get('cancelar'):
        raise RuntimeError('Cancelado')
    if p.poll() is None:
        try:
            p.kill()
        except OSError:
            pass
    if p.returncode != 0 or not os.path.exists(destino):
        raise RuntimeError('ffmpeg falló: ' + '\n'.join(tail)[-400:])


def trabajar(job, base, al_terminar):
    """Descarga + conversión de un trabajo; al_terminar() libera el cupo."""
    url, fmt = job['url'], job['formato']
    extra = job.get('extra') or []
    try:
        if fmt in ('mp3', 'wma'):
            audio_fmt = 'mp3' if fmt == 'mp3' else 'wav'
            ok, log = run_progreso(job, ytdlp_cmd(url,
                ['-x', '--audio-format', audio_fmt,
                 '-o', base + '.%(ext)s'], extra))
            tmp = buscar(base)
            if not ok or not tmp:
                raise RuntimeError('yt-dlp falló: ' + log)
            if fmt == 'mp3':
                final = tmp
            else:
                final = base + '.wma'
                convertir(job, tmp, final, ['-vn', '-c:a', 'wmav2'])
                os.remove(tmp)
        else:
            ok, log = run_progreso(job, ytdlp_cmd(url,
                ['-S', 'vcodec:h264', '--merge-output-format', 'mp4',
                 '-o', base + '_v.%(ext)s'], extra))
            tmp = buscar(base + '_v')
            if not ok or not tmp:
                raise RuntimeError('yt-dlp falló: ' + log)
            if fmt == 'mp4':
                final = tmp
            elif fmt == 'gif':
                final = base + '.gif'
                convertir(job, tmp, final,
                          ['-vf', 'fps=10,scale=480:-1:flags=lanczos'])
                os.remove(tmp)
            else:  # wmv
                final = base + '.wmv'
                convertir(job, tmp, final,
                          ['-c:v', 'wmv2', '-b:v', '2M', '-c:a', 'wmav2'])
                os.remove(tmp)
        job['status'] = 'listo'
        job['pct'] = 100
        job['archivo'] = final
        job['nombre'] = 'descarga_' + job['id'][:8] + '.' + fmt
        job['msg'] = 'Listo'
    except Exception as e:
        job['status'] = 'cancelado' if job.get('cancelar') else 'error'
        msg = str(e)
        if job.get('cancelar'):
            msg = 'Detenido'
        elif 'filter' in msg or 'is_live' in msg:
            msg = 'Transmisión en vivo: no descargable hasta que termine.'
        job['msg'] = msg[:280]
    job['proc'] = None; al_terminar()
