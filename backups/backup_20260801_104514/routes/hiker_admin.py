from flask import jsonify, session
from models import Hiker, EventRegistration
from db import db
from sqlalchemy import text
from routes import bp

# ==========================================
# SISTEMA CRM – RUTAS ADMIN
# ==========================================

@bp.route('/api/admin/fix_database')
def fix_database():
    """
    Ruta de emergencia para inyectar la columna faltante en producción 
    sin consola, sin apagar el servidor y sin perder datos.
    """
    if session.get('role') != 'Superusuario':
        return "Acceso denegado. Debes iniciar sesión como administrador.", 403
    try:
        db.session.execute(text("ALTER TABLE hiker ADD COLUMN fecha_nacimiento DATE"))
        db.session.commit()
        return "<h1>Base de datos actualizada con éxito.</h1><p>La columna 'fecha_nacimiento' fue agregada.</p><a href='/'>Volver al inicio</a>"
    except Exception as e:
        db.session.rollback()
        return f"<h1>Resultado</h1><p>{str(e)}</p><p><b>Si el error dice 'duplicate column name', la columna ya existe y tu base de datos está perfecta.</b></p><a href='/'>Volver al inicio</a>"


@bp.route('/api/admin/hikers')
def admin_get_hikers():
    """
    Ruta para el Directorio CRM con protección contra fallos físicos de la DB.
    Si la columna fecha_nacimiento falta, el API sigue enviando los registros
    omitiendo solo ese dato, evitando el error de JSON en el CRM.
    """
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        hikers = Hiker.query.all()
        output = []
        for h in hikers:
            # Escudo de lectura para la columna conflictiva
            f_nac = ""
            try:
                if hasattr(h, 'fecha_nacimiento') and h.fecha_nacimiento:
                    f_nac = h.fecha_nacimiento.strftime('%Y-%m-%d')
            except:
                f_nac = ""

            output.append({
                'id': h.id,
                'cedula': h.cedula,
                'nombre_completo': h.nombre_completo,
                'telefono': h.telefono,
                'tipo_sangre': h.tipo_sangre,
                'fecha_nacimiento': f_nac, 
                'alergias': h.alergias,
                'enfermedades_cronicas': getattr(h, 'enfermedades_cronicas', ""),
                'contacto_emergencia_nombre': h.contacto_emergencia_nombre,
                'contacto_emergencia_telefono': h.contacto_emergencia_telefono,
                'pin_secreto': h.pin_secreto
            })
        return jsonify(output)
        
    except Exception as e:
        # SI LA CONSULTA ORM FALLA TOTALMENTE (SELECT fallido por columna faltante)
        if "no such column: hiker.fecha_nacimiento" in str(e):
            print("EJECUTANDO SALVAVIDAS: Columna fecha_nacimiento no encontrada físicamente.")
            sql = text("SELECT id, cedula, nombre_completo, telefono, tipo_sangre, alergias, enfermedades_cronicas, contacto_emergencia_nombre, contacto_emergencia_telefono, pin_secreto FROM hiker")
            result = db.session.execute(sql)
            output = []
            for row in result:
                output.append({
                    'id': row[0], 'cedula': row[1], 'nombre_completo': row[2], 'telefono': row[3],
                    'tipo_sangre': row[4], 'fecha_nacimiento': "", 'alergias': row[5],
                    'enfermedades_cronicas': row[6], 'contacto_emergencia_nombre': row[7],
                    'contacto_emergencia_telefono': row[8], 'pin_secreto': row[9]
                })
            return jsonify(output)
        
        return jsonify({'error': f"Error crítico en Base de Datos: {str(e)}"}), 500


@bp.route('/api/admin/delete_hiker/<int:hiker_id>', methods=['DELETE'])
def admin_delete_hiker(hiker_id):
    """
    Elimina a un caminante blindado contra errores físicos de base de datos.
    """
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        try:
            hiker = Hiker.query.get(hiker_id)
            if hiker:
                EventRegistration.query.filter_by(hiker_id=hiker_id).delete()
                db.session.delete(hiker)
                db.session.commit()
                return jsonify({'success': True})
        except Exception as e_orm:
            if "no such column" in str(e_orm):
                print(f"Salvavidas de borrado activado para ID {hiker_id}")
                db.session.rollback()
                db.session.execute(text("DELETE FROM event_registration WHERE hiker_id = :id"), {'id': hiker_id})
                db.session.execute(text("DELETE FROM hiker WHERE id = :id"), {'id': hiker_id})
                db.session.commit()
                return jsonify({'success': True})
            else:
                raise e_orm

        return jsonify({'error': 'Caminante no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        print(f"ERROR CRÍTICO AL BORRAR: {str(e)}")
        return jsonify({'error': f"Error al eliminar: {str(e)}"}), 500
