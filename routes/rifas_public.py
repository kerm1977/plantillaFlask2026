import json
from flask import render_template, redirect, url_for, flash, request, jsonify
from models import Raffle, RaffleSelection, Hiker
from routes import bp


# ── BÚSQUEDA DE HIKER (AUTOCOMPLETE) ────────────────────────────────────────

@bp.route('/api/hikers/search')
def search_hikers():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'hikers': []})
    hikers = Hiker.query.filter(
        (Hiker.cedula.ilike(f'%{query}%')) |
        (Hiker.nombre_completo.ilike(f'%{query}%'))
    ).limit(10).all()
    results = [{'cedula': h.cedula, 'nombre_completo': h.nombre_completo, 'telefono': h.telefono}
               for h in hikers]
    return jsonify({'hikers': results})


# ── VISTA PÚBLICA: DETALLE ───────────────────────────────────────────────────

@bp.route('/rifas/<int:raffle_id>')
def rifa_detalle(raffle_id):
    rifa = Raffle.query.get_or_404(raffle_id)
    if not rifa.is_active:
        flash('Esta rifa no está activa', 'warning')
        return redirect(url_for('main.list_rifas'))
    selections = RaffleSelection.query.filter_by(raffle_id=raffle_id).all()
    selected_numbers = [s.number for s in selections if not s.is_canceled]
    grouped = {}
    for s in selections:
        key = s.customer_phone
        if key not in grouped:
            # Ocultar solo el contenido entre paréntesis (cedula)
            display_name = s.customer_name
            if display_name:
                import re
                # Eliminar todo lo que esté entre paréntesis
                display_name = re.sub(r'\([^)]*\)', '', display_name).strip()
            grouped[key] = {'name': display_name, 'phone': s.customer_phone, 'items': []}
        grouped[key]['items'].append(s)
    grouped_selections = {}
    for key, g in grouped.items():
        numbers = [s.number for s in g['items']]
        total = sum(rifa.price for s in g['items'] if not s.is_canceled)
        is_paid = all(s.is_paid for s in g['items'])
        is_canceled = any(s.is_canceled for s in g['items'])
        grouped_selections[key] = {'name': g['name'], 'phone': g['phone'],
                                   'numbers': numbers, 'total': total,
                                   'is_paid': is_paid, 'is_canceled': is_canceled}
    available_numbers = [f"{i:02d}" for i in range(100) if f"{i:02d}" not in selected_numbers]
    try:
        winners = json.loads(rifa.winning_numbers) if rifa.winning_numbers else []
    except Exception:
        winners = []
    number_to_name = {s.number: s.customer_name for s in selections}
    winners_info = [{'number': num, 'name': number_to_name.get(num, 'Sin asignar')} for num in winners]
    return render_template('rifa_detalle.html', rifa=rifa, available_numbers=available_numbers,
                           selected_numbers=selected_numbers, winners=winners,
                           winners_info=winners_info, grouped_selections=grouped_selections)


# ── VISTA PÚBLICA: LISTA ─────────────────────────────────────────────────────

@bp.route('/rifas')
def list_rifas():
    all_rifas = Raffle.query.all()
    stats_meta = stats_recaudado = 0
    for r in all_rifas:
        stats_meta += 100 * r.price
        vendidos = RaffleSelection.query.filter_by(raffle_id=r.id, is_canceled=False).count()
        stats_recaudado += vendidos * r.price
    stats = {
        'total_rifas': len(all_rifas),
        'activas':     sum(1 for r in all_rifas if r.is_active),
        'cerradas':    sum(1 for r in all_rifas if not r.is_active),
        'meta':        stats_meta,
        'recaudado':   stats_recaudado,
        'pendiente':   stats_meta - stats_recaudado,
        'porcentaje':  round(stats_recaudado / stats_meta * 100, 1) if stats_meta > 0 else 0,
    }
    rifas = Raffle.query.filter_by(is_active=True).order_by(Raffle.raffle_date.desc()).all()
    raffle_data = []
    for r in rifas:
        total_sold = RaffleSelection.query.filter_by(raffle_id=r.id, is_canceled=False).count()
        try:
            winners = json.loads(r.winning_numbers) if r.winning_numbers else []
        except Exception:
            winners = []
        winners_info = []
        for num in winners:
            sel = RaffleSelection.query.filter_by(raffle_id=r.id, number=num, is_canceled=False).first()
            winners_info.append({'number': num, 'name': sel.customer_name if sel else 'Sin asignar'})
        raffle_data.append({
            'id': r.id, 'raffle_number': r.raffle_number, 'name': r.name,
            'price': r.price, 'prize': r.prize, 'detail': r.detail,
            'raffle_date': r.raffle_date.strftime('%Y-%m-%d') if r.raffle_date else '',
            'raffle_time': r.raffle_time, 'image_filename': r.image_filename,
            'winning_numbers': winners, 'winners_info': winners_info,
            'total_sold': total_sold, 'total_available': 100 - total_sold
        })
    return render_template('rifas.html', rifas=raffle_data, stats=stats)


# ── MI SELECCIÓN (VISTA PERSONAL) ────────────────────────────────────────────

@bp.route('/rifas/mis-selecciones')
def mis_selecciones():
    return render_template('mis_selecciones_busqueda.html')


@bp.route('/rifas/mi-seleccion/<int:selection_id>')
def mi_seleccion(selection_id):
    selection = RaffleSelection.query.get_or_404(selection_id)
    if not selection.raffle.is_active:
        flash('Esta rifa no está activa', 'warning')
        return redirect(url_for('main.list_rifas'))
    try:
        winners = json.loads(selection.raffle.winning_numbers) if selection.raffle.winning_numbers else []
    except Exception:
        winners = []
    is_winner = selection.number in winners if not selection.is_canceled else False
    return render_template('mi_seleccion.html', selection=selection, winners=winners, is_winner=is_winner)
