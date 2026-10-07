# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_donacion.py - Donar puntos (usuario) y gestionar finalidades (superusuario)
from flask import request, session, redirect, url_for
from db import db
from models import DonacionFinalidad, HikerPoints
from modules.points_charity import reglas, finalidades_activas, finalidades_admin, donar
from routes import bp
from routes.points import _current_user


@bp.app_context_processor
def _inject_donacion():
    return {'donacion_reglas': reglas, 'donacion_finalidades': finalidades_activas,
            'donacion_finalidades_admin': finalidades_admin}


def _volver(cedula):
    return redirect(url_for('main.mis_puntos', cedula=cedula))


def _es_super():
    return session.get('role') == 'Superusuario'


@bp.route('/mis-puntos/donar-causa', methods=['POST'])
def donar_causa():
    cedula = (request.form.get('cedula') or '').strip()
    if not cedula or not (_es_super() or session.get('mis_puntos_ok') == cedula):
        session['admin_error'] = 'Verificá tu cédula y contraseña primero.'
        return _volver(cedula)
    try:
        monto = int(request.form.get('monto') or 0)
        finalidad_id = int(request.form.get('finalidad_id') or 0)
    except ValueError:
        monto, finalidad_id = 0, 0
    res = donar(cedula, finalidad_id, monto, _current_user())
    if res.get('ok'):
        session['admin_message'] = f'Donaste {monto} puntos a «{res["finalidad"]}». Te quedan {res["restante"]} puntos. ¡Gracias por tu generosidad!'
    else:
        session['admin_error'] = res.get('error')
    return _volver(cedula)


@bp.route('/admin/donacion/finalidad', methods=['POST'])
def donacion_finalidad_crear():
    cedula = (request.form.get('cedula') or '').strip()
    if not _es_super():
        return redirect(url_for('main.home'))
    nombre = (request.form.get('nombre') or '').strip()[:200]
    if nombre:
        db.session.add(DonacionFinalidad(nombre=nombre, descripcion=(request.form.get('descripcion') or '').strip()))
        db.session.commit()
        session['admin_message'] = f'Finalidad de donación «{nombre}» creada.'
    else:
        session['admin_error'] = 'El nombre de la finalidad es obligatorio.'
    return _volver(cedula)


@bp.route('/admin/donacion/finalidad/<int:fid>/<accion>', methods=['POST'])
def donacion_finalidad_accion(fid, accion):
    cedula = (request.form.get('cedula') or '').strip()
    if not _es_super():
        return redirect(url_for('main.home'))
    fin = DonacionFinalidad.query.get_or_404(fid)
    if accion == 'toggle':
        fin.activo = not fin.activo
        session['admin_message'] = f'«{fin.nombre}» ahora está {"activa" if fin.activo else "inactiva"}.'
    elif accion == 'eliminar':
        if HikerPoints.query.filter_by(donacion_finalidad_id=fid).first():
            session['admin_error'] = 'Ya recibió donaciones; no se puede eliminar, solo desactivar.'
            return _volver(cedula)
        db.session.delete(fin)
        session['admin_message'] = f'Finalidad «{fin.nombre}» eliminada.'
    db.session.commit()
    return _volver(cedula)
