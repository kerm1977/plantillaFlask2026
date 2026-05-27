from flask import render_template, session, redirect, url_for
from models import Notification, Event, Hiker
from datetime import datetime, date
from sqlalchemy import func
from db import db
from routes import bp


@bp.route('/')
def home():
    notifications = Notification.query.all()
    today = date.today()
    birthday_hikers = Hiker.query.filter(
        func.strftime('%m-%d', Hiker.fecha_nacimiento) == today.strftime('%m-%d'),
        Hiker.fecha_nacimiento != None
    ).all()
    return render_template('home.html', notifications=notifications, birthday_hikers=birthday_hikers)


@bp.route('/profile')
def profile():
    from models import User
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.home'))
    return render_template('perfil.html', user=user)


@bp.route('/calendario')
def calendario():
    # Protegemos la ruta para que solo Superusuarios puedan acceder
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    
    # Obtener todos los eventos ordenados por fecha
    eventos_db = Event.query.order_by(Event.fecha_inicio).all()
    
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    eventos_procesados = []
    for ev in eventos_db:
        if getattr(ev, 'fecha_inicio', None):
            fecha_dt = ev.fecha_inicio
            
            # Blindaje: Por si la fecha viene como string desde SQLite
            if isinstance(fecha_dt, str):
                try:
                    fecha_dt = datetime.strptime(fecha_dt, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        fecha_dt = datetime.strptime(fecha_dt, '%d/%m/%Y').date()
                    except ValueError:
                        continue # Si el formato es totalmente ilegible, lo omite sin crashear
            
            # Extracción segura de mes y día
            mes_num = getattr(fecha_dt, 'month', 1)
            dia_num = getattr(fecha_dt, 'day', 1)
            
            eventos_procesados.append({
                'mes': meses_es.get(mes_num, 'S/M'),
                'dia': str(dia_num),
                'nombre': getattr(ev, 'nombre_lugar', 'Caminata'),
                'categoria': getattr(ev, 'actividad', 'Caminata') or 'Caminata',
                'dificultad': getattr(ev, 'dificultad', 'Moderada') or 'Moderada'
            })
    
    # Pasamos los eventos ya procesados al HTML sin errores de Json
    return render_template('calendario.html', eventos=eventos_procesados)
