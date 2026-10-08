# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_ganar.py - Retos de "Ganar puntos desde casa".
# La persona confirma -> solicitud pendiente + aviso por WhatsApp
# a coordinadores -> el superusuario aprueba (acredita) o rechaza.
# Cada reto se acredita una sola vez por mes.
from datetime import datetime
from flask import request, session, redirect, url_for, jsonify

from db import db
from models import Hiker
from modules import retos, retos_builder
from routes import bp
from routes.points import _current_user


@bp.app_context_processor
def inject_retos():
    # BLINDADO: helpers del panel "Retos" del superusuario (se consultan solo si se usa).
    return {'retos_pendientes': retos.pendientes, 'retos_resueltas': retos.resueltas,
            'retos_todos': retos_builder.todos_custom}


def _volver(cedula):
    return redirect(url_for('main.mis_puntos', cedula=cedula))


def _ajax():
    return request.headers.get('X-Requested-With') == 'fetch'


def _hiker_autorizado():
    """(cedula, hiker, redirect). Superusuario o persona verificada con su PIN."""
    cedula = (request.form.get('cedula') or request.args.get('cedula') or '').strip()
    if not cedula or (session.get('role') != 'Superusuario' and session.get('mis_puntos_ok') != cedula):
        return None, None, 'Verificá tu cédula y contraseña primero.'
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return None, None, 'Usuario no encontrado.'
    return cedula, hiker, None


@bp.route('/mis-puntos/reto/<reto>', methods=['POST'])
def reto_confirmar(reto):
    """Confirma un reto (foto de perfil / portada): solicitud pendiente + WhatsApp."""
    cedula, hiker, err = _hiker_autorizado()
    if err:
        if _ajax():
            return jsonify({'ok': False, 'error': err})
        session['admin_error'] = err
        return _volver(cedula)
    res = retos.crear_solicitud(cedula, reto)
    wa = retos.wa_coordinador(hiker, reto)
    if _ajax():
        return jsonify({'ok': res['ok'], 'ya_pendiente': res.get('ya_pendiente', False),
                        'error': res.get('error', ''), 'wa': wa})
    if res['ok']:
        session['admin_message'] = 'Reto registrado. Tocá el botón verde para avisar a los coordinadores por WhatsApp.'
        session['wa_aviso'] = wa
    else:
        session['admin_error'] = res['error']
    return _volver(cedula)


@bp.route('/admin/retos/<int:sid>/<accion>', methods=['POST'])
def reto_resolver(sid, accion):
    """Solo superusuario: aprueba (acredita puntos) o rechaza el reto."""
    cedula = (request.form.get('cedula') or '').strip()
    if session.get('role') != 'Superusuario':
        session['admin_error'] = 'Solo el superusuario puede resolver retos.'
        return _volver(cedula)
    res = retos.resolver(sid, accion, _current_user())
    if res['ok']:
        session['admin_message'] = res['mensaje']
        if res.get('wa'):
            session['wa_aviso'] = res['wa']
    else:
        session['admin_error'] = res['error']
    return _volver(cedula)


@bp.route('/admin/retos/crear', methods=['POST'])
def reto_crear():
    """Constructor de retos: crea un reto personalizado (solo superusuario)."""
    cedula = (request.form.get('cedula') or '').strip()
    if session.get('role') != 'Superusuario':
        session['admin_error'] = 'Solo el superusuario puede crear retos.'
        return _volver(cedula)
    res = retos_builder.crear_custom(request.form.get('titulo'), request.form.get('texto'),
                                     request.form.get('puntos'), request.form.get('enlace'),
                                     request.form.get('frecuencia'), _current_user())
    if res['ok']:
        session['admin_message'] = res['mensaje']
    else:
        session['admin_error'] = res['error']
    return _volver(cedula)


@bp.route('/admin/retos/custom/<int:rid>/toggle', methods=['POST'])
def reto_custom_toggle(rid):
    """Activa/desactiva un reto personalizado (solo superusuario)."""
    cedula = (request.form.get('cedula') or '').strip()
    if session.get('role') != 'Superusuario':
        session['admin_error'] = 'Solo el superusuario puede gestionar retos.'
        return _volver(cedula)
    res = retos_builder.toggle_custom(rid)
    if res['ok']:
        session['admin_message'] = res['mensaje']
    else:
        session['admin_error'] = res['error']
    return _volver(cedula)


@bp.route('/mis-puntos/actualizar-datos', methods=['POST'])
def actualizar_datos():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        session['admin_error'] = err
        return _volver(cedula)
    f = lambda k: (request.form.get(k) or '').strip()
    # Todos estos campos son obligatorios para completar el reto
    requeridos = {
        'nombre_completo': 'nombre completo',
        'telefono': 'número de teléfono',
        'correo': 'correo electrónico',
        'tipo_sangre': 'tipo de sangre',
        'contacto_emergencia_nombre': 'contacto de emergencia',
        'contacto_emergencia_telefono': 'teléfono de emergencia',
    }
    faltantes = [label for k, label in requeridos.items() if not f(k)]
    if faltantes:
        session['admin_error'] = 'Para completar el reto tenés que llenar todos los campos. Faltan: ' + ', '.join(faltantes) + '.'
        return _volver(cedula)

    hiker.nombre_completo = f('nombre_completo')
    hiker.telefono = f('telefono')
    hiker.card_email = f('correo').lower()
    hiker.tipo_sangre = f('tipo_sangre')
    hiker.contacto_emergencia_nombre = f('contacto_emergencia_nombre')
    hiker.contacto_emergencia_telefono = f('contacto_emergencia_telefono')
    if f('pasaporte'):
        hiker.pasaporte = f('pasaporte')
    if f('alergias'):
        hiker.alergias = f('alergias')
    if f('enfermedades_cronicas'):
        hiker.enfermedades_cronicas = f('enfermedades_cronicas')
    if f('fecha_nacimiento'):
        try:
            hiker.fecha_nacimiento = datetime.strptime(f('fecha_nacimiento'), '%Y-%m-%d').date()
        except ValueError:
            pass
    db.session.commit()

    res = retos.crear_solicitud(cedula, 'datos')
    if res['ok']:
        session['admin_message'] = ('Datos guardados. Tu reto quedó pendiente de aprobación: '
                                    'avisá a los coordinadores por WhatsApp para que lo confirmen.')
        session['wa_aviso'] = retos.wa_coordinador(hiker, 'datos')
    else:
        session['admin_message'] = 'Datos guardados. (El premio de este reto ya lo ganaste este mes.)'
    return _volver(cedula)
