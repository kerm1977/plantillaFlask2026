from db import db
from models_forms import Form, CotizadorLugar
from app import create_app

app = create_app()
with app.app_context():
    # Buscar el formulario más reciente
    form = Form.query.order_by(Form.id.desc()).first()
    if form:
        print(f'Formulario más reciente: ID {form.id}, Nombre: {form.name}, Tipo: {form.form_type}')
        lugares = CotizadorLugar.query.filter_by(form_id=form.id).all()
        print(f'Lugares en base de datos: {len(lugares)}')
        for lugar in lugares:
            print(f'  - ID: {lugar.id}, Nombre: {lugar.nombre}, Moneda: {lugar.moneda}')
    else:
        print('No hay formularios en la base de datos')
