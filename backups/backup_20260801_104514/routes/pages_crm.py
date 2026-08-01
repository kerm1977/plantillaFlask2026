import re
from flask import render_template, redirect, url_for
from models import Event, Hiker
from routes import bp


@bp.route('/registro')
def registro_publico():
    """Formulario de registro CRM sin evento específico."""
    class _MockEvento:
        nombre_lugar = "La Tribu de Los Libres"
        id           = 0
        is_sold_out  = False
    return render_template('formulario_inscripcion.html', evento=_MockEvento())


@bp.route('/inscripcion/<path:identifier>')
def inscripcion_evento(identifier):
    """
    Ruta pública para el formulario de inscripción a un evento.
    Soporta identificadores numéricos (/inscripcion/20) y slugs amigables (/inscripcion/caminata-isla-venado-20).
    """
    if identifier.isdigit():
        # Si el link es antiguo y solo tiene el número (ej: /inscripcion/20)
        evento = Event.query.get_or_404(int(identifier))
    else:
        # Si es un link nuevo con texto, buscamos el ID al final (ej: caminata-isla-venado-20 -> extrae el 20)
        match = re.search(r'-(\d+)$', identifier)
        if match:
            evento_id = int(match.group(1))
            evento = Event.query.get_or_404(evento_id)
        else:
            # Fallback de seguridad: si el link no tiene número al final por alguna razón, 
            # intenta buscar el evento por el nombre aproximado.
            nombre_real = identifier.replace('-', ' ')
            evento = Event.query.filter(Event.nombre_lugar.ilike(f"%{nombre_real}%")).order_by(Event.id.desc()).first_or_404()
            
    return render_template('formulario_inscripcion.html', evento=evento)


@bp.route('/editar_caminante/<identifier>')
def editar_caminante(identifier):
    """
    Abre el formulario en modo 'edición' usando la cédula (CRM) o el PIN (Usuario).
    """
    # Intentamos buscar primero por cédula
    hiker = Hiker.query.filter_by(cedula=identifier).first()
    
    # Si no aparece, intentamos buscar por PIN
    if not hiker:
        hiker = Hiker.query.filter_by(pin_secreto=identifier).first()
        
    if not hiker:
        # Si de ninguna forma existe, lo mandamos al inicio
        return redirect(url_for('main.home'))
        
    return render_template('editar_caminante.html', hiker=hiker)
