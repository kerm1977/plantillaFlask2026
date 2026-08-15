# Migrated from routes_cotizador.py
from . import bp
import re
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, make_response
from models_cotizador import Cotizador, CotizadorLugar
from db import db

@bp.route('/cotizadores/<slug>', methods=['GET'])
def cotizador_publico_slug(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    lugares_serializados = []
    for l in cotizador.lugares:
        lugares_serializados.append({
            'id': l.id,
            'nombre': l.nombre,
            'provincia': l.provincia or '',
            'duracion': l.duracion,
            'tipo_caminata': l.tipo_caminata or 'circular',
            'fecha_ida': l.fecha_ida or '',
            'fecha_regreso': l.fecha_regreso or '',
            'hora': l.hora or '',
            'maps_ida': l.maps_ida or '',
            'maps_regreso': l.maps_regreso or '',
            'moneda': l.moneda,
            'precio': l.precio,
            'precios_historial': json.loads(l.precios_historial or '[]')
        })
    resp = make_response(render_template('cotizador_publico.html', cotizador=cotizador, lugares_json=lugares_serializados))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, no-transform, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    resp.headers['Vary'] = '*'
    return resp

def cotizador_publico(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    lugares_serializados = []
    for l in cotizador.lugares:
        lugares_serializados.append({
            'id': l.id,
            'nombre': l.nombre,
            'provincia': l.provincia or '',
            'duracion': l.duracion,
            'tipo_caminata': l.tipo_caminata or 'circular',
            'fecha_ida': l.fecha_ida or '',
            'fecha_regreso': l.fecha_regreso or '',
            'hora': l.hora or '',
            'maps_ida': l.maps_ida or '',
            'maps_regreso': l.maps_regreso or '',
            'moneda': l.moneda,
            'precio': l.precio,
            'precios_historial': json.loads(l.precios_historial or '[]')
        })
    resp = make_response(render_template('cotizador_publico.html', cotizador=cotizador, lugares_json=lugares_serializados))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, no-transform, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    resp.headers['Vary'] = '*'
    return resp

@bp.route('/cotizadores/<slug>/verificar', methods=['POST'])
def verificar_clave_slug(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    clave = request.get_json().get('clave')
    if clave == cotizador.clave_acceso:
        return jsonify({'ok': True})
    return jsonify({'error': 'Clave incorrecta'}), 401

@bp.route('/cotizadores/<slug>/guardar', methods=['POST'])
def guardar_precios_slug(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    clave = request.get_json().get('clave')
    if clave != cotizador.clave_acceso:
        return jsonify({'error': 'Clave incorrecta'}), 401
    precios = request.get_json().get('precios', {})
    guardados = {}
    for lugar_id, precio in precios.items():
        lugar = CotizadorLugar.query.get(int(lugar_id))
        if lugar and lugar.cotizador_id == cotizador.id:
            if precio is None or (isinstance(precio, str) and not precio.strip()):
                nuevo_precio = None
            else:
                try:
                    nuevo_precio = float(precio)
                except (ValueError, TypeError):
                    continue
            if lugar.precio != nuevo_precio:
                historial = json.loads(lugar.precios_historial or '[]')
                historial.append({'precio': nuevo_precio, 'fecha': datetime.utcnow().isoformat()})
                lugar.precios_historial = json.dumps(historial, ensure_ascii=False)
                lugar.precio = nuevo_precio
            guardados[lugar_id] = {'precio': lugar.precio, 'precios_historial': json.loads(lugar.precios_historial or '[]')}
    try:
        db.session.commit()
        return jsonify({'ok': True, 'guardados': guardados})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

def verificar_clave(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    clave = request.get_json().get('clave')
    if clave == cotizador.clave_acceso:
        return jsonify({'ok': True})
    return jsonify({'error': 'Clave incorrecta'}), 401

def guardar_precios(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    clave = request.get_json().get('clave')
    if clave != cotizador.clave_acceso:
        return jsonify({'error': 'Clave incorrecta'}), 401
    precios = request.get_json().get('precios', {})
    guardados = {}
    for lugar_id, precio in precios.items():
        lugar = CotizadorLugar.query.get(int(lugar_id))
        if lugar and lugar.cotizador_id == cotizador.id:
            if precio is None or (isinstance(precio, str) and not precio.strip()):
                nuevo_precio = None
            else:
                try:
                    nuevo_precio = float(precio)
                except (ValueError, TypeError):
                    continue
            if lugar.precio != nuevo_precio:
                historial = json.loads(lugar.precios_historial or '[]')
                historial.append({'precio': nuevo_precio, 'fecha': datetime.utcnow().isoformat()})
                lugar.precios_historial = json.dumps(historial, ensure_ascii=False)
                lugar.precio = nuevo_precio
            guardados[lugar_id] = {'precio': lugar.precio, 'precios_historial': json.loads(lugar.precios_historial or '[]')}
    try:
        db.session.commit()
        return jsonify({'ok': True, 'guardados': guardados})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

@bp.route('/api/cotizadores/unico', methods=['GET'])
def cotizador_unico():
    c = Cotizador.query.first()
    if not c:
        return jsonify({'slug': None}), 404
    return jsonify({'slug': c.slug})

