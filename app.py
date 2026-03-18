import os
from flask import Flask
from db import db, configure_db_uri
from routes import bp
from users import inject_superusers

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_super_secreta_pwa')
    
    # Configuración inteligente de Base de Datos
    app.config['SQLALCHEMY_DATABASE_URI'] = configure_db_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        inject_superusers() # Inyección automática en el primer inicio

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)