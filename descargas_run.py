# ══ BLINDADO — DESCARGAS (ejecución yt-dlp + ffmpeg) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Procesos, progreso y conversión. La cola vive en descargas_dl.py.
import os
import re
import sys

# eventlet.monkey_patch rompe subprocess en hilos verdes:
# se usa el subprocess REAL del sistema operativo.
try:
    import eventlet.patcher as _ep
    subprocess = _ep.original('subprocess')
except Exception:
    import subprocess

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'downloads')
os.makedirs(DIR, exist_ok=True)

TIMEOUT = 1200
_PCT = re.compile(r'\[download\]\s+(\d+\.?\d*)%')


def ytdlp_cmd(url, args, extra):
    return [sys.executable, '-m', 'yt_dlp', '--no-playlist', '--newline',
            '--no-warnings', '--ffmpeg-location', FFMPEG] + args + extra + [url]


def run_progreso(job, cmd):
    """Ejecuta yt-dlp leyendo el progreso línea a línea (0-90%)."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    tail = []
    try:
        for line in p.stdout:
            tail.append(line.rstrip())
            del tail[:-20]
            m = _PCT.search(line)
            if m:
                job['pct'] = int(float(m.group(1)) * 0.9)
                job['msg'] = 'Descargando ' + m.group(1) + '%'
        p.wait(timeout=TIMEOUT)
    except Exception:
        p.kill()
        return False, '\n'.join(tail)
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
    r = subprocess.run([FFMPEG, '-y', '-i', tmp] + args + [destino],
                       capture_output=True, text=True, timeout=TIMEOUT)
    if r.returncode != 0 or not os.path.exists(destino):
        raise RuntimeError('ffmpeg falló: ' + (r.stderr or '')[-400:])


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
        job['status'] = 'error'
        job['msg'] = str(e)[:280]
    al_terminar()
