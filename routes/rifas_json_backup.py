# ==========================================
# RUTAS DE RESPALDO JSON PARA RIFAS
# ==========================================
# Archivo independiente para exportar/importar JSON
# NO TOCA DATOS EXISTENTES - Solo lectura/escritura controlada
# ==========================================

import json
from datetime import datetime
from flask import jsonify, request
from models import Raffle, RaffleSelection
from db import db
from routes import bp


# ==========================================
# EXPORTAR RIFA INDIVIDUAL A JSON
# ==========================================
@bp.route('/api/rifas/<int:raffle_id>/export-json', methods=['GET'])
def export_raffle_json(raffle_id):
    """Exporta una rifa específica y todas sus selecciones a JSON."""
    try:
        rifa = Raffle.query.get_or_404(raffle_id)
        selections = RaffleSelection.query.filter_by(raffle_id=raffle_id).all()

        # Agrupar selecciones por teléfono
        grouped = {}
        for s in selections:
            key = s.customer_phone
            display_name = s.customer_name if s.customer_name else 'Sin nombre'
            if key not in grouped:
                grouped[key] = {'name': display_name, 'phone': s.customer_phone, 'items': []}
            grouped[key]['items'].append(s)

        grouped_selections = {}
        for key, g in grouped.items():
            numbers = [s.number for s in g['items']]
            total = sum(rifa.price for s in g['items'] if not s.is_canceled)
            is_paid = all(s.is_paid for s in g['items'])
            is_canceled = any(s.is_canceled for s in g['items'])
            grouped_selections[key] = {
                'name': g['name'],
                'phone': g['phone'],
                'numbers': numbers,
                'total': total,
                'is_paid': is_paid,
                'is_canceled': is_canceled
            }

        data = {
            'metadata': {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'export_type': 'single_raffle'
            },
            'raffle': {
                'id': rifa.id,
                'name': rifa.name,
                'raffle_number': rifa.raffle_number,
                'detail': rifa.detail,
                'prize': rifa.prize,
                'price': rifa.price,
                'raffle_date': rifa.raffle_date.strftime('%d/%m/%Y') if rifa.raffle_date else '',
                'raffle_time': rifa.raffle_time if rifa.raffle_time else '',
                'sinpe_name': rifa.sinpe_name_default if rifa.sinpe_name_default else '',
                'sinpe_phone': rifa.sinpe_phone_default if rifa.sinpe_phone_default else '',
                'is_active': rifa.is_active,
                'image_filename': rifa.image_filename,
                'winning_numbers': rifa.winning_numbers
            },
            'selections': grouped_selections
        }

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================
# IMPORTAR RIFA INDIVIDUAL DESDE JSON
# ==========================================
@bp.route('/api/rifas/<int:raffle_id>/import-json', methods=['POST'])
def import_raffle_json(raffle_id):
    """Importa selecciones de una rifa desde JSON."""
    try:
        data = request.get_json()
        if not data or 'selections' not in data:
            return jsonify({'error': 'Formato JSON inválido'}), 400

        rifa = Raffle.query.get_or_404(raffle_id)

        # Eliminar selecciones existentes de esta rifa
        RaffleSelection.query.filter_by(raffle_id=raffle_id).delete()

        # Recrear selecciones desde JSON
        for phone, sel_data in data['selections'].items():
            for number in sel_data['numbers']:
                selection = RaffleSelection(
                    raffle_id=raffle_id,
                    number=number,
                    customer_name=sel_data['name'],
                    customer_phone=sel_data['phone'],
                    is_paid=sel_data['is_paid'],
                    is_canceled=sel_data['is_canceled']
                )
                db.session.add(selection)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Importación exitosa'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==========================================
# EXPORTAR TODAS LAS RIFAS A JSON
# ==========================================
@bp.route('/api/rifas/export-all-json', methods=['GET'])
def export_all_rifas_json():
    """Exporta todas las rifas y sus selecciones a JSON."""
    try:
        all_rifas = Raffle.query.all()
        rifas_data = []

        for rifa in all_rifas:
            selections = RaffleSelection.query.filter_by(raffle_id=rifa.id).all()

            # Agrupar selecciones por teléfono
            grouped = {}
            for s in selections:
                key = s.customer_phone
                display_name = s.customer_name if s.customer_name else 'Sin nombre'
                if key not in grouped:
                    grouped[key] = {'name': display_name, 'phone': s.customer_phone, 'items': []}
                grouped[key]['items'].append(s)

            grouped_selections = {}
            for key, g in grouped.items():
                numbers = [s.number for s in g['items']]
                total = sum(rifa.price for s in g['items'] if not s.is_canceled)
                is_paid = all(s.is_paid for s in g['items'])
                is_canceled = any(s.is_canceled for s in g['items'])
                grouped_selections[key] = {
                    'name': g['name'],
                    'phone': g['phone'],
                    'numbers': numbers,
                    'total': total,
                    'is_paid': is_paid,
                    'is_canceled': is_canceled
                }

            rifas_data.append({
                'id': rifa.id,
                'name': rifa.name,
                'raffle_number': rifa.raffle_number,
                'detail': rifa.detail,
                'prize': rifa.prize,
                'price': rifa.price,
                'raffle_date': rifa.raffle_date.strftime('%d/%m/%Y') if rifa.raffle_date else '',
                'raffle_time': rifa.raffle_time if rifa.raffle_time else '',
                'sinpe_name': rifa.sinpe_name_default if rifa.sinpe_name_default else '',
                'sinpe_phone': rifa.sinpe_phone_default if rifa.sinpe_phone_default else '',
                'is_active': rifa.is_active,
                'image_filename': rifa.image_filename,
                'winning_numbers': rifa.winning_numbers,
                'selections': grouped_selections
            })

        data = {
            'metadata': {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'export_type': 'all_rifas',
                'total_rifas': len(rifas_data)
            },
            'rifas': rifas_data
        }

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================
# IMPORTAR TODAS LAS RIFAS DESDE JSON
# ==========================================
@bp.route('/api/rifas/import-all-json', methods=['POST'])
def import_all_rifas_json():
    """Importa todas las rifas y selecciones desde JSON."""
    try:
        data = request.get_json()
        if not data or 'rifas' not in data:
            return jsonify({'error': 'Formato JSON inválido'}), 400

        # Eliminar todas las selecciones existentes
        RaffleSelection.query.delete()

        # Recrear rifas y selecciones desde JSON
        for rifa_data in data['rifas']:
            # Actualizar rifa existente o crear nueva
            rifa = Raffle.query.get(rifa_data['id'])
            if rifa:
                rifa.name = rifa_data['name']
                rifa.raffle_number = rifa_data['raffle_number']
                rifa.detail = rifa_data['detail']
                rifa.prize = rifa_data['prize']
                rifa.price = rifa_data['price']
                rifa.sinpe_name_default = rifa_data['sinpe_name']
                rifa.sinpe_phone_default = rifa_data['sinpe_phone']
                rifa.is_active = rifa_data['is_active']
                rifa.image_filename = rifa_data['image_filename']
                rifa.winning_numbers = rifa_data['winning_numbers']
                # Parsear fecha y hora si existen
                if rifa_data['raffle_date']:
                    rifa.raffle_date = datetime.strptime(rifa_data['raffle_date'], '%d/%m/%Y')
                if rifa_data['raffle_time']:
                    rifa.raffle_time = rifa_data['raffle_time']
            else:
                # Crear nueva rifa
                rifa = Raffle(
                    name=rifa_data['name'],
                    raffle_number=rifa_data['raffle_number'],
                    detail=rifa_data['detail'],
                    prize=rifa_data['prize'],
                    price=rifa_data['price'],
                    sinpe_name_default=rifa_data['sinpe_name'],
                    sinpe_phone_default=rifa_data['sinpe_phone'],
                    is_active=rifa_data['is_active'],
                    image_filename=rifa_data['image_filename'],
                    winning_numbers=rifa_data['winning_numbers']
                )
                if rifa_data['raffle_date']:
                    rifa.raffle_date = datetime.strptime(rifa_data['raffle_date'], '%d/%m/%Y')
                if rifa_data['raffle_time']:
                    rifa.raffle_time = rifa_data['raffle_time']
                db.session.add(rifa)
                db.session.flush()  # Para obtener el ID

            # Recrear selecciones
            for phone, sel_data in rifa_data['selections'].items():
                for number in sel_data['numbers']:
                    selection = RaffleSelection(
                        raffle_id=rifa.id,
                        number=number,
                        customer_name=sel_data['name'],
                        customer_phone=sel_data['phone'],
                        is_paid=sel_data['is_paid'],
                        is_canceled=sel_data['is_canceled']
                    )
                    db.session.add(selection)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Importación exitosa'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
