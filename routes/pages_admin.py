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
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('eventos.html')


@bp.route('/detalles_evento/<int:event_id>')
def detalles_evento(event_id):
    evento = Event.query.get_or_404(event_id)
    return render_template('ver_evento.html', evento=evento)


@bp.route('/agenda')
def agenda():
    # Solo visible para el Superusuario (Directorio global de la Tribu)
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('agenda.html')


@bp.route('/backups')
def backup_manager():
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('backups.html')
