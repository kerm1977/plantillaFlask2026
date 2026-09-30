# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/pages_caminatas.py - Listados de caminatas (tribu, estados, 2027)
from flask import render_template, session, redirect, url_for, request
import hashlib
from models import Event, CaminataBlock
from datetime import datetime
from sqlalchemy import or_
from routes import bp
from routes.pages import _get_site_text


@bp.route('/caminatas')
def caminatas():
    from itertools import groupby
    is_super = session.get('role') == 'Superusuario'
    meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    eventos = Event.query.order_by(Event.fecha_unica, Event.fecha_inicio).all()
    if not is_super:
        eventos = [ev for ev in eventos if ev.visitado != 'Cotización']

    def mes_key(ev):
        fecha = ev.fecha_unica or ev.fecha_inicio or ev.fecha_regreso
        if fecha and len(fecha.split('-')) >= 2:
            return fecha[:7]
        return '9999-99'

    por_definir = 'Otras Caminatas'

    def mes_label(key):
        if key == '9999-99':
            return por_definir
        y, m = key.split('-')
        return f"{meses[int(m)-1]} {y}"

    def es_caminata_2027(ev):
        return (
            (ev.fecha_unica or '').startswith('2027') or
            (ev.fecha_inicio or '').startswith('2027') or
            (ev.fecha_regreso or '').startswith('2027')
        )

    eventos_sorted = sorted(eventos, key=lambda ev: (mes_key(ev), ev.fecha_unica or ev.fecha_inicio or '9999-99-99'))
    timeline = []
    for idx, (key, items) in enumerate(groupby(eventos_sorted, key=mes_key)):
        items = list(items)
        entry = {'type': 'provincia', 'order': idx, 'group_label': mes_label(key), 'walks': items, 'walks_2027': []}
        if key == '9999-99':
            walks_2027 = [ev for ev in items if es_caminata_2027(ev)]
            walks_other = [ev for ev in items if not es_caminata_2027(ev)]
            entry['walks'] = walks_other
            entry['walks_2027'] = walks_2027
        timeline.append(entry)

    return render_template('caminatas_2027.html',
        caminatas_2027_text=_get_site_text('caminatas'),
        is_super=is_super,
        eventos=eventos,
        timeline=timeline,
        page_title='Caminatas de la Tribu',
        is_caminatas_2027_page=False,
        empty_message='Aún no hay caminatas registradas.',
        detail_endpoint='main.detalles_evento',
        group_header_text_class='',
        show_expand_hint=True,
        expand_hint_text='Toca para expandir el mes',
        group_badge_class='bg-white text-dark border ms-3 shadow-sm',
        group_badge_style='',
        group_badge_icon='bi-person-walking',
        group_badge_icon_color='#0dcaf0')


@bp.route('/caminatas/pendientes')
def caminatas_pendientes():
    is_super = session.get('role') == 'Superusuario'
    eventos = Event.query.filter(
        or_(
            Event.visitado == 'Pendiente',
            Event.visitado == 'No',
            Event.visitado == '',
            Event.visitado.is_(None)
        )
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas Pendientes')


@bp.route('/caminatas/anio')
def caminatas_anio():
    is_super = session.get('role') == 'Superusuario'
    eventos = [e for e in Event.query.order_by(Event.nombre_lugar).all()
               if e.visitado and e.visitado.isdigit() and len(e.visitado) == 4]
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas por Año')


@bp.route('/caminatas/visitados')
def caminatas_visitados():
    is_super = session.get('role') == 'Superusuario'
    eventos = Event.query.filter(
        or_(
            Event.visitado == 'Visitados',
            Event.visitado == 'Visitado',
            Event.visitado == 'Sí'
        )
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas Visitadas')


@bp.route('/caminatas/programados')
def caminatas_programados():
    is_super = session.get('role') == 'Superusuario'
    eventos = Event.query.filter(
        or_(Event.visitado == 'Programados', Event.visitado == 'Por programar')
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=is_super,
        eventos=eventos,
        page_title='Caminatas Programadas')


@bp.route('/caminatas/cotizaciones')
def caminatas_cotizaciones():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    eventos = Event.query.filter(
        Event.visitado == 'Cotización'
    ).order_by(Event.nombre_lugar).all()
    return render_template('caminatas_por_estado.html',
        is_super=True,
        eventos=eventos,
        page_title='Cotizaciones')


@bp.route('/cotizaciones/buseta')
def cotizaciones_buseta():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    from itertools import groupby
    eventos = Event.query.filter_by(visitado='Cotización').order_by(Event.provincia, Event.nombre_lugar).all()
    grupos = []
    for prov, items in groupby(eventos, key=lambda e: e.provincia or 'Sin provincia'):
        grupos.append({'provincia': prov, 'eventos': list(items)})
    return render_template('cotizaciones_buseta.html',
        is_super=True,
        grupos=grupos,
        page_title='Cotizaciones de buseta')


@bp.route('/caminatas-2027')
def caminatas_2027():
    from itertools import groupby
    is_share = request.args.get('share') == '1'
    is_super = session.get('role') == 'Superusuario' and not is_share
    eventos = Event.query.filter(
        or_(
            Event.fecha_unica.like('2027%'),
            Event.fecha_inicio.like('2027%'),
            Event.fecha_regreso.like('2027%')
        )
    ).order_by(Event.fecha_unica, Event.fecha_inicio).all()

    if not is_super:
        eventos = [ev for ev in eventos if ev.provincia != 'Referencia' and ev.visitado != 'Cotización']

    eventos_sorted = sorted(eventos, key=lambda e: (e.provincia or 'Sin provincia'))
    timeline = []
    for idx, (provincia, items) in enumerate(groupby(eventos_sorted, key=lambda e: (e.provincia or 'Sin provincia'))):
        timeline.append({'type': 'provincia', 'order': idx * 100.0, 'group_label': provincia or 'Sin provincia', 'walks': list(items)})

    blocks = CaminataBlock.query.filter_by(page='caminatas_2027').order_by(CaminataBlock.order).all()
    for b in blocks:
        timeline.append({'type': 'block', 'order': b.order, 'id': b.id, 'content': b.content})

    timeline.sort(key=lambda x: x['order'])

    share_url = url_for('main.caminatas_2027', share=1, _external=True)
    share_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')

    return render_template('caminatas_2027.html',
        caminatas_2027_text=_get_site_text('caminatas_2027'),
        is_super=is_super,
        is_share=is_share,
        share_url=share_url,
        share_datetime=share_datetime,
        eventos=eventos,
        timeline=timeline,
        detail_endpoint='main.ver_caminata_2027',
        group_badge_icon='bi-person-walking',
        group_badge_icon_color='#ffffff')


@bp.route('/caminatas-2027/<int:event_id>')
def ver_caminata_2027(event_id):
    is_share = request.args.get('share') == '1'
    is_super = session.get('role') == 'Superusuario' and not is_share
    event = Event.query.get_or_404(event_id)
    if event.visitado == 'Cotización' and not is_super:
        return redirect(url_for('main.home'))
    share_url = url_for('main.ver_caminata_2027', event_id=event_id, share=1, _external=True)
    share_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')
    itinerario_hash = hashlib.md5((event.itinerario or '').encode('utf-8')).hexdigest()
    return render_template('ver_caminata_2027.html',
        event=event,
        is_super=is_super,
        is_share=is_share,
        share_url=share_url,
        share_datetime=share_datetime,
        itinerario_hash=itinerario_hash)
