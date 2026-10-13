# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points.py - Endpoints del motor de puntuación
# (páginas en points_mis.py / points_evento.py, exportación en points_export.py)
import json
import re
from datetime import datetime
from urllib.parse import quote
from flask import request, jsonify, session, Response, redirect, url_for
from db import db
from models import Hiker, Event, HikerPoints, User
from modules.points_engine import get_points_engine
from modules.points_helpers import (set_puntos_password, set_notif_cleared, get_puntos_admin_visible,
                                    set_puntos_admin_visible, build_estado_cuenta_whatsapp)
from routes import bp


def _current_user():
    return session.get('name') or session.get('email') or 'sistema'


@bp.route('/admin/puntos/password', methods=['POST'])
def puntos_password():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    pwd = (request.form.get('password') or '').strip()
    if not (pwd.isdigit() and len(pwd) == 4):
        session['puntos_pwd_msg'] = 'La contraseña debe tener exactamente 4 dígitos.'
    else:
        set_puntos_password(pwd)
        session['puntos_pwd_msg'] = 'Contraseña de ingreso a puntos actualizada correctamente.'
    return redirect(url_for('main.mis_puntos'))


@bp.route('/admin/puntos/password-visibilidad', methods=['POST'])
def puntos_password_visibilidad():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    set_puntos_admin_visible(bool(request.form.get('visible')))
    return redirect(url_for('main.mis_puntos'))


@bp.route('/admin/puntos/estadisticas-restaurar', methods=['POST'])
def admin_puntos_estadisticas_restaurar():
    """Restaura las estadísticas personales a cero desde ahora (todos los
    usuarios). NO toca los puntos: solo fija la fecha desde la que cuentan
    las estadísticas."""
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    from modules.estado_global import reset_stats_desde
    reset_stats_desde()
    cedula = (request.form.get('cedula') or '').strip()
    session['admin_message'] = 'Estadísticas restauradas a cero. Los puntos no se modificaron.'
    return redirect(url_for('main.mis_puntos', cedula=cedula) if cedula
                    else url_for('main.mis_puntos'))


@bp.route('/admin/puntos/lista-ocultar-ceros', methods=['POST'])
def admin_puntos_lista_ocultar_ceros():
    """Guarda el toggle 'Ocultar personas sin puntos' de la lista (persistente)."""
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    from modules.points_helpers import set_lista_ocultar_ceros
    set_lista_ocultar_ceros(bool(request.form.get('ocultar')))
    return redirect(url_for('main.mis_puntos'))


@bp.route('/admin/puntos/whatsapp/<cedula>')
def admin_puntos_whatsapp(cedula):
    """Redirige a WhatsApp con el estado de cuenta de la persona, generado en
    tiempo real. Si tiene teléfono registrado se abre su chat directo."""
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return redirect(url_for('main.mis_puntos'))
    estado = build_estado_cuenta_whatsapp(cedula, hiker)
    tel = re.sub(r'\D', '', hiker.telefono or '')
    if tel and len(tel) == 8:
        tel = '506' + tel
    wa = f'https://wa.me/{tel}?text={quote(estado)}' if tel \
        else 'https://wa.me/?text=' + quote(estado)
    return redirect(wa)


@bp.route('/puntos/limpiar-notificaciones', methods=['POST'])
def puntos_limpiar_notificaciones():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('main.home'))
    full_name = f'{user.name} {user.last_name_1} {user.last_name_2}'.strip()
    hiker = Hiker.query.filter_by(telefono=user.phone).first() if user.phone else None
    if not hiker:
        hiker = Hiker.query.filter_by(nombre_completo=full_name).first()
    if hiker:
        set_notif_cleared(hiker.cedula)
    if session.get('role') == 'Superusuario':
        return redirect(url_for('main.control_usuarios', seccion='expediente'))
    return redirect(url_for('main.profile'))


@bp.route('/admin/puntos/exportar-json', methods=['GET'])
def admin_puntos_exportar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    engine = get_points_engine()
    hikers = Hiker.query.order_by(Hiker.nombre_completo).all()
    data = {
        'generado': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'usuarios': []
    }
    for hiker in hikers:
        data['usuarios'].append({
            'cedula': hiker.cedula,
            'nombre_completo': hiker.nombre_completo,
            'total': engine.total_by_cedula(hiker.cedula),
            'historial': engine.history_with_names(hiker.cedula)
        })
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(text, mimetype='application/json', headers={'Content-Disposition': 'attachment; filename=puntos_todos_usuarios.json',
                                                              'Cache-Control': 'no-store, no-cache, must-revalidate', 'Pragma': 'no-cache'})


@bp.route('/admin/puntos/importar-json', methods=['POST'])
def admin_puntos_importar_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    if 'archivo' not in request.files:
        session['puntos_pwd_msg'] = 'Falta el archivo JSON.'
        return redirect(url_for('main.mis_puntos'))
    archivo = request.files['archivo']
    if archivo.filename == '':
        session['puntos_pwd_msg'] = 'Archivo vacío.'
        return redirect(url_for('main.mis_puntos'))
    try:
        contenido = json.loads(archivo.read().decode('utf-8'))
        registros = []
        if isinstance(contenido, dict) and isinstance(contenido.get('usuarios'), list):
            for u in contenido['usuarios']:
                ced = (u.get('cedula') or '').strip()
                for r in (u.get('historial') or []):
                    r = dict(r)
                    r['cedula'] = ced
                    registros.append(r)
        elif isinstance(contenido, dict) and isinstance(contenido.get('historial'), list):
            ced = (contenido.get('cedula') or '').strip()
            for r in contenido['historial']:
                r = dict(r)
                r.setdefault('cedula', ced)
                registros.append(r)
        elif isinstance(contenido, list):
            registros = contenido
        else:
            session['puntos_pwd_msg'] = 'El JSON no contiene registros de puntos.'
            return redirect(url_for('main.mis_puntos'))
        agregados = 0
        for r in registros:
            ced = (r.get('cedula') or '').strip()
            if not ced:
                continue
            hiker = Hiker.query.filter_by(cedula=ced).first()
            hp = HikerPoints(
                cedula=ced,
                hiker_id=hiker.id if hiker else None,
                event_id=r.get('event_id'),
                points=int(r.get('puntos', 0) or 0),
                tipo=(r.get('tipo') or 'participacion')[:20],
                detalle=(r.get('detalle') or '')[:255],
                created_by=(r.get('creado_por') or _current_user())[:100],
                created_at=datetime.fromisoformat(r['creado_at']) if r.get('creado_at') else datetime.utcnow()
            )
            db.session.add(hp)
            agregados += 1
        db.session.commit()
        session['puntos_pwd_msg'] = f'Importación completada: {agregados} movimientos de puntos agregados.'
        return redirect(url_for('main.mis_puntos'))
    except Exception as e:
        session['puntos_pwd_msg'] = f'Error al importar: {e}'
        return redirect(url_for('main.mis_puntos'))


@bp.route('/api/puntos/asignar/<int:event_id>', methods=['POST'])
def puntos_asignar(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    result = get_points_engine().assign_to_event(event_id, _current_user())
    return jsonify(result), (200 if result.get('ok') else 400)


@bp.route('/api/puntos/retirar/<int:event_id>', methods=['POST'])
def puntos_retirar(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.json or request.form or {}
    cedula = (data.get('cedula') or '').strip()
    justificado = (data.get('justificado') or data.get('lesion') or '').lower() in ('true', '1', 'si', 'yes', 'on')
    mensaje = (data.get('mensaje') or '').strip()
    if not cedula:
        return jsonify({'ok': False, 'error': 'Falta la cédula'}), 400
    result = get_points_engine().withdraw(event_id, cedula, _current_user(), justificado=justificado, mensaje=mensaje)
    return jsonify(result), (200 if result.get('ok') else 400)


@bp.route('/api/puntos/historial/<cedula>', methods=['GET'])
def puntos_historial(cedula):
    engine = get_points_engine()
    cedula = cedula.strip()
    total = engine.total_by_cedula(cedula)
    history = engine.history_with_names(cedula)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    return jsonify({
        'ok': True,
        'cedula': cedula,
        'nombre_completo': hiker.nombre_completo if hiker else '',
        'total': total,
        'history': history
    })


@bp.route('/api/puntos/evento/<int:event_id>', methods=['GET'])
def puntos_evento(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    rows = get_points_engine().event_assignments(event_id)
    event = Event.query.get_or_404(event_id)
    return jsonify({'ok': True, 'puntos_por_persona': event.puntos or 0, 'asignados': rows})


@bp.route('/mis-puntos/eliminar/<int:row_id>', methods=['POST'])
def mis_puntos_eliminar(row_id):
    if 'user_id' not in session and session.get('role') != 'Superusuario':
        return redirect(url_for('main.mis_puntos'))
    record = HikerPoints.query.get_or_404(row_id)
    cedula = record.cedula
    is_super = session.get('role') == 'Superusuario'
    puede_eliminar = is_super
    if not is_super and 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            full_name = f'{user.name} {user.last_name_1} {user.last_name_2}'.strip()
            hiker = Hiker.query.filter_by(telefono=user.phone).first() if user.phone else None
            if not hiker:
                hiker = Hiker.query.filter_by(nombre_completo=full_name).first()
            if hiker and hiker.cedula == cedula:
                puede_eliminar = True
    if not puede_eliminar:
        return redirect(url_for('main.mis_puntos', cedula=cedula))
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('main.mis_puntos', cedula=cedula))
