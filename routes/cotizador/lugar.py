# Migrated from routes_cotizador.py
from . import bp
import re
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, make_response
from models_cotizador import Cotizador, CotizadorLugar
from db import db

@bp.route('/cotizadores/lugar/<int:id>', methods=['PUT'])
def actualizar_lugar(id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    lugar = CotizadorLugar.query.get_or_404(id)
    data = request.get_json()
    lugar.nombre = data.get('nombre', lugar.nombre)
    lugar.provincia = data.get('provincia', lugar.provincia)
    lugar.duracion = data.get('duracion', lugar.duracion)
    lugar.tipo_caminata = data.get('tipo_caminata', lugar.tipo_caminata)
    lugar.fecha_ida = data.get('fecha_ida', lugar.fecha_ida)
    lugar.fecha_regreso = data.get('fecha_regreso', lugar.fecha_regreso)
    lugar.hora = data.get('hora', lugar.hora)
    lugar.maps_ida = data.get('maps_ida', lugar.maps_ida)
    lugar.maps_regreso = data.get('maps_regreso', lugar.maps_regreso)
    lugar.moneda = data.get('moneda', lugar.moneda)
    db.session.commit()
    return jsonify({'ok': True})

@bp.route('/cotizadores/lugar/<int:id>', methods=['DELETE'])
def eliminar_lugar(id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    lugar = CotizadorLugar.query.get_or_404(id)
    db.session.delete(lugar)
    db.session.commit()
    return jsonify({'ok': True})

@bp.route('/api/cotizadores/lugar/<int:lugar_id>/precio-historial', methods=['DELETE'])
def eliminar_precio_historial(lugar_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        lugar = CotizadorLugar.query.get_or_404(lugar_id)
        data = request.get_json() or {}
        idx = data.get('index')
        historial = json.loads(lugar.precios_historial or '[]')
        if isinstance(idx, int) and 0 <= idx < len(historial):
            historial.pop(idx)
        lugar.precios_historial = json.dumps(historial, ensure_ascii=False)
        db.session.commit()
        return jsonify({'ok': True, 'precios_historial': historial})
    except Exception as e:
        db.session.rollback()
        print(f'[ERROR] Error al eliminar precio historial: {e}')
        return jsonify({'error': str(e)}), 500

