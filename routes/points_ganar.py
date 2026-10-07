# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_ganar.py - "Ganar puntos desde casa" (Mis puntos).
# - actualizar-datos: formulario completo de la persona, +200 pts una vez.
# - foto-fb: foto de perfil con la camisa de La Tribu, +200 pts una vez.
# Cada premio se acredita una unica vez por cedula (tipo en hiker_points).
from datetime import datetime
from flask import request, session, redirect, url_for

from db import db
from models import Hiker, HikerPoints
from modules.points_engine import get_points_engine
from routes import bp
from routes.points import _current_user

PUNTOS_DATOS = 200
PUNTOS_FOTO = 200


def _volver(cedula):
    return redirect(url_for('main.mis_puntos', cedula=cedula))


def _hiker_autorizado():
    """(cedula, hiker, redirect). Superusuario o persona verificada con su PIN."""
    cedula = (request.form.get('cedula') or '').strip()
    if not cedula or (session.get('role') != 'Superusuario' and session.get('mis_puntos_ok') != cedula):
        session['admin_error'] = 'Verificá tu cédula y contraseña primero.'
        return None, None, _volver(cedula)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        session['admin_error'] = 'Usuario no encontrado.'
        return None, None, _volver(cedula)
    return cedula, hiker, None


def _premio_unico(cedula, hiker, tipo, puntos, detalle):
    """Acredita puntos solo si nunca se otorgó ese tipo a la cédula."""
    ya = HikerPoints.query.filter_by(cedula=cedula, tipo=tipo).first()
    if ya:
        return False
    get_points_engine()._add_record(cedula, hiker.id, None, puntos, tipo, detalle, _current_user())
    return True


@bp.route('/mis-puntos/actualizar-datos', methods=['POST'])
def actualizar_datos():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    f = lambda k: (request.form.get(k) or '').strip()
    # Todos estos campos son obligatorios para ganar los puntos
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
        session['admin_error'] = 'Para ganar los puntos tenés que llenar todos los campos. Faltan: ' + ', '.join(faltantes) + '.'
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

    if _premio_unico(cedula, hiker, 'datos_actualizados', PUNTOS_DATOS,
                     'Datos personales actualizados por completo'):
        session['admin_message'] = f'Datos actualizados. Ganaste {PUNTOS_DATOS} puntos.'
    else:
        session['admin_message'] = 'Datos actualizados correctamente. (El premio de 200 puntos ya lo habías ganado antes.)'
    return _volver(cedula)


@bp.route('/mis-puntos/foto-fb', methods=['POST'])
def foto_fb():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    if (request.form.get('confirma') or '') != 'si':
        session['admin_error'] = 'Marcá la casilla para confirmar que ya pusiste la foto.'
        return _volver(cedula)
    if _premio_unico(cedula, hiker, 'foto_facebook', PUNTOS_FOTO,
                     'Foto de perfil en Facebook con la camisa de La Tribu (1 semana)'):
        session['admin_message'] = f'Confirmado. Ganaste {PUNTOS_FOTO} puntos por tu foto de perfil. Recordá mantenerla una semana.'
    else:
        session['admin_error'] = 'Ya habías ganado los puntos de la foto de perfil.'
    return _volver(cedula)
