from app import create_app
app = create_app()
with app.app_context():
    from models import User
    u = User.query.first()
    if not u:
        print('No user in DB')
    else:
        with app.test_client() as client:
            with client.session_transaction() as s:
                s['user_id'] = u.id
                s['role'] = u.role
            r = client.get('/profile')
            print('STATUS', r.status_code)
            data = r.data.decode('utf-8', errors='ignore')
            print('HAS PUNTOS ACCORDION:', 'Puntos y expediente' in data)
            print('HAS DESCARGAR:', 'Descargar estado de cuenta' in data)
            print('HAS WHATSAPP:', 'WhatsApp' in data)
            print('HAS ROL:', 'Rol de seguridad' in data)
