# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_export.py - Estados de cuenta y exportación/importación JSON
import json
from datetime import datetime
from flask import request, jsonify, session, Response, redirect, url_for
from db import db
from models import Hiker, HikerPoints
from modules.points_engine import get_points_engine
from routes import bp
from routes.points import _current_user


def _format_row_line(row):
    fecha = (row.get('creado_at') or '')[:19].replace('T', ' ')
    tipo = (row.get('tipo') or '')[:17]
    detalle = (row.get('detalle') or '')[:40]
    return f'{fecha:<20} {tipo:<17} {detalle:<40} {row.get("puntos", 0):>8}'


def _build_estado_cuenta(cedula, hiker=None):
    engine = get_points_engine()
    lines = []
    lines.append('=' * 90)
    lines.append('ESTADO DE CUENTA - La Tribu de los Libres')
    lines.append('=' * 90)
    lines.append(f'Cedula: {cedula}')
    lines.append(f'Nombre: {hiker.nombre_completo if hiker else ""}')
    if hiker:
        fn = hiker.fecha_nacimiento
        lines.append(f'Telefono: {hiker.telefono or "No registrado"}')
        lines.append(f'Pasaporte: {hiker.pasaporte or "No registrado"}')
        lines.append(f'Tipo de sangre: {hiker.tipo_sangre or "No registrado"}')
        lines.append(f'Fecha de nacimiento: {fn.strftime("%d/%m/%Y") if fn else "No registrada"}')
        lines.append(f'Alergias: {hiker.alergias or "Ninguna"}')
        lines.append(f'Enfermedades cronicas: {hiker.enfermedades_cronicas or "Ninguna"}')
        lines.append(f'Contacto emergencia: {hiker.contacto_emergencia_nombre or ""} {hiker.contacto_emergencia_telefono or ""}'.strip())
    lines.append(f'Total puntos: {engine.total_by_cedula(cedula)}')
    lines.append('Generado: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    lines.append('')
    lines.append(f'{"Fecha":<20} {"Tipo":<17} {"Detalle":<40} {"Puntos":>8}')
    lines.append('-' * 90)
    for row in engine.history_with_names(cedula):
        lines.append(_format_row_line(row))
    lines.append('')
    return '\n'.join(lines)


@bp.route('/mis-puntos/estado-cuenta', methods=['GET'])
def estado_cuenta():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    text = _build_estado_cuenta(cedula, hiker)
    filename = f'estado_cuenta_{cedula}.txt'
    return Response(text, mimetype='text/plain', headers={'Content-Disposition': f'attachment; filename={filename}'})


@bp.route('/admin/puntos/exportar', methods=['GET'])
def admin_puntos_exportar():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
    parts = []
    parts.append('=' * 90)
    parts.append('RESUMEN DE ESTADOS DE CUENTA - La Tribu de los Libres')
    parts.append('Generado: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    parts.append('=' * 90)
    parts.append('')
    for hiker in hikers:
        parts.append(_build_estado_cuenta(hiker.cedula, hiker))
    text = '\n'.join(parts)
    return Response(text, mimetype='text/plain', headers={'Content-Disposition': 'attachment; filename=estados_cuenta_todos.txt'})


@bp.route('/mis-puntos/exportar-json', methods=['GET'])
def mis_puntos_exportar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    engine = get_points_engine()
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    data = {
        'cedula': cedula,
        'nombre_completo': hiker.nombre_completo if hiker else '',
        'total': engine.total_by_cedula(cedula),
        'historial': engine.history_with_names(cedula)
    }
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(text, mimetype='application/json', headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.json'})


@bp.route('/mis-puntos/importar-json', methods=['POST'])
def mis_puntos_importar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    cedula = (request.form.get('cedula') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cedula'}), 400
    if 'archivo' not in request.files:
        return jsonify({'ok': False, 'error': 'Falta el archivo'}), 400
    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({'ok': False, 'error': 'Archivo vacío'}), 400
    try:
        contenido = json.loads(archivo.read().decode('utf-8'))
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        hiker_id = hiker.id if hiker else None
        registros = contenido.get('historial', contenido) if isinstance(contenido, dict) else contenido
        if not isinstance(registros, list):
            return jsonify({'ok': False, 'error': 'El JSON no contiene una lista de registros'}), 400
        agregados = 0
        for r in registros:
            if (r.get('cedula') or '').strip() != cedula:
                continue
            puntos = int(r.get('puntos', 0) or 0)
            hp = HikerPoints(
                cedula=cedula,
                hiker_id=hiker_id,
                event_id=r.get('event_id'),
                points=puntos,
                tipo=(r.get('tipo') or 'participacion')[:20],
                detalle=(r.get('detalle') or '')[:255],
                created_by=(r.get('creado_por') or _current_user())[:100],
                created_at=datetime.fromisoformat(r['creado_at']) if r.get('creado_at') else datetime.utcnow()
            )
            db.session.add(hp)
            agregados += 1
        db.session.commit()
        return redirect(url_for('main.mis_puntos', cedula=cedula))
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400
