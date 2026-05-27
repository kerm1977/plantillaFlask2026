import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from PIL import Image
from models import Raffle, RaffleSelection, Hiker, User
from db import db
from routes import bp, _PROJECT_ROOT

UPLOAD_FOLDER = os.path.join(_PROJECT_ROOT, 'static', 'uploads', 'rifas')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Asegurar que el directorio de uploads exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==========================================
# API DE BÚSQUEDA DE HIKER (AUTOCOMPLETE)
# ==========================================

@bp.route('/api/hikers/search')
def search_hikers():
    """API para buscar hikers por cédula o nombre (para autocomplete)."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'hikers': []})
    
    # Buscar por cédula exacta o nombre parcial
    hikers = Hiker.query.filter(
        (Hiker.cedula.ilike(f'%{query}%')) | 
        (Hiker.nombre_completo.ilike(f'%{query}%'))
    ).limit(10).all()
    
    results = [{'cedula': h.cedula, 'nombre_completo': h.nombre_completo, 'telefono': h.telefono} 
               for h in hikers]
    
    return jsonify({'hikers': results})


# ==========================================
# RIFAS PÚBLICAS
# ==========================================

@bp.route('/rifas')
def list_rifas():
    """Vista pública de rifas disponibles."""
    # ── Estadísticas globales (todas las rifas, no solo activas) ──
    all_rifas = Raffle.query.all()
    stats_total_rifas  = len(all_rifas)
    stats_activas      = sum(1 for r in all_rifas if r.is_active)
    stats_cerradas     = stats_total_rifas - stats_activas
    stats_meta         = 0
    stats_recaudado    = 0
    for r in all_rifas:
        stats_meta += 100 * r.price
        vendidos = RaffleSelection.query.filter_by(raffle_id=r.id, is_canceled=False).count()
        stats_recaudado += vendidos * r.price
    stats_porcentaje = round(stats_recaudado / stats_meta * 100, 1) if stats_meta > 0 else 0
    stats = {
        'total_rifas':  stats_total_rifas,
        'activas':      stats_activas,
        'cerradas':     stats_cerradas,
        'meta':         stats_meta,
        'recaudado':    stats_recaudado,
        'pendiente':    stats_meta - stats_recaudado,
        'porcentaje':   stats_porcentaje,
    }

    rifas = Raffle.query.filter_by(is_active=True).order_by(Raffle.raffle_date.desc()).all()
    
    raffle_data = []
    for r in rifas:
        total_sold = RaffleSelection.query.filter_by(
            raffle_id=r.id, is_canceled=False
        ).count()
        try:
            winners = json.loads(r.winning_numbers) if r.winning_numbers else []
        except:
            winners = []
        
        winners_info = []
        for num in winners:
            sel = RaffleSelection.query.filter_by(raffle_id=r.id, number=num, is_canceled=False).first()
            winners_info.append({'number': num, 'name': sel.customer_name if sel else 'Sin asignar'})
        
        raffle_data.append({
            'id': r.id,
            'raffle_number': r.raffle_number,
            'name': r.name,
            'price': r.price,
            'prize': r.prize,
            'detail': r.detail,
            'raffle_date': r.raffle_date.strftime('%Y-%m-%d') if r.raffle_date else '',
            'raffle_time': r.raffle_time,
            'image_filename': r.image_filename,
            'winning_numbers': winners,
            'winners_info': winners_info,
            'total_sold': total_sold,
            'total_available': 100 - total_sold
        })
    
    return render_template('rifas.html', rifas=raffle_data, stats=stats)


@bp.route('/rifas/<int:raffle_id>')
def rifa_detalle(raffle_id):
    """Detalle de rifa y selección de números."""
    rifa = Raffle.query.get_or_404(raffle_id)
    
    if not rifa.is_active:
        flash('Esta rifa no está activa', 'warning')
        return redirect(url_for('main.list_rifas'))
    
    # Obtener números ya seleccionados (no cancelados)
    selections = RaffleSelection.query.filter_by(
        raffle_id=raffle_id, is_canceled=False
    ).all()
    selected_numbers = [s.number for s in selections]
    
    # Agrupar selecciones por cliente (phone)
    grouped_selections = {}
    for s in selections:
        key = s.customer_phone
        if key not in grouped_selections:
            grouped_selections[key] = {
                'name': s.customer_name,
                'phone': s.customer_phone,
                'numbers': [],
                'total': 0
            }
        grouped_selections[key]['numbers'].append(s.number)
        grouped_selections[key]['total'] += rifa.price
    
    # Números disponibles (00-99)
    available_numbers = [f"{i:02d}" for i in range(100) if f"{i:02d}" not in selected_numbers]
    
    try:
        winners = json.loads(rifa.winning_numbers) if rifa.winning_numbers else []
    except:
        winners = []
    
    number_to_name = {s.number: s.customer_name for s in selections}
    winners_info = [{'number': num, 'name': number_to_name.get(num, 'Sin asignar')} for num in winners]
    
    return render_template('rifa_detalle.html', rifa=rifa, available_numbers=available_numbers, 
                         selected_numbers=selected_numbers, winners=winners,
                         winners_info=winners_info, grouped_selections=grouped_selections)


@bp.route('/api/rifas/<int:raffle_id>/select-multiple', methods=['POST'])
def select_multiple_numbers(raffle_id):
    """API para seleccionar múltiples números a la vez."""
    rifa = Raffle.query.get_or_404(raffle_id)
    
    if not rifa.is_active:
        return jsonify({'error': 'Rifa no activa'}), 400
    
    data = request.get_json()
    numbers = data.get('numbers', [])
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_cedula = data.get('customer_cedula', '').strip()
    pin = data.get('pin', '').strip()
    
    if not numbers or not customer_name or not customer_phone or not pin:
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    
    if len(pin) != 4 or not pin.isalnum():
        return jsonify({'error': 'El PIN debe tener 4 caracteres alfanuméricos'}), 400
    
    # Verificar que los números estén disponibles
    existing_numbers = RaffleSelection.query.filter(
        RaffleSelection.raffle_id == raffle_id,
        RaffleSelection.number.in_(numbers),
        RaffleSelection.is_canceled == False
    ).all()
    
    if existing_numbers:
        existing_nums = [s.number for s in existing_numbers]
        return jsonify({'error': f'Números ya seleccionados: {", ".join(existing_nums)}'}), 400
    
    # Crear o reutilizar selecciones (UPDATE si fue cancelada, INSERT si es nueva)
    try:
        created_selections = []
        for number in numbers:
            canceled_row = RaffleSelection.query.filter_by(
                raffle_id=raffle_id, number=number, is_canceled=True
            ).first()
            
            if canceled_row:
                canceled_row.customer_name = customer_name
                canceled_row.customer_phone = customer_phone
                canceled_row.customer_cedula = customer_cedula
                canceled_row.pin = pin
                canceled_row.selection_password = ''
                canceled_row.payment_method = 'No especificado'
                canceled_row.is_canceled = False
                canceled_row.created_at = datetime.utcnow()
                created_selections.append(canceled_row)
            else:
                selection = RaffleSelection(
                    raffle_id=raffle_id,
                    number=number,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    customer_cedula=customer_cedula,
                    pin=pin,
                    selection_password='',
                    payment_method='No especificado'
                )
                db.session.add(selection)
                created_selections.append(selection)
        
        db.session.commit()
        return jsonify({'ok': True, 'count': len(created_selections), 'selection_ids': [s.id for s in created_selections]})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar: {str(e)}'}), 500


@bp.route('/api/rifas/<int:raffle_id>/release-numbers', methods=['POST'])
def release_numbers(raffle_id):
    """API para liberar números seleccionados con phone + PIN."""
    data = request.get_json()
    phone = data.get('phone', '').strip()
    pin = data.get('pin', '').strip()
    
    if not phone or not pin:
        return jsonify({'error': 'Teléfono y PIN requeridos'}), 400
    
    selections = RaffleSelection.query.filter(
        RaffleSelection.raffle_id == raffle_id,
        RaffleSelection.customer_phone == phone,
        RaffleSelection.pin == pin,
        RaffleSelection.is_canceled == False
    ).all()
    
    if not selections:
        return jsonify({'error': 'No se encontraron selecciones con ese teléfono y PIN'}), 404
    
    count = 0
    for sel in selections:
        sel.is_canceled = True
        count += 1
    
    db.session.commit()
    
    return jsonify({'ok': True, 'count': count})


@bp.route('/api/rifas/<int:raffle_id>/admin-release', methods=['POST'])
def admin_release_numbers(raffle_id):
    """API para superadmin liberar números sin PIN."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 403
    
    user = User.query.get(session['user_id'])
    if not user or user.email not in ['kenth1977@gmail.com', 'lthikingcr@gmail.com']:
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    phone = data.get('phone', '').strip()
    
    selections = RaffleSelection.query.filter(
        RaffleSelection.raffle_id == raffle_id,
        RaffleSelection.customer_phone == phone,
        RaffleSelection.is_canceled == False
    ).all()
    
    count = 0
    for sel in selections:
        sel.is_canceled = True
        count += 1
    
    db.session.commit()
    return jsonify({'ok': True, 'count': count})


@bp.route('/api/rifas/<int:raffle_id>/select', methods=['POST'])
def select_number(raffle_id):
    """API para seleccionar un número."""
    rifa = Raffle.query.get_or_404(raffle_id)
    
    if not rifa.is_active:
        return jsonify({'error': 'Rifa no activa'}), 400
    
    data = request.get_json()
    number = data.get('number')
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_cedula = data.get('customer_cedula', '').strip()
    pin = data.get('pin', '').strip()
    
    if not number or not customer_name or not customer_phone or not pin:
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    
    if len(pin) != 4 or not pin.isalnum():
        return jsonify({'error': 'El PIN debe tener 4 caracteres alfanuméricos'}), 400
    
    # Verificar que el número esté disponible
    existing = RaffleSelection.query.filter_by(
        raffle_id=raffle_id, number=number, is_canceled=False
    ).first()
    if existing:
        return jsonify({'error': 'Número ya seleccionado'}), 400
    
    # Crear selección
    selection = RaffleSelection(
        raffle_id=raffle_id,
        number=number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_cedula=customer_cedula,
        pin=pin,
        payment_method='No especificado'
    )
    
    db.session.add(selection)
    db.session.commit()
    
    return jsonify({'ok': True, 'selection_id': selection.id})


@bp.route('/rifas/mis-selecciones')
def mis_selecciones():
    """Buscar selecciones por teléfono y PIN."""
    return render_template('mis_selecciones_busqueda.html')


@bp.route('/rifas/mis-selecciones/ver', methods=['POST'])
def ver_mis_selecciones():
    """Ver selecciones de una persona (teléfono + PIN)."""
    data = request.get_json()
    phone = data.get('phone', '').strip()
    pin = data.get('pin', '').strip()
    
    if not phone or not pin:
        return jsonify({'error': 'Faltan teléfono y PIN'}), 400
    
    # Buscar selecciones activas con ese teléfono y PIN
    selections = RaffleSelection.query.filter_by(
        customer_phone=phone, pin=pin, is_canceled=False
    ).all()
    
    if not selections:
        return jsonify({'error': 'No se encontraron selecciones con ese teléfono y PIN'}), 404
    
    # Agrupar por rifa
    raffle_groups = {}
    for sel in selections:
        raffle_id = sel.raffle_id
        if raffle_id not in raffle_groups:
            raffle_groups[raffle_id] = {
                'raffle': sel.raffle,
                'selections': [],
                'total': 0
            }
        raffle_groups[raffle_id]['selections'].append(sel)
        raffle_groups[raffle_id]['total'] += sel.raffle.price
    
    results = []
    for raffle_id, group in raffle_groups.items():
        results.append({
            'raffle_id': raffle_id,
            'raffle_name': group['raffle'].name,
            'raffle_number': group['raffle'].raffle_number,
            'price': group['raffle'].price,
            'selections': [{'id': s.id, 'number': s.number} for s in group['selections']],
            'total': group['total'],
            'customer_name': group['selections'][0].customer_name
        })
    
    return jsonify({'ok': True, 'selections': results})


@bp.route('/rifas/mi-seleccion/<int:selection_id>')
def mi_seleccion(selection_id):
    """Ver y editar selección propia."""
    selection = RaffleSelection.query.get_or_404(selection_id)
    
    if not selection.raffle.is_active:
        flash('Esta rifa no está activa', 'warning')
        return redirect(url_for('main.list_rifas'))
    
    try:
        winners = json.loads(selection.raffle.winning_numbers) if selection.raffle.winning_numbers else []
    except:
        winners = []
    
    is_winner = selection.number in winners if not selection.is_canceled else False
    
    return render_template('mi_seleccion.html', selection=selection, winners=winners, is_winner=is_winner)


@bp.route('/api/rifas/seleccion/<int:selection_id>/cancelar', methods=['POST'])
def cancelar_seleccion(selection_id):
    """Cancelar selección propia (requiere teléfono + PIN)."""
    selection = RaffleSelection.query.get_or_404(selection_id)
    
    # Verificar teléfono + PIN
    data = request.get_json()
    phone = data.get('phone', '').strip()
    pin = data.get('pin', '').strip()
    
    if selection.customer_phone != phone or selection.pin != pin:
        return jsonify({'error': 'Teléfono o PIN incorrecto'}), 403
    
    selection.is_canceled = True
    db.session.commit()
    
    return jsonify({'ok': True})


# ==========================================
# RIFAS - ADMIN (SUPERUSUARIO)
# ==========================================

@bp.route('/admin/rifas')
def admin_rifas():
    """Panel de administración de rifas."""
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    
    rifas = Raffle.query.order_by(Raffle.created_at.desc()).all()
    
    raffle_data = []
    for r in rifas:
        total_sold = RaffleSelection.query.filter_by(
            raffle_id=r.id, is_canceled=False
        ).count()
        total_canceled = RaffleSelection.query.filter_by(
            raffle_id=r.id, is_canceled=True
        ).count()
        
        raffle_data.append({
            'id': r.id,
            'raffle_number': r.raffle_number,
            'name': r.name,
            'price': r.price,
            'raffle_date': r.raffle_date.strftime('%Y-%m-%d') if r.raffle_date else '',
            'total_sold': total_sold,
            'total_canceled': total_canceled,
            'is_active': r.is_active
        })
    
    return render_template('admin_rifas.html', rifas=raffle_data)


@bp.route('/admin/rifas/crear', methods=['GET', 'POST'])
def crear_rifa():
    """Crear nueva rifa."""
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        image_file = request.files.get('image')
        
        if not image_file or image_file.filename == '' or not allowed_file(image_file.filename):
            flash('Debe subir una imagen válida (PNG, JPG, JPEG)', 'danger')
            return redirect(request.url)
        
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Procesar imagen (resize si es muy grande)
        try:
            img = Image.open(image_file)
            if img.width > 800:
                ratio = 800 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((800, new_height), Image.LANCZOS)
            img.save(filepath)
        except Exception as e:
            flash(f'Error al procesar la imagen: {e}', 'danger')
            return redirect(request.url)
        
        # Crear rifa
        rifa = Raffle(
            raffle_number=request.form.get('raffle_number'),
            name=request.form.get('name'),
            price=float(request.form.get('price')),
            prize=request.form.get('prize'),
            detail=request.form.get('detail'),
            raffle_date=datetime.strptime(request.form.get('raffle_date'), '%Y-%m-%d').date(),
            raffle_time=request.form.get('raffle_time'),
            image_filename=filename,
            sinpe_name_default=request.form.get('sinpe_name_default'),
            sinpe_phone_default=request.form.get('sinpe_phone_default')
        )
        
        try:
            db.session.add(rifa)
            db.session.commit()
            flash('Rifa creada exitosamente', 'success')
            return redirect(url_for('main.admin_rifas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(request.url)
    
    return render_template('crear_rifa.html')


@bp.route('/admin/rifas/<int:raffle_id>/editar', methods=['GET', 'POST'])
def editar_rifa(raffle_id):
    """Editar rifa existente."""
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    
    rifa = Raffle.query.get_or_404(raffle_id)
    
    if request.method == 'POST':
        rifa.raffle_number = request.form.get('raffle_number')
        rifa.name = request.form.get('name')
        rifa.price = float(request.form.get('price'))
        rifa.prize = request.form.get('prize')
        rifa.detail = request.form.get('detail')
        rifa.raffle_date = datetime.strptime(request.form.get('raffle_date'), '%Y-%m-%d').date()
        rifa.raffle_time = request.form.get('raffle_time')
        rifa.sinpe_name_default = request.form.get('sinpe_name_default')
        rifa.sinpe_phone_default = request.form.get('sinpe_phone_default')
        rifa.is_active = 'is_active' in request.form
        
        # Procesar nueva imagen si se subió
        image_file = request.files.get('image')
        if image_file and image_file.filename != '' and allowed_file(image_file.filename):
            # Eliminar imagen anterior
            old_filepath = os.path.join(UPLOAD_FOLDER, rifa.image_filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
            
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            try:
                img = Image.open(image_file)
                if img.width > 800:
                    ratio = 800 / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((800, new_height), Image.LANCZOS)
                img.save(filepath)
                rifa.image_filename = filename
            except Exception as e:
                flash(f'Error al procesar la imagen: {e}', 'danger')
                return redirect(request.url)
        
        try:
            db.session.commit()
            flash('Rifa actualizada exitosamente', 'success')
            return redirect(url_for('main.admin_rifas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(request.url)
    
    return render_template('editar_rifa.html', rifa=rifa)


@bp.route('/admin/rifas/<int:raffle_id>/eliminar', methods=['DELETE'])
def eliminar_rifa(raffle_id):
    """Eliminar rifa."""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    rifa = Raffle.query.get_or_404(raffle_id)
    
    # Eliminar imagen
    filepath = os.path.join(UPLOAD_FOLDER, rifa.image_filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    db.session.delete(rifa)
    db.session.commit()
    
    return jsonify({'ok': True})


@bp.route('/admin/rifas/seleccion/<int:selection_id>/eliminar', methods=['DELETE'])
def admin_eliminar_seleccion(selection_id):
    """Superusuario: Eliminar una selección sin requerir PIN."""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    selection = RaffleSelection.query.get_or_404(selection_id)
    selection.is_canceled = True
    db.session.commit()
    
    return jsonify({'ok': True})


@bp.route('/admin/rifas/<int:raffle_id>/ganadores', methods=['POST'])
def establecer_ganadores(raffle_id):
    """Establecer números ganadores."""
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    rifa = Raffle.query.get_or_404(raffle_id)
    data = request.get_json()
    winners = data.get('winners', [])
    
    rifa.winning_numbers = json.dumps(winners)
    db.session.commit()
    
    return jsonify({'ok': True})


@bp.route('/admin/rifas/<int:raffle_id>/selecciones')
def ver_selecciones(raffle_id):
    """Ver todas las selecciones de una rifa."""
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    
    rifa = Raffle.query.get_or_404(raffle_id)
    selecciones = RaffleSelection.query.filter_by(raffle_id=raffle_id).order_by(RaffleSelection.created_at.desc()).all()
    
    try:
        winners = json.loads(rifa.winning_numbers) if rifa.winning_numbers else []
    except:
        winners = []
    
    return render_template('rifa_selecciones.html', rifa=rifa, selecciones=selecciones, winners=winners)


@bp.route('/api/rifas/<int:raffle_id>/find-winner/<string:number>', methods=['GET'])
def find_winner(raffle_id, number):
    """API para buscar quién tiene un número específico en una rifa."""
    user = User.query.get(session.get('user_id'))
    if not user or user.email not in ['kenth1977@gmail.com', 'lthikingcr@gmail.com']:
        return jsonify({'error': 'No autorizado'}), 403

    num = number.zfill(2)
    selection = RaffleSelection.query.filter_by(
        raffle_id=raffle_id,
        number=num,
        is_canceled=False
    ).first()

    if selection:
        return jsonify({'winner': {
            'name': selection.customer_name,
            'phone': selection.customer_phone,
            'cedula': selection.customer_cedula or ''
        }})
    return jsonify({'winner': None})
