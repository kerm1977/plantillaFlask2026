# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_compra.py - Comprar puntos (usuario) y aprobar pagos (superusuario)
from flask import request, session, redirect, url_for
from modules import points_purchase as pp
from routes import bp
from routes.points import _current_user


@bp.app_context_processor
def _inject_compra():
    return {'compra_fee': pp.FEE, 'compra_minimo': pp.MINIMO, 'compra_miles': pp.miles,
            'compra_pendientes_usuario': pp.pendientes_usuario, 'compra_pendientes_admin': pp.pendientes_admin}


def _volver(cedula, ancla=''):
    return redirect(url_for('main.mis_puntos', cedula=cedula) + ancla)


def _es_super():
    return session.get('role') == 'Superusuario'


@bp.route('/mis-puntos/comprar', methods=['POST'])
def comprar_puntos():
    cedula = (request.form.get('cedula') or '').strip()
    if not cedula or not (_es_super() or session.get('mis_puntos_ok') == cedula):
        session['admin_error'] = 'Verificá tu cédula y contraseña primero.'
        return _volver(cedula)
    try:
        puntos = int(request.form.get('puntos') or 0)
    except ValueError:
        puntos = 0
    res = pp.solicitar(cedula, puntos)
    if res.get('ok'):
        session['admin_message'] = (f'Solicitud registrada: {pp.miles(puntos)} puntos por ₡{pp.miles(res["pagar"])}. '
                                    'Avisá por WhatsApp; los puntos se acreditan cuando un superusuario apruebe tu pago.')
    else:
        session['admin_error'] = res.get('error')
    return _volver(cedula, '#accComprar')


@bp.route('/admin/compras/<int:compra_id>/<accion>', methods=['POST'])
def compra_resolver(compra_id, accion):
    cedula = (request.form.get('cedula') or '').strip()
    if not _es_super() or accion not in ('aprobar', 'rechazar'):
        return redirect(url_for('main.home'))
    res = pp.resolver(compra_id, accion == 'aprobar', _current_user())
    if res.get('ok'):
        verbo = 'aprobada: se acreditaron' if accion == 'aprobar' else 'rechazada:'
        session['admin_message'] = f'Compra {verbo} {pp.miles(res["puntos"])} puntos (cédula {res["cedula"]}).'
    else:
        session['admin_error'] = res.get('error')
    return _volver(cedula)
