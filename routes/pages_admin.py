from flask import render_template, session, redirect, url_for
from models import Event
from routes import bp


@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('dashboard.html')


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
