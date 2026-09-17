from db import db
from models_core import PaymentMethod


def _seed_payment_methods():
    """Crea la tabla payment_method si no existe y semilla los métodos iniciales."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_method (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                tipo VARCHAR(20) NOT NULL,
                titular VARCHAR(200) NOT NULL,
                numero VARCHAR(100) NOT NULL,
                detalle VARCHAR(200),
                is_active BOOLEAN DEFAULT 1,
                orden INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

        if PaymentMethod.query.first():
            return

        seed = [
            PaymentMethod(tipo='sinpe', titular='Jenny Ceciliano Cordoba', numero='86529837', detalle='', orden=1),
            PaymentMethod(tipo='sinpe', titular='Jenny Ceciliano Cordoba', numero='87984232', detalle='', orden=2),
            PaymentMethod(tipo='sinpe', titular='Kenneth Ruiz Matamoros', numero='86227500', detalle='', orden=3),
            PaymentMethod(tipo='cuenta', titular='Jenny Ceciliano Cordoba', numero='CR66080402010100715103', detalle='Colones MUCAP', orden=1),
            PaymentMethod(tipo='cuenta', titular='Jenny Ceciliano Cordoba', numero='CR62015202001268129163', detalle='Colones BCR', orden=2),
            PaymentMethod(tipo='cuenta', titular='Kenneth Ruiz Matamoros', numero='CR19080403012501524778', detalle='Colones MUCAP', orden=3),
            PaymentMethod(tipo='cuenta', titular='Juan Carlos Ruiz', numero='CR61015202001292863793', detalle='Colones BCR', orden=4),
            PaymentMethod(tipo='cuenta', titular='Juan Carlos Ruiz', numero='CR50015202001410361158', detalle='Dolares BCR', orden=5),
        ]
        db.session.add_all(seed)
        db.session.commit()
    except Exception as e:
        print(f"[Migration] Error en _seed_payment_methods: {e}")
