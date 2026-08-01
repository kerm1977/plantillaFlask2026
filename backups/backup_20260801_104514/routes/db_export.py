import os
import json
import random
import string as _str2
from flask import request, jsonify, session, Response
from models import User, Hiker, Event, EventRegistration, Notification, SiteContent
from db import db
from datetime import datetime
from routes import bp, _PROJECT_ROOT

# ==========================================
# EXPORTAR / IMPORTAR BASE DE DATOS
# ==========================================

def _serialize_row(obj, date_fields=(), datetime_fields=()):
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if val is None:
            d[col.name] = None
        elif hasattr(val, 'isoformat'):
            d[col.name] = val.isoformat()
        else:
            d[col.name] = val
    return d


@bp.route('/api/admin/db/export')
def db_export_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        payload = {
            'exported_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'tables': {
                'users':               [_serialize_row(r) for r in User.query.all()],
                'hikers':              [_serialize_row(r) for r in Hiker.query.all()],
                'events':              [_serialize_row(r) for r in Event.query.all()],
                'event_registrations': [_serialize_row(r) for r in EventRegistration.query.all()],
                'notifications':       [_serialize_row(r) for r in Notification.query.all()],
                'site_content':        [_serialize_row(r) for r in SiteContent.query.all()],
            }
        }
        ts       = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        fname    = f'db_export_{ts}.json'
        raw      = json.dumps(payload, ensure_ascii=False, indent=2)
        return Response(
            raw,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename="{fname}"'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/admin/db/import', methods=['POST'])
def db_import_json():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        data = request.get_json()
        if not data or 'tables' not in data:
            return jsonify({'error': 'Formato de archivo inválido'}), 400
        tables   = data['tables']
        stats    = {}

        # --- Hikers ---
        added = skipped = 0
        for row in tables.get('hikers', []):
            cedula = row.get('cedula')
            nombre = row.get('nombre_completo', '')
            if cedula:
                if Hiker.query.filter_by(cedula=cedula).first():
                    skipped += 1; continue
            else:
                if Hiker.query.filter_by(nombre_completo=nombre).first():
                    skipped += 1; continue
                cedula = 'SC-' + ''.join(random.choices(_str2.digits, k=8))
            h = Hiker(
                cedula=cedula, nombre_completo=nombre,
                telefono=row.get('telefono'), tipo_sangre=row.get('tipo_sangre'),
                alergias=row.get('alergias'), enfermedades_cronicas=row.get('enfermedades_cronicas'),
                contacto_emergencia_nombre=row.get('contacto_emergencia_nombre'),
                contacto_emergencia_telefono=row.get('contacto_emergencia_telefono'),
                pin_secreto=row.get('pin_secreto')
            )
            if row.get('fecha_nacimiento'):
                try: h.fecha_nacimiento = datetime.strptime(row['fecha_nacimiento'][:10], '%Y-%m-%d').date()
                except: pass
            db.session.add(h); added += 1
        db.session.commit()
        stats['hikers'] = {'added': added, 'skipped': skipped}

        # --- Users ---
        added = skipped = 0
        for row in tables.get('users', []):
            if User.query.filter_by(email=row.get('email','').lower()).first():
                skipped += 1; continue
            u = User(
                name=row.get('name'), last_name_1=row.get('last_name_1'),
                last_name_2=row.get('last_name_2'), email=row.get('email','').lower(),
                password_hash=row.get('password_hash', ''), role=row.get('role','Usuario'),
                status=row.get('status','Activo'), phone=row.get('phone'),
                phone_code=row.get('phone_code'), avatar=row.get('avatar','default.png')
            )
            if row.get('dob'):
                try: u.dob = datetime.strptime(row['dob'][:10], '%Y-%m-%d').date()
                except: pass
            db.session.add(u); added += 1
        db.session.commit()
        stats['users'] = {'added': added, 'skipped': skipped}

        # --- SiteContent ---
        added = skipped = 0
        for row in tables.get('site_content', []):
            if SiteContent.query.filter_by(key=row.get('key')).first():
                skipped += 1; continue
            db.session.add(SiteContent(key=row.get('key'), value=row.get('value',''))); added += 1
        db.session.commit()
        stats['site_content'] = {'added': added, 'skipped': skipped}

        return jsonify({'ok': True, 'stats': stats})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==========================================
# IMPORTAR contactos.json
# ==========================================
@bp.route('/api/admin/import/contactos', methods=['POST'])
def import_contactos():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        json_path = os.path.join(_PROJECT_ROOT, 'contactos.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            contacts = json.load(f)
        added = skipped = 0
        for c in contacts:
            cedula          = str(c.get('Cédula', '')).strip()
            nombre_completo = ' '.join(filter(None, [
                c.get('Nombre','').strip(),
                c.get('Primer Apellido','').strip(),
                c.get('Segundo Apellido','').strip()
            ]))
            if not nombre_completo:
                skipped += 1; continue
            if cedula and Hiker.query.filter_by(cedula=cedula).first():
                skipped += 1; continue
            if not cedula and Hiker.query.filter_by(nombre_completo=nombre_completo).first():
                skipped += 1; continue
            pin = ''.join(random.choices(_str2.ascii_uppercase + _str2.digits, k=6))
            if not cedula:
                cedula = 'SC-' + ''.join(random.choices(_str2.digits, k=8))
            db.session.add(Hiker(
                cedula=cedula,
                nombre_completo=nombre_completo,
                pin_secreto=pin
            ))
            added += 1
        db.session.commit()
        return jsonify({'ok': True, 'added': added, 'skipped': skipped})
    except FileNotFoundError:
        return jsonify({'error': 'contactos.json no encontrado en el servidor'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
