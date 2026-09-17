import hashlib
import json
import os
from flask import Response, send_file, send_from_directory, render_template, make_response, jsonify, session, url_for
from models import Event
from routes import bp

# ==========================================
# RUTAS DE PWA (PROGRESIVE WEB APP)
# ==========================================

@bp.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "Caminatas La Tribu",
        "short_name": "La Tribu",
        "description": "Gestión de caminatas, eventos y comunidad de La Tribu de Los Libres.",
        "lang": "es",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#ffe0bd",
        "theme_color": "#ff8c00",
        "categories": ["sports", "social", "lifestyle"],
        "icons": [
            {
                "src": "/static/logo.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/logo.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "shortcuts": [
            {
                "name": "Inicio",
                "url": "/",
                "icons": [{"src": "/static/logo.png", "sizes": "96x96"}]
            }
        ]
    }
    return Response(json.dumps(manifest_data), mimetype='application/manifest+json')


@bp.route('/sw.js')
def sw():
    response = make_response(send_from_directory('static', 'sw.js', mimetype='application/javascript'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@bp.route('/offline')
def offline():
    return render_template('offline.html')


@bp.route('/download/android')
def download_android_app():
    apk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'downloads', 'LaTribu-debug.apk'))
    if not os.path.isfile(apk_path):
        return jsonify({'error': 'APK no disponible'}), 404
    response = send_file(apk_path, mimetype='application/vnd.android.package-archive', as_attachment=True, download_name='LaTribu.apk', conditional=True)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.route('/api/app/version')
def app_version():
    apk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'downloads', 'LaTribu-debug.apk'))
    checksum = ''
    size = 0
    if os.path.isfile(apk_path):
        size = os.path.getsize(apk_path)
        digest = hashlib.sha256()
        with open(apk_path, 'rb') as apk_file:
            for chunk in iter(lambda: apk_file.read(1024 * 1024), b''):
                digest.update(chunk)
        checksum = digest.hexdigest()
    return jsonify({
        'versionCode': 14,
        'versionName': '2.3.0',
        'url': 'https://www.latribu.top/download/android?build=15',
        'sha256': checksum,
        'size': size
    })


@bp.route('/api/offline/manifest')
def offline_manifest():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    static_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    files = []
    total_bytes = 0
    latest_mtime_ns = 0
    if os.path.isdir(static_root):
        for root, dirs, names in os.walk(static_root):
            dirs[:] = [name for name in dirs if name != 'downloads']
            for name in names:
                if name.lower().endswith('.apk'):
                    continue
                path = os.path.join(root, name)
                relative = os.path.relpath(path, static_root).replace(os.sep, '/')
                try:
                    stat = os.stat(path)
                except OSError:
                    continue
                size = stat.st_size
                total_bytes += size
                latest_mtime_ns = max(latest_mtime_ns, stat.st_mtime_ns)
                files.append({
                    'url': url_for('static', filename=relative),
                    'size': size,
                    'version': f'{stat.st_mtime_ns:x}-{size:x}'
                })

    pages = [
        '/', '/caminatas', '/caminatas/pendientes', '/caminatas/anio',
        '/caminatas/visitados', '/caminatas/programados', '/caminatas/cotizaciones',
        '/cotizaciones/buseta', '/nuestra-historia', '/mision', '/nuestra-oracion',
        '/terminos', '/nuestra-musica', '/caminatas-2027', '/quienes-somos',
        '/profile', '/gestor-fechas', '/offline'
    ]
    pages.extend(url_for('main.ver_caminata_2027', event_id=event.id)
                 for event in Event.query.order_by(Event.id).all())
    pages = list(dict.fromkeys(pages))
    return jsonify({
        'version': f'{latest_mtime_ns:x}-{total_bytes:x}-{len(files):x}-{len(pages):x}',
        'pages': pages,
        'files': files,
        'file_count': len(files),
        'total_bytes': total_bytes
    })
