# routes/agenda.py - Buscador de agenda médica con PIN maestro
from sqlalchemy import or_
from flask import request, jsonify
from config import Config
from models import Hiker
from routes import bp


@bp.route('/api/agenda/search', methods=['POST'])
def search_agenda():
    data = request.json or {}
    master_pin = (data.get('master_pin') or '').strip()
    if master_pin != Config.SUPERUSER_PASSWORD:
        return jsonify({'ok': False, 'error': 'PIN maestro inválido'}), 403

    query = (data.get('q') or '').strip()
    if not query:
        return jsonify({'ok': True, 'hikers': []})

    search = f'%{query}%'
    hikers = Hiker.query.filter(
        or_(
            Hiker.cedula.ilike(search),
            Hiker.nombre_completo.ilike(search),
            Hiker.telefono.ilike(search),
            Hiker.pasaporte.ilike(search),
            Hiker.tipo_sangre.ilike(search),
            Hiker.alergias.ilike(search),
            Hiker.enfermedades_cronicas.ilike(search),
            Hiker.contacto_emergencia_nombre.ilike(search),
            Hiker.contacto_emergencia_telefono.ilike(search),
            Hiker.pin_secreto.ilike(search),
        )
    ).limit(50).all()

    results = []
    for h in hikers:
        results.append({
            'id': h.id,
            'cedula': h.cedula,
            'nombre_completo': h.nombre_completo,
            'telefono': h.telefono,
            'pasaporte': h.pasaporte,
            'tipo_sangre': h.tipo_sangre,
            'fecha_nacimiento': h.fecha_nacimiento.strftime('%d/%m/%Y') if h.fecha_nacimiento else '',
            'alergias': h.alergias,
            'enfermedades_cronicas': h.enfermedades_cronicas,
            'contacto_emergencia_nombre': h.contacto_emergencia_nombre,
            'contacto_emergencia_telefono': h.contacto_emergencia_telefono,
            'pin_secreto': h.pin_secreto,
        })
    return jsonify({'ok': True, 'hikers': results})
