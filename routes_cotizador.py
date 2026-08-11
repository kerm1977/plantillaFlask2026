import re
import json
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models_cotizador import Cotizador, CotizadorLugar
from db import db

bp = Blueprint('cotizador', __name__)

def _slugify(text):
    text = text.lower().strip()
    for src, dst in [('[áàäâ]','a'),('[éèëê]','e'),('[íìïî]','i'),('[óòöô]','o'),('[úùüû]','u'),('[ñ]','n')]:
        text = re.sub(src, dst, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text

def _unique_slug(text, exclude_id=None):
    slug = _slugify(text)
    counter = 1
    while True:
        query = Cotizador.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(Cotizador.id != exclude_id)
        existing = query.first()
        if not existing:
            return slug
        slug = f"{slug}-{counter}"
        counter += 1

@bp.route('/cotizadores')
def crear_cotizador():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return redirect(url_for('cotizador.listar_cotizadores'))

@bp.route('/cotizadores/arte')
def arte_cotizacion():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('arte_cotizacion.html')

@bp.route('/cotizadores/lista')
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
            lugar = CotizadorLugar(
                cotizador_id=id,
                nombre=lugar_data.get('nombre'),
                provincia=lugar_data.get('provincia'),
                duracion=lugar_data.get('duracion', '1_dia'),
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
        return jsonify({'ok': True})
    except Exception as e:
        print(f"[ERROR] Error al actualizar cotizador: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/cotizadores/<slug>')
def cotizador_publico_slug(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    lugares_serializados = []
    for l in cotizador.lugares:
        lugares_serializados.append({
            'id': l.id,
            'nombre': l.nombre,
            'provincia': l.provincia or '',
            'duracion': l.duracion,
            'fecha_ida': l.fecha_ida or '',
            'fecha_regreso': l.fecha_regreso or '',
            'hora': l.hora or '',
            'maps_ida': l.maps_ida or '',
            'maps_regreso': l.maps_regreso or '',
            'moneda': l.moneda,
            'precio': l.precio
        })
    return render_template('cotizador_publico.html', cotizador=cotizador, lugares_json=lugares_serializados)

@bp.route('/cotizador/<slug>')
def cotizador_publico(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    lugares_serializados = []
    for l in cotizador.lugares:
        lugares_serializados.append({
            'id': l.id,
            'nombre': l.nombre,
            'provincia': l.provincia or '',
            'duracion': l.duracion,
            'fecha_ida': l.fecha_ida or '',
            'fecha_regreso': l.fecha_regreso or '',
            'hora': l.hora or '',
            'maps_ida': l.maps_ida or '',
            'maps_regreso': l.maps_regreso or '',
            'moneda': l.moneda,
            'precio': l.precio
        })
    return render_template('cotizador_publico.html', cotizador=cotizador, lugares_json=lugares_serializados)

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
    for lugar_id, precio in precios.items():
        lugar = CotizadorLugar.query.get(int(lugar_id))
        if lugar and lugar.cotizador_id == cotizador.id:
            lugar.precio = float(precio) if precio else None
    db.session.commit()
    return jsonify({'ok': True})

@bp.route('/cotizador/<slug>/verificar', methods=['POST'])
def verificar_clave(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    clave = request.get_json().get('clave')
    if clave == cotizador.clave_acceso:
        return jsonify({'ok': True})
    return jsonify({'error': 'Clave incorrecta'}), 401

@bp.route('/cotizador/<slug>/guardar', methods=['POST'])
def guardar_precios(slug):
    cotizador = Cotizador.query.filter_by(slug=slug).first_or_404()
    clave = request.get_json().get('clave')
    if clave != cotizador.clave_acceso:
        return jsonify({'error': 'Clave incorrecta'}), 401
    precios = request.get_json().get('precios', {})
    for lugar_id, precio in precios.items():
        lugar = CotizadorLugar.query.get(int(lugar_id))
        if lugar and lugar.cotizador_id == cotizador.id:
            lugar.precio = float(precio) if precio else None
    db.session.commit()
    return jsonify({'ok': True})

@bp.route('/cotizadores/<int:id>/ver')
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
            'fecha_ida': l.fecha_ida or '',
            'fecha_regreso': l.fecha_regreso or '',
            'hora': l.hora or '',
            'maps_ida': l.maps_ida or '',
            'maps_regreso': l.maps_regreso or '',
            'moneda': l.moneda,
            'precio': l.precio
        })
    return render_template('ver_cotizador.html', cotizador=cotizador, lugares_json=lugares_serializados)

@bp.route('/cotizadores/lugar/<int:id>', methods=['PUT'])
def actualizar_lugar(id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    lugar = CotizadorLugar.query.get_or_404(id)
    data = request.get_json()
    lugar.nombre = data.get('nombre', lugar.nombre)
    lugar.provincia = data.get('provincia', lugar.provincia)
    lugar.duracion = data.get('duracion', lugar.duracion)
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

@bp.route('/api/cotizadores/unico')
def cotizador_unico():
    c = Cotizador.query.first()
    if not c:
        return jsonify({'slug': None}), 404
    return jsonify({'slug': c.slug})

@bp.route('/api/cotizadores/export-json')
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
