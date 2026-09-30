# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
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


def _rifa_dict(rifa):
    return {
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
    }


def _grouped_selections(rifa):
    """Agrupa las selecciones de una rifa por teléfono del cliente."""
    selections = RaffleSelection.query.filter_by(raffle_id=rifa.id).all()
    grouped = {}
    for s in selections:
        key = s.customer_phone
        display_name = s.customer_name if s.customer_name else 'Sin nombre'
        if key not in grouped:
            grouped[key] = {'name': display_name, 'phone': s.customer_phone, 'items': []}
        grouped[key]['items'].append(s)

    grouped_selections = {}
    for key, g in grouped.items():
        grouped_selections[key] = {
            'name': g['name'],
            'phone': g['phone'],
            'numbers': [s.number for s in g['items']],
            'total': sum(rifa.price for s in g['items'] if not s.is_canceled),
            'is_paid': all(s.is_paid for s in g['items']),
            'is_canceled': any(s.is_canceled for s in g['items'])
        }
    return grouped_selections


def _apply_rifa_data(rifa, rifa_data):
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


def _add_selections(raffle_id, selections_dict):
    for phone, sel_data in selections_dict.items():
        for number in sel_data['numbers']:
            db.session.add(RaffleSelection(
                raffle_id=raffle_id,
                number=number,
                customer_name=sel_data['name'],
                customer_phone=sel_data['phone'],
                is_paid=sel_data['is_paid'],
                is_canceled=sel_data['is_canceled']
            ))


# ==========================================
# EXPORTAR RIFA INDIVIDUAL A JSON
# ==========================================
@bp.route('/api/rifas/<int:raffle_id>/export-json', methods=['GET'])
def export_raffle_json(raffle_id):
    """Exporta una rifa específica y todas sus selecciones a JSON."""
    try:
        rifa = Raffle.query.get_or_404(raffle_id)
        data = {
            'metadata': {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'export_type': 'single_raffle'
            },
            'raffle': _rifa_dict(rifa),
            'selections': _grouped_selections(rifa)
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
        _add_selections(raffle_id, data['selections'])

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
        rifas_data = []
        for rifa in Raffle.query.all():
            row = _rifa_dict(rifa)
            row['selections'] = _grouped_selections(rifa)
            rifas_data.append(row)

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
                _apply_rifa_data(rifa, rifa_data)
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
            _add_selections(rifa.id, rifa_data['selections'])

        db.session.commit()
        return jsonify({'success': True, 'message': 'Importación exitosa'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
