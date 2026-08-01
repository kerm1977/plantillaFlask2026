from flask import jsonify, session, make_response
from models import Event
from db import db
from routes import bp
from helpers.google_calendar import generate_google_calendar_link_event


@bp.route('/api/get_events')
def get_events():
    events = Event.query.order_by(Event.created_at.desc()).all()
    is_super = session.get('role') == 'Superusuario'
    output = []
    
    for e in events:
        # LÓGICA DE NEGOCIO EN EL BACKEND (Donde debe estar)
        # Si es logística segura y NO es admin, ocultamos datos
        if e.logistica_segura and not is_super:   
            destino_text = "Ver en chat"
            hora_text = "Ver en chat"
        else:
            destino_text = e.lugar_salida
            hora_text = e.hora_salida
                
        # Calcular precio o devolver "PENDIENTE"
        try:
            precio_val = int(e.precio) if e.precio else 0
        except (ValueError, TypeError):
            precio_val = 0
            
        precio_mostrar = f"{e.moneda or ''}{precio_val}" if precio_val > 0 else "PENDIENTE"
        
        # Generar enlace de Google Calendar
        google_calendar_link = generate_google_calendar_link_event(e)
                
        output.append({
            "id": e.id,
            "poster": f"/static/uploads/{e.poster}" if e.poster else "/static/default.png",
            "nombreLugar": e.nombre_lugar,
            "dificultad": e.dificultad,
            "actividad": e.actividad,
            "precio": precio_mostrar,
            "destino": destino_text,
            "hora_salida": hora_text or "Por definir",
            "logistica_segura": e.logistica_segura,
            "fecha": e.fecha_unica if e.dias == 1 else f"{e.fecha_inicio} al {e.fecha_regreso}",
            "solo_chat": e.solo_chat, 
            "capacidad": e.capacidad,
            "is_sold_out": e.is_sold_out,
            "google_calendar_link": google_calendar_link
        })
    response = make_response(jsonify(output))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response


@bp.route('/api/toggle_espacio/<int:event_id>', methods=['POST'])
def toggle_espacio(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    # Ya no manipulamos strings, solo invertimos el booleano
    evento.is_sold_out = not evento.is_sold_out
    db.session.commit()
    return jsonify({"success": True, "is_sold_out": evento.is_sold_out})


@bp.route('/api/make_public/<int:event_id>', methods=['POST'])
def make_public(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    # Quitamos la privacidad limpiamente
    evento.logistica_segura = False
    evento.solo_chat = False
    db.session.commit()
    return jsonify({"success": True})
