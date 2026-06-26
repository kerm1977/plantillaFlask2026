import json
from flask import Response, send_from_directory, render_template, make_response
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
