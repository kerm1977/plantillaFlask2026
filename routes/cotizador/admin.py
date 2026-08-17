# Migrated from routes_cotizador.py
from . import bp, _slugify, _unique_slug
import re
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, make_response
from models_cotizador import Cotizador, CotizadorLugar
from db import db

@bp.route('/cotizadores/crear', methods=['GET'])
def crear_cotizador():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return redirect(url_for('cotizador.listar_cotizadores'))

@bp.route('/cotizadores/arte', methods=['GET'])
def arte_cotizacion():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('arte_cotizacion.html')

@bp.route('/cotizadores/lista')
@bp.route('/cotizadores')
def listar_cotizadores():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    cotizadores = Cotizador.query.order_by(Cotizador.fecha_creacion.desc()).all()
    return render_template('listar_cotizadores.html', cotizadores=cotizadores)

@bp.route('/cotizadores/crear', methods=['POST'])
def guardar_cotizador():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    try:
        # Verificar si ya existe un cotizador
        cotizador_existente = Cotizador.query.first()
        if cotizador_existente:
            return jsonify({'error': 'Ya existe un cotizador global. Solo se puede editar el existente.'}), 400
        
        data = request.get_json()
        print(f"[DEBUG] Datos recibidos: {data}")
        
        if not data.get('nombre') or not data.get('clave'):
            return jsonify({'error': 'Nombre y clave son obligatorios'}), 400
        
        cotizador = Cotizador(
            nombre=data.get('nombre'),
            slug=_unique_slug(data.get('nombre')),
            clave_acceso=data.get('clave')
        )
        db.session.add(cotizador)
        db.session.commit()
        
        print(f"[DEBUG] Cotizador creado con ID: {cotizador.id}")
        
        for lugar_data in data.get('lugares', []):
            lugar = CotizadorLugar(
                cotizador_id=cotizador.id,
                nombre=lugar_data.get('nombre'),
                provincia=lugar_data.get('provincia'),
                duracion=lugar_data.get('duracion', '1_dia'),
                tipo_caminata=lugar_data.get('tipo_caminata', 'circular'),
                fecha_ida=lugar_data.get('fecha_ida'),
                fecha_regreso=lugar_data.get('fecha_regreso'),
                hora=lugar_data.get('hora'),
                maps_ida=lugar_data.get('maps_ida'),
                maps_regreso=lugar_data.get('maps_regreso'),
                moneda=lugar_data.get('moneda', 'colones'),
                order=lugar_data.get('order', 0)
            )
            db.session.add(lugar)
        db.session.commit()
        
        print(f"[DEBUG] Lugares guardados correctamente")
        return jsonify({'ok': True, 'id': cotizador.id, 'slug': cotizador.slug})
    except Exception as e:
        print(f"[ERROR] Error al crear cotizador: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/cotizadores/<int:id>/eliminar', methods=['POST'])
def eliminar_cotizador(id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    cotizador = Cotizador.query.get_or_404(id)
    db.session.delete(cotizador)
    db.session.commit()
    return jsonify({'ok': True})

@bp.route('/cotizadores/<int:id>', methods=['PUT'])
def actualizar_cotizador(id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    cotizador = Cotizador.query.get_or_404(id)
    data = request.get_json()
    
    try:
        if data.get('titulo') is not None:
            cotizador.titulo = data.get('titulo')
        
        if data.get('nombre'):
            cotizador.nombre = data.get('nombre')
            cotizador.slug = _unique_slug(data.get('nombre'), exclude_id=id)
        
        if data.get('descripcion') is not None:
            cotizador.descripcion = data.get('descripcion')
        
        if data.get('clave'):
            cotizador.clave_acceso = data.get('clave')
        
        if data.get('mostrar_nombre') is not None:
            cotizador.mostrar_nombre = bool(data.get('mostrar_nombre'))
        if data.get('mostrar_descripcion') is not None:
            cotizador.mostrar_descripcion = bool(data.get('mostrar_descripcion'))
        if data.get('mostrar_titulo') is not None:
            cotizador.mostrar_titulo = bool(data.get('mostrar_titulo'))
        
        db.session.commit()
        
        # Eliminar lugares existentes
        CotizadorLugar.query.filter_by(cotizador_id=id).delete()
        
        # Agregar nuevos lugares
        for lugar_data in data.get('lugares', []):
            precio_raw = lugar_data.get('precio')
            try:
                precio = float(str(precio_raw)) if precio_raw is not None and str(precio_raw).strip() != '' else None
            except (ValueError, TypeError):
                precio = None
            lugar = CotizadorLugar(
                cotizador_id=id,
                nombre=lugar_data.get('nombre'),
                provincia=lugar_data.get('provincia'),
                duracion=lugar_data.get('duracion', '1_dia'),
                tipo_caminata=lugar_data.get('tipo_caminata', 'circular'),
                fecha_ida=lugar_data.get('fecha_ida'),
                fecha_regreso=lugar_data.get('fecha_regreso'),
                hora=lugar_data.get('hora'),
                maps_ida=lugar_data.get('maps_ida'),
                maps_regreso=lugar_data.get('maps_regreso'),
                moneda=lugar_data.get('moneda', 'colones'),
                precio=precio,
                order=lugar_data.get('order', 0)
            )
            db.session.add(lugar)
        
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        print(f"[ERROR] Error al actualizar cotizador: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/cotizadores/<int:id>/ver', methods=['GET'])
def ver_cotizador(id):
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    cotizador = Cotizador.query.get_or_404(id)
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
    return render_template('ver_cotizador.html', cotizador=cotizador, lugares_json=lugares_serializados)

