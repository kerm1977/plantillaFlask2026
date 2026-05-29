import re
from flask import jsonify, session
from models import User, Hiker
from routes import bp

# ==========================================
# RUTAS DE ADMINISTRACIÓN – LECTURA
# ==========================================

@bp.route('/api/admin/users')
def admin_get_users():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    users = User.query.all()
    hikers = Hiker.query.all()
    hiker_by_phone = {}
    for h in hikers:
        if h.telefono:
            clean = re.sub(r'\D', '', h.telefono)
            if clean:
                hiker_by_phone[clean] = h
    output = []
    for u in users:
        u_phone_clean = re.sub(r'\D', '', u.phone or '')
        hiker = hiker_by_phone.get(u_phone_clean)
        f_nac = ''
        if hiker:
            try:
                if hasattr(hiker, 'fecha_nacimiento') and hiker.fecha_nacimiento:
                    f_nac = hiker.fecha_nacimiento.strftime('%Y-%m-%d')
            except: pass
        output.append({
            'id': u.id,
            'name': u.name,
            'last_name_1': u.last_name_1,
            'last_name_2': u.last_name_2,
            'email': u.email,
            'role': u.role,
            'status': u.status,
            'dob': u.dob.strftime('%Y-%m-%d') if u.dob else None,
            'phone': f"{u.phone_code or ''} {u.phone or 'No registrado'}",
            'created': u.created_at.strftime('%d de %B, %Y - %H:%M') if u.created_at else 'N/A',
            'updated': u.updated_at.strftime('%d de %B, %Y - %H:%M') if u.updated_at else 'N/A',
            'avatar': u.avatar,
            'crm_cedula': hiker.cedula if hiker else None,
            'crm_tipo_sangre': hiker.tipo_sangre if hiker else None,
            'crm_alergias': hiker.alergias if hiker else None,
            'crm_enfermedades': getattr(hiker, 'enfermedades_cronicas', '') if hiker else None,
            'crm_emergencia_nombre': hiker.contacto_emergencia_nombre if hiker else None,
            'crm_emergencia_tel': hiker.contacto_emergencia_telefono if hiker else None,
            'crm_fecha_nac': f_nac
        })
    return jsonify(output)


@bp.route('/api/admin/all_contacts')
def admin_get_all_contacts():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    users = User.query.all()
    hikers = Hiker.query.all()

    hiker_by_phone = {}
    for h in hikers:
        if h.telefono:
            clean = re.sub(r'\D', '', h.telefono)
            if clean:
                hiker_by_phone[clean] = h

    matched_hiker_ids = set()
    output = []

    for u in users:
        u_phone_clean = re.sub(r'\D', '', u.phone or '')
        hiker = hiker_by_phone.get(u_phone_clean)
        if hiker:
            matched_hiker_ids.add(hiker.id)
        f_nac = ''
        if hiker:
            try:
                if hasattr(hiker, 'fecha_nacimiento') and hiker.fecha_nacimiento:
                    f_nac = hiker.fecha_nacimiento.strftime('%Y-%m-%d')
            except: pass
        output.append({
            'type': 'user',
            'id': u.id,
            'display_name': f'{u.name} {u.last_name_1} {u.last_name_2}',
            'name': u.name, 'last_name_1': u.last_name_1, 'last_name_2': u.last_name_2,
            'email': u.email, 'role': u.role, 'status': u.status,
            'dob': u.dob.strftime('%Y-%m-%d') if u.dob else None,
            'phone': f"{u.phone_code or ''} {u.phone or 'No registrado'}",
            'created': u.created_at.strftime('%d/%m/%Y') if u.created_at else 'N/A',
            'updated': u.updated_at.strftime('%d/%m/%Y') if u.updated_at else 'N/A',
            'avatar': u.avatar,
            'crm_cedula': hiker.cedula if hiker else None,
            'crm_tipo_sangre': hiker.tipo_sangre if hiker else None,
            'crm_alergias': hiker.alergias if hiker else None,
            'crm_enfermedades': getattr(hiker, 'enfermedades_cronicas', '') if hiker else None,
            'crm_emergencia_nombre': hiker.contacto_emergencia_nombre if hiker else None,
            'crm_emergencia_tel': hiker.contacto_emergencia_telefono if hiker else None,
            'crm_fecha_nac': f_nac
        })

    for h in hikers:
        if h.id in matched_hiker_ids:
            continue
        f_nac = ''
        try:
            if hasattr(h, 'fecha_nacimiento') and h.fecha_nacimiento:
                f_nac = h.fecha_nacimiento.strftime('%Y-%m-%d')
        except: pass
        output.append({
            'type': 'hiker',
            'id': f'h{h.id}',
            'hiker_id': h.id,
            'display_name': h.nombre_completo or 'Sin nombre',
            'phone': h.telefono or 'No registrado',
            'crm_cedula': h.cedula,
            'crm_tipo_sangre': h.tipo_sangre,
            'crm_alergias': h.alergias,
            'crm_enfermedades': getattr(h, 'enfermedades_cronicas', ''),
            'crm_emergencia_nombre': h.contacto_emergencia_nombre,
            'crm_emergencia_tel': h.contacto_emergencia_telefono,
            'crm_fecha_nac': f_nac,
            'pin_secreto': h.pin_secreto
        })

    return jsonify(output)
