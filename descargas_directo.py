# ══ BLINDADO — DESCARGAS (motor directo ffmpeg/HTTP) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Segundo motor para enlaces DIRECTOS a medios: .mp4 .mp3 .m3u8 .mpd .ts
# .webm .aac … sin extractor web. Soporta -decryption_key con la clave
# propia del usuario (KID:key) para contenido Widevine de su propiedad.
import os
import time
import urllib.request
import urllib.error

import descargas_run as run

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/127.0 Safari/537.36')
# Extensiones que el motor directo sabe manejar
_EXT_STREAM = ('.m3u8', '.mpd')               # HLS / DASH → ffmpeg
_EXT_MEDIA = ('.mp4', '.mp3', '.m4a', '.aac', '.webm', '.mkv', '.ts',
              '.mov', '.ogg', '.opus', '.wav', '.flv', '.avi', '.m4v')


def es_directa(url):
    """True si la URL apunta a un archivo/stream directo."""
    u = url.split('?')[0].split('#')[0].lower()
    return u.endswith(_EXT_STREAM + _EXT_MEDIA)


def _clave_hex(clave):
    """Acepta 'KID:hex' (mp4decrypt) o 'hex' directo; None si vacía."""
    if not clave:
        return None
    c = clave.strip()
    if ':' in c:
        c = c.split(':', 1)[1]
    c = c.strip()
    return c if c and all(ch in '0123456789abcdefABCDEF' for ch in c) else None


def _descargar_http(job, url, destino):
    """Descarga un archivo plano con progreso real por Content-Length."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    escrito, total = 0, 0
    with urllib.request.urlopen(req, timeout=60) as r, \
            open(destino, 'wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        while True:
            if job.get('cancelar'):
                return False
            chunk = r.read(256 * 1024)
            if not chunk:
                break
            f.write(chunk)
            escrito += len(chunk)
            job['t_act'] = time.time()
            if total:
                pct = min(90, int(escrito * 90 / total))
                job['pct'] = pct
                job['msg'] = 'Descargando %d%% (%.1f MB)' % (
                    escrito * 100 / total, escrito / 1048576)
            else:
                job['msg'] = 'Descargando %.1f MB' % (escrito / 1048576)
    return escrito > 0


def _ffmpeg_copia(job, url, destino, clave):
    """Captura HLS/DASH o remuxa un stream remoto vía ffmpeg (-c copy)."""
    args = [run.FFMPEG, '-y', '-headers', 'User-Agent: %s\r\n' % UA]
    k = _clave_hex(clave)
    if k:
        args += ['-decryption_key', k]
    args += ['-i', url, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', destino]
    p = run._proc(job, args)
    tail = []
    try:
        for line in p.stdout:
            job['t_act'] = time.time()
            txt = line.strip()
            if len(txt) > 3:
                tail.append(txt)
                del tail[:-12]
                job['log'] = '\n'.join(tail[-4:])
                if 'time=' in txt:
                    job['msg'] = 'Capturando ' + txt.split('time=')[-1][:11]
    except Exception:
        pass
    p.wait()
    return p.returncode == 0 and os.path.exists(destino), tail


def trabajar(job, base, al_terminar):
    """Motor directo: HTTP para archivos, ffmpeg para streams."""
    url, fmt = job['url'], job['formato']
    try:
        u = url.split('?')[0].lower()
        es_stream = u.endswith(_EXT_STREAM)
        tmp = base + '_v.mp4' if es_stream else None
        if es_stream:
            ok, tail = _ffmpeg_copia(job, url, tmp, job.get('clave'))
            if not ok:
                raise RuntimeError('ffmpeg falló: ' + '\n'.join(tail)[-400:])
        else:  # archivo plano por HTTP
            ext = os.path.splitext(u)[1] or '.bin'
            tmp = base + '_v' + ext
            if not _descargar_http(job, url, tmp):
                if job.get('cancelar'):
                    raise RuntimeError('Cancelado')
                raise RuntimeError('Descarga incompleta o falló')
        if fmt == 'mp4' and tmp.endswith('.mp4'):
            final = tmp
        elif fmt == 'mp3':
            final = base + '.mp3'
            run.convertir(job, tmp, final, ['-vn', '-c:a', 'libmp3lame'])
            if tmp != final:
                os.remove(tmp)
        elif fmt == 'wma':
            final = base + '.wma'
            run.convertir(job, tmp, final, ['-vn', '-c:a', 'wmav2'])
            os.remove(tmp)
        elif fmt == 'gif':
            final = base + '.gif'
            run.convertir(job, tmp, final,
                          ['-vf', 'fps=10,scale=480:-1:flags=lanczos'])
            os.remove(tmp)
        elif fmt == 'wmv':
            final = base + '.wmv'
            run.convertir(job, tmp, final,
                          ['-c:v', 'wmv2', '-b:v', '2M', '-c:a', 'wmav2'])
            os.remove(tmp)
        else:
            final = tmp
        job['status'] = 'listo'
        job['pct'] = 100
        job['archivo'] = final
        job['nombre'] = 'descarga_' + job['id'][:8] + '.' + fmt
        job['msg'] = 'Listo'
    except Exception as e:
        if job.get('cancelar'):
            job['status'] = 'cancelado'
            job['msg'] = 'Detenido'
        else:
            job['status'] = 'error'
            job['msg'] = str(e)[:280]
    job['proc'] = None
    al_terminar()
