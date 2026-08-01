from flask import request, jsonify
from models import Hiker, EventRegistration
from db import db
from datetime import datetime
from routes import bp

# ==========================================
# SISTEMA CRM – RUTAS PÚBLICAS
# ==========================================

@bp.route('/api/hiker/check/<cedula>')
def check_hiker(cedula):
    # API Silenciosa para autocompletar formularios si el caminante ya existe
    try:
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        if hiker:
            # Shield para fecha_nacimiento física
            f_nac_str = ""
            try:
                if hasattr(hiker, 'fecha_nacimiento') and hiker.fecha_nacimiento:
                    f_nac_str = hiker.fecha_nacimiento.strftime('%Y-%m-%d')
            except:
                f_nac_str = ""

            return jsonify({
                'found': True,
                'nombre_completo': hiker.nombre_completo,
                'telefono': hiker.telefono,
                'fecha_nacimiento': f_nac_str,
                'tipo_sangre': hiker.tipo_sangre,
                'alergias': hiker.alergias,
                'enfermedades_cronicas': hiker.enfermedades_cronicas,
                'contacto_emergencia_nombre': hiker.contacto_emergencia_nombre,
                'contacto_emergencia_telefono': hiker.contacto_emergencia_telefono
            })
    except:
        pass
    return jsonify({'found': False})


@bp.route('/api/hiker/register', methods=['POST'])
def register_hiker():
    data = request.get_json()
    
    try:
        cedula = data.get('cedula', '').strip()
        event_id = data.get('event_id')
        
        if not cedula:
            return jsonify({'success': False, 'error': 'La cédula es obligatoria'}), 400

        # 1. ESCUDO ANTI-DUPLICADOS (Buscamos si la cédula ya existe)
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        
        if not hiker:
            # Si NO existe, creamos un nuevo caminante
            hiker = Hiker(cedula=cedula)
            db.session.add(hiker)
        
        # 2. ACTUALIZAMOS SIEMPRE SU INFORMACIÓN
        hiker.nombre_completo = data.get('nombre_completo', hiker.nombre_completo)
        hiker.telefono = data.get('telefono', hiker.telefono)
        hiker.tipo_sangre = data.get('tipo_sangre', hiker.tipo_sangre)
        hiker.alergias = data.get('alergias', hiker.alergias)
        hiker.enfermedades_cronicas = data.get('enfermedades_cronicas', hiker.enfermedades_cronicas)
        hiker.contacto_emergencia_nombre = data.get('contacto_emergencia_nombre', hiker.contacto_emergencia_nombre)
        hiker.contacto_emergencia_telefono = data.get('contacto_emergencia_telefono', hiker.contacto_emergencia_telefono)
        
        # INTEGRACIÓN SEGURA FECHA NACIMIENTO
        f_nac = data.get('fecha_nacimiento')
        if f_nac:
            try:
                # Solo intentamos guardar si la columna existe en el objeto
                hiker.fecha_nacimiento = datetime.strptime(f_nac, '%Y-%m-%d').date()
            except:
                pass

        # Generar PIN si es nuevo
        if not hiker.pin_secreto:
            import random, string
            hiker.pin_secreto = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            
        db.session.commit()

        # 3. REGISTRO AL EVENTO
        if event_id:
            inscripcion_existente = EventRegistration.query.filter_by(event_id=event_id, hiker_id=hiker.id).first()
            if not inscripcion_existente:
                nueva_inscripcion = EventRegistration(event_id=event_id, hiker_id=hiker.id)
                db.session.add(nueva_inscripcion)
                db.session.commit()

        return jsonify({'success': True, 'pin': hiker.pin_secreto})

    except Exception as e:
        db.session.rollback()
        print(f"Error registrando caminante: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/hiker/pin/<pin>')
def get_hiker_by_pin(pin):
    hiker = Hiker.query.filter_by(pin_secreto=pin).first()
    if hiker:
        f_nac = ""
        try:
            if hiker.fecha_nacimiento: f_nac = hiker.fecha_nacimiento.strftime('%Y-%m-%d')
        except: pass
        return jsonify({
            'found': True,
            'nombre_completo': hiker.nombre_completo,
            'cedula': hiker.cedula,
            'telefono': hiker.telefono,
            'tipo_sangre': hiker.tipo_sangre,
            'fecha_nacimiento': f_nac, 
            'alergias': hiker.alergias,
            'enfermedades_cronicas': hiker.enfermedades_cronicas,
            'contacto_emergencia_nombre': hiker.contacto_emergencia_nombre,
            'contacto_emergencia_telefono': hiker.contacto_emergencia_telefono
        })
    return jsonify({'found': False})
