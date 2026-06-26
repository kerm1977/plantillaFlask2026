import json
from datetime import datetime
from flask import request, jsonify
from models import Raffle, RaffleSelection
from db import db
from routes import bp


@bp.route('/api/rifas/<int:raffle_id>/select-multiple', methods=['POST'])
def select_multiple_numbers(raffle_id):
    rifa = Raffle.query.get_or_404(raffle_id)
    if not rifa.is_active:
        return jsonify({'error': 'Rifa no activa'}), 400
    data = request.get_json()
    numbers        = data.get('numbers', [])
    customer_name  = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_cedula= data.get('customer_cedula', '').strip()
    pin            = data.get('pin', '').strip()
    if not numbers or not customer_name or not customer_phone or not pin:
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    if len(pin) != 4 or not pin.isalnum():
        return jsonify({'error': 'El PIN debe tener 4 caracteres alfanuméricos'}), 400
    existing = RaffleSelection.query.filter(
        RaffleSelection.raffle_id == raffle_id,
        RaffleSelection.number.in_(numbers),
        RaffleSelection.is_canceled == False
    ).all()
    if existing:
        return jsonify({'error': f'Números ya seleccionados: {", ".join(s.number for s in existing)}'}), 400
    try:
        created = []
        for number in numbers:
            canceled_row = RaffleSelection.query.filter_by(
                raffle_id=raffle_id, number=number, is_canceled=True).first()
            if canceled_row:
                canceled_row.customer_name   = customer_name
                canceled_row.customer_phone  = customer_phone
                canceled_row.customer_cedula = customer_cedula
                canceled_row.pin             = pin
                canceled_row.selection_password = ''
                canceled_row.payment_method  = 'No especificado'
                canceled_row.is_canceled     = False
                canceled_row.created_at      = datetime.utcnow()
                created.append(canceled_row)
            else:
                sel = RaffleSelection(
                    raffle_id=raffle_id, number=number,
                    customer_name=customer_name, customer_phone=customer_phone,
                    customer_cedula=customer_cedula, pin=pin,
                    selection_password='', payment_method='No especificado')
                db.session.add(sel)
                created.append(sel)
        db.session.commit()
        return jsonify({'ok': True, 'count': len(created), 'selection_ids': [s.id for s in created]})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar: {str(e)}'}), 500


@bp.route('/api/rifas/<int:raffle_id>/select', methods=['POST'])
def select_number(raffle_id):
    rifa = Raffle.query.get_or_404(raffle_id)
    if not rifa.is_active:
        return jsonify({'error': 'Rifa no activa'}), 400
    data = request.get_json()
    number         = data.get('number')
    customer_name  = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_cedula= data.get('customer_cedula', '').strip()
    pin            = data.get('pin', '').strip()
    if not number or not customer_name or not customer_phone or not pin:
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    if len(pin) != 4 or not pin.isalnum():
        return jsonify({'error': 'El PIN debe tener 4 caracteres alfanuméricos'}), 400
    if RaffleSelection.query.filter_by(raffle_id=raffle_id, number=number, is_canceled=False).first():
        return jsonify({'error': 'Número ya seleccionado'}), 400
    sel = RaffleSelection(raffle_id=raffle_id, number=number, customer_name=customer_name,
                          customer_phone=customer_phone, customer_cedula=customer_cedula,
                          pin=pin, payment_method='No especificado')
    db.session.add(sel)
    db.session.commit()
    return jsonify({'ok': True, 'selection_id': sel.id})


@bp.route('/api/rifas/<int:raffle_id>/release-numbers', methods=['POST'])
def release_numbers_with_pin(raffle_id):
    """Liberar números usando teléfono y PIN del cliente"""
    rifa = Raffle.query.get_or_404(raffle_id)
    data = request.get_json()
    phone = data.get('phone', '').strip()
    pin = data.get('pin', '').strip()
    if not phone or not pin:
        return jsonify({'error': 'Faltan teléfono y PIN'}), 400
    selections = RaffleSelection.query.filter_by(
        raffle_id=raffle_id,
        customer_phone=phone,
        pin=pin,
        is_canceled=False
    ).all()
    if not selections:
        return jsonify({'error': 'No se encontraron selecciones con ese teléfono y PIN'}), 404
    try:
        for sel in selections:
            sel.is_canceled = True
        db.session.commit()
        return jsonify({'ok': True, 'count': len(selections)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al liberar: {str(e)}'}), 500


@bp.route('/api/rifas/<int:raffle_id>/admin-release', methods=['POST'])
def admin_release_numbers(raffle_id):
    """Liberar números como superusuario (solo requiere teléfono)"""
    from flask import session
    if session.get('email') not in ['kenth1977@gmail.com', 'lthikingcr@gmail.com']:
        return jsonify({'error': 'No autorizado'}), 403
    rifa = Raffle.query.get_or_404(raffle_id)
    data = request.get_json()
    phone = data.get('phone', '').strip()
    if not phone:
        return jsonify({'error': 'Falta el teléfono'}), 400
    selections = RaffleSelection.query.filter_by(
        raffle_id=raffle_id,
        customer_phone=phone,
        is_canceled=False
    ).all()
    if not selections:
        return jsonify({'error': 'No se encontraron selecciones para ese teléfono'}), 404
    try:
        for sel in selections:
            sel.is_canceled = True
        db.session.commit()
        return jsonify({'ok': True, 'count': len(selections)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al liberar: {str(e)}'}), 500
