from app import create_app
app = create_app()
with app.app_context():
    from models import Hiker
    h = Hiker.query.first()
    if not h:
        print('NO HIKER')
    else:
        with app.test_client() as c:
            with c.session_transaction() as s:
                s['role'] = 'Superusuario'
                s['user_id'] = 1
            r = c.get('/mis-puntos?cedula='+h.cedula)
            data = r.data.decode('utf-8', errors='ignore')
            print('GET STATUS', r.status_code)
            print('HAS modalObsequiar:', 'modalObsequiar' in data)
            print('HAS modalRestar:', 'modalRestar' in data)
            print('HAS modalRedimir:', 'modalRedimir' in data)
            print('HAS history card:', h.evento_nombre if hasattr(h,'evento_nombre') else 'hiker' in data)
            # POST obsequiar
            r2 = c.post('/mis-puntos', data={'cedula': h.cedula, 'accion': 'obsequiar', 'monto': '1', 'detalle': 'prueba'})
            print('POST obsequiar STATUS', r2.status_code)
