# Migrated from routes_cotizador.py
from . import bp
import re
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, make_response
from models_cotizador import Cotizador, CotizadorLugar
from db import db

@bp.route('/api/cotizadores/export-json', methods=['GET'])
def exportar_cotizadores_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        cotizadores = Cotizador.query.order_by(Cotizador.id.asc()).all()
        data = []
        for c in cotizadores:
            data.append({
                'nombre': c.nombre,
                'slug': c.slug,
                'clave_acceso': c.clave_acceso,
                'titulo': c.titulo,
                'descripcion': c.descripcion,
                'mostrar_nombre': c.mostrar_nombre,
                'mostrar_descripcion': c.mostrar_descripcion,
                'mostrar_titulo': c.mostrar_titulo,
                'fecha_creacion': c.fecha_creacion.isoformat() if c.fecha_creacion else None,
                'lugares': [{
                    'nombre': l.nombre,
                    'provincia': l.provincia,
                    'duracion': l.duracion,
                    'tipo_caminata': l.tipo_caminata or 'circular',
                    'fecha_ida': l.fecha_ida,
                    'fecha_regreso': l.fecha_regreso,
                    'hora': l.hora,
                    'maps_ida': l.maps_ida,
                    'maps_regreso': l.maps_regreso,
                    'moneda': l.moneda,
                    'precio': l.precio,
                    'order': l.order
                } for l in c.lugares]
            })
        return jsonify({'cotizadores': data})
    except Exception as e:
        print(f'[ERROR] Error al exportar cotizadores: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/api/cotizadores/import-json', methods=['POST'])
def importar_cotizadores_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        payload = request.get_json()
        if not payload or 'cotizadores' not in payload:
            return jsonify({'error': 'Formato JSON invalido'}), 400

        # Eliminar cotizadores existentes y sus lugares en cascada
        Cotizador.query.delete()
        db.session.commit()

        nuevos = []
        for c_data in payload['cotizadores']:
            c = Cotizador(
                nombre=c_data.get('nombre'),
                slug=c_data.get('slug'),
                clave_acceso=c_data.get('clave_acceso'),
                titulo=c_data.get('titulo'),
                descripcion=c_data.get('descripcion'),
                mostrar_nombre=c_data.get('mostrar_nombre', True),
                mostrar_descripcion=c_data.get('mostrar_descripcion', True),
                mostrar_titulo=c_data.get('mostrar_titulo', True)
            )
            db.session.add(c)
            db.session.flush()

            for l_data in c_data.get('lugares', []):
                lugar = CotizadorLugar(
                    cotizador_id=c.id,
                    nombre=l_data.get('nombre'),
                    provincia=l_data.get('provincia'),
                    duracion=l_data.get('duracion', '1_dia'),
                    tipo_caminata=l_data.get('tipo_caminata', 'circular'),
                    fecha_ida=l_data.get('fecha_ida'),
                    fecha_regreso=l_data.get('fecha_regreso'),
                    hora=l_data.get('hora'),
                    maps_ida=l_data.get('maps_ida'),
                    maps_regreso=l_data.get('maps_regreso'),
                    moneda=l_data.get('moneda', 'colones'),
                    precio=l_data.get('precio'),
                    order=l_data.get('order', 0)
                )
                db.session.add(lugar)
            nuevos.append(c)

        db.session.commit()
        return jsonify({'ok': True, 'importados': len(nuevos)})
    except Exception as e:
        db.session.rollback()
        print(f'[ERROR] Error al importar cotizadores: {e}')
        return jsonify({'error': str(e)}), 500

