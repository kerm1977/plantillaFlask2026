import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import request, jsonify, render_template, redirect, url_for, flash, session
from PIL import Image
from models import Raffle, RaffleSelection, User
from db import db
from routes import bp, _PROJECT_ROOT

UPLOAD_FOLDER     = os.path.join(_PROJECT_ROOT, 'static', 'uploads', 'rifas')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _allowed_rifa_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_rifa_image(image_file, filepath):
    img = Image.open(image_file)
    if img.width > 800:
        ratio = 800 / img.width
        img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
    img.save(filepath)


# ── PANEL ADMIN ──────────────────────────────────────────────────────────────

@bp.route('/admin/rifas')
def admin_rifas():
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    rifas = Raffle.query.order_by(Raffle.created_at.desc()).all()
    raffle_data = []
    for r in rifas:
        total_sold     = RaffleSelection.query.filter_by(raffle_id=r.id, is_canceled=False).count()
        total_canceled = RaffleSelection.query.filter_by(raffle_id=r.id, is_canceled=True).count()
        raffle_data.append({
            'id': r.id, 'raffle_number': r.raffle_number, 'name': r.name,
            'price': r.price, 'raffle_date': r.raffle_date.strftime('%Y-%m-%d') if r.raffle_date else '',
            'total_sold': total_sold, 'total_canceled': total_canceled, 'is_active': r.is_active
        })
    return render_template('admin_rifas.html', rifas=raffle_data)


# ── CREAR RIFA ───────────────────────────────────────────────────────────────

@bp.route('/admin/rifas/crear', methods=['GET', 'POST'])
def crear_rifa():
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        image_file = request.files.get('image')
        if not image_file or image_file.filename == '' or not _allowed_rifa_file(image_file.filename):
            flash('Debe subir una imagen válida (PNG, JPG, JPEG)', 'danger')
            return redirect(request.url)
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            _save_rifa_image(image_file, filepath)
        except Exception as e:
            flash(f'Error al procesar la imagen: {e}', 'danger')
            return redirect(request.url)
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


# ── EDITAR RIFA ──────────────────────────────────────────────────────────────

@bp.route('/admin/rifas/<int:raffle_id>/editar', methods=['GET', 'POST'])
def editar_rifa(raffle_id):
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    rifa = Raffle.query.get_or_404(raffle_id)
    if request.method == 'POST':
        rifa.raffle_number      = request.form.get('raffle_number')
        rifa.name               = request.form.get('name')
        rifa.price              = float(request.form.get('price'))
        rifa.prize              = request.form.get('prize')
        rifa.detail             = request.form.get('detail')
        rifa.raffle_date        = datetime.strptime(request.form.get('raffle_date'), '%Y-%m-%d').date()
        rifa.raffle_time        = request.form.get('raffle_time')
        rifa.sinpe_name_default = request.form.get('sinpe_name_default')
        rifa.sinpe_phone_default= request.form.get('sinpe_phone_default')
        rifa.is_active          = 'is_active' in request.form
        image_file = request.files.get('image')
        if image_file and image_file.filename != '' and _allowed_rifa_file(image_file.filename):
            old_path = os.path.join(UPLOAD_FOLDER, rifa.image_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            try:
                _save_rifa_image(image_file, filepath)
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


# ── ELIMINAR RIFA ────────────────────────────────────────────────────────────

@bp.route('/admin/rifas/<int:raffle_id>/eliminar', methods=['DELETE'])
def eliminar_rifa(raffle_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    rifa = Raffle.query.get_or_404(raffle_id)
    filepath = os.path.join(UPLOAD_FOLDER, rifa.image_filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(rifa)
    db.session.commit()
    return jsonify({'ok': True})


# ── ELIMINAR SELECCIÓN (admin) ───────────────────────────────────────────────

@bp.route('/admin/rifas/seleccion/<int:selection_id>/eliminar', methods=['DELETE'])
def admin_eliminar_seleccion(selection_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    selection = RaffleSelection.query.get_or_404(selection_id)
    selection.is_canceled = True
    db.session.commit()
    return jsonify({'ok': True})


# ── ESTABLECER GANADORES ─────────────────────────────────────────────────────

@bp.route('/admin/rifas/<int:raffle_id>/ganadores', methods=['POST'])
def establecer_ganadores(raffle_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    rifa = Raffle.query.get_or_404(raffle_id)
    data = request.get_json()
    rifa.winning_numbers = json.dumps(data.get('winners', []))
    db.session.commit()
    return jsonify({'ok': True})


# ── VER SELECCIONES DE UNA RIFA ──────────────────────────────────────────────

@bp.route('/admin/rifas/<int:raffle_id>/selecciones')
def ver_selecciones(raffle_id):
    if session.get('role') != 'Superusuario':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.home'))
    rifa = Raffle.query.get_or_404(raffle_id)
    selecciones = RaffleSelection.query.filter_by(raffle_id=raffle_id).order_by(
        RaffleSelection.created_at.desc()).all()
    try:
        winners = json.loads(rifa.winning_numbers) if rifa.winning_numbers else []
    except Exception:
        winners = []
    return render_template('rifa_selecciones.html', rifa=rifa, selecciones=selecciones, winners=winners)


# ── BUSCAR GANADOR POR NÚMERO ────────────────────────────────────────────────

@bp.route('/api/rifas/<int:raffle_id>/find-winner/<string:number>', methods=['GET'])
def find_winner(raffle_id, number):
    user = User.query.get(session.get('user_id'))
    if not user or user.email not in ['kenth1977@gmail.com', 'lthikingcr@gmail.com']:
        return jsonify({'error': 'No autorizado'}), 403
    num = number.zfill(2)
    selection = RaffleSelection.query.filter_by(
        raffle_id=raffle_id, number=num, is_canceled=False).first()
    if selection:
        return jsonify({'winner': {'name': selection.customer_name,
                                   'phone': selection.customer_phone,
                                   'cedula': selection.customer_cedula or ''}})
    return jsonify({'winner': None})


# ── ACTUALIZAR ESTADO DE PAGO ───────────────────────────────────────────────────

@bp.route('/api/rifas/<int:raffle_id>/toggle-payment/<string:phone>', methods=['POST'])
def toggle_payment(raffle_id, phone):
    user = User.query.get(session.get('user_id'))
    if not user or user.email not in ['kenth1977@gmail.com', 'lthikingcr@gmail.com']:
        return jsonify({'error': 'No autorizado'}), 403
    selections = RaffleSelection.query.filter_by(
        raffle_id=raffle_id, customer_phone=phone).all()
    if not selections:
        return jsonify({'error': 'Selección no encontrada'}), 404
    # Alternar estado de pago de todas las selecciones de este teléfono
    new_status = not all(sel.is_paid for sel in selections)
    for sel in selections:
        sel.is_paid = new_status
    db.session.commit()
    return jsonify({'ok': True, 'is_paid': new_status, 'is_canceled': any(s.is_canceled for s in selections)})
