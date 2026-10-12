# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
import re
from flask import render_template, session, redirect, url_for
from models import Event, User, Hiker
from routes import bp


@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('dashboard.html')


@bp.route('/admin/crear-usuario')
def crear_usuario():
    # Crear usuario como página dedicada (hoja única, sin modal)
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('crear_usuario.html')


@bp.route('/admin/editar-usuario/<int:user_id>')
def editar_usuario(user_id):
    # Editar usuario como página dedicada (hoja única, sin modal, datos precargados)
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    u = User.query.get_or_404(user_id)

    # Vincular la ficha del caminante (CRM): por teléfono, si no por nombre completo
    hiker = None
    phone_clean = re.sub(r'\D', '', u.phone or '')
    if phone_clean:
        for h in Hiker.query.all():
            if h.telefono and re.sub(r'\D', '', h.telefono) == phone_clean:
                hiker = h
                break
    if not hiker:
        full_name = f"{u.name} {u.last_name_1} {u.last_name_2}".strip()
        hiker = Hiker.query.filter_by(nombre_completo=full_name).first()

    cedula_val = re.sub(r'\D', '', hiker.cedula or '') if hiker else ''
    fnac = (hiker.fecha_nacimiento if hiker else None) or u.dob
    fnac_dia = fnac.strftime('%d') if fnac else None
    fnac_mes = fnac.strftime('%m') if fnac else None
    fnac_anio = fnac.year if fnac else None

    nombres_em = [s.strip() for s in (hiker.contacto_emergencia_nombre or '').split(' | ') if s.strip()] if hiker else []
    tels_em = [s.strip() for s in (hiker.contacto_emergencia_telefono or '').split(' | ') if s.strip()] if hiker else []
    n = max(len(nombres_em), len(tels_em), 1)
    emergencias = [{'nombre': nombres_em[i] if i < len(nombres_em) else '',
                    'telefono': tels_em[i] if i < len(tels_em) else ''} for i in range(n)]

    extras = []
    for name, label in [('facebook', 'Facebook'), ('instagram', 'Instagram'),
                        ('address', 'Dirección'), ('institution', 'Institución/Empresa'),
                        ('other_info', 'Información adicional')]:
        val = getattr(u, name, None)
        if val:
            extras.append({'name': name, 'label': label, 'value': val})

    avatar_file = u.avatar if u.avatar else 'default.png'

    return render_template('editar_usuario.html', u=u, hiker=hiker,
                           cedula_val=cedula_val, phone_val=phone_clean,
                           fnac_dia=fnac_dia, fnac_mes=fnac_mes, fnac_anio=fnac_anio,
                           emergencias=emergencias, extras=extras, avatar_file=avatar_file)


@bp.route('/eventos')
def eventos():
    # El formulario de crear/editar eventos se unificó dentro de /caminatas-2027
    # (modal "Crear Nuevo Evento"), para evitar tener dos formularios distintos.
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return redirect(url_for('main.caminatas_2027', crear=1))


@bp.route('/detalles_evento/<int:event_id>')
def detalles_evento(event_id):
    evento = Event.query.get_or_404(event_id)
    if evento.visitado == 'Cotización' and session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    if evento.visitado in ('Visitados','Visitado','Sí'):
        return render_template('ver_visitado.html', evento=evento)
    from modules.points_helpers import get_puntos_password
    return render_template('ver_evento.html', evento=evento, puntos_password=get_puntos_password())


@bp.route('/backups')
def backup_manager():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('backups.html')


@bp.route('/admin/tema')
def admin_theme():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('admin_theme.html')


@bp.route('/admin/logo-config')
def admin_logo_config():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('admin_logo_config.html')


@bp.route('/admin/carrusel')
def admin_carrusel():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('admin_carrusel.html')
