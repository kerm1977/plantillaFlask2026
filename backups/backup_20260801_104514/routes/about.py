from flask import request, jsonify, session
from models import SiteContent
from db import db
from routes import bp

# ==========================================
# CONTENIDO EDITABLE DEL SITIO
# ==========================================
DEFAULT_SITE_CONTENT = {
    'quienes_somos': (
        "En San Diego de la Unión de Cartago, nace en el mes de Octubre, un grupo de senderismo llamado "
        "la tribu de los libres y hace referencia a las tribus en general que siempre han sido los guardianes "
        "y amantes de la naturaleza.\n\n"
        "Lleva como base la filosofía Ubuntu, proveniente de las tribus sudafricanas y que significa:\n\n"
        "\u201cSoy porque tú eres. Eres porque somos.\u201d\n\n"
        "Pero Ubuntu, ni su significado, se refieren a ningún dogma político, ni religión, sino... "
        "Se trata de una ética mundial que se enfoca en la lealtad propia y con los demás, englobando el "
        "sentido de la vida visto con ojos de lealtad, estabilidad emocional y hermandad que se resume en que:\n\n"
        "\u201cTenemos la responsabilidad sobre los demás, especialmente sobre los vulnerables, y el medio ambiente.\u201d\n\n"
        "La vida de la tribu, es la voluntad de vivir la solidaridad entre iguales. Por eso, la tribu hiking "
        "hace énfasis a uno de sus lemas que lleva desde sus inicios:\n\n"
        "\u201cEsta es una historia escrita, con el cariño y el corazón de sus miembros\u201d"
    ),
    'mision': (
        "Ser el grupo de senderismo de referencia en Costa Rica, promoviendo la naturaleza, la hermandad "
        "y la filosofía Ubuntu entre sus miembros y comunidades."
    ),
    'vision': (
        "Inspirar a cada persona a reconectar con la naturaleza y con los demás, forjando lazos de lealtad, "
        "solidaridad y respeto mutuo en cada caminata, pero promoviendo la participación activa y sincera "
        "de esta bonita actividad."
    ),
    'valores': (
        "Hermandad: Creemos en la fuerza del grupo y en que cada miembro es esencial para el todo.\n"
        "Ubuntu: \u201cSoy porque tú eres. Eres porque somos.\u201d Es nuestra guía de vida.\n"
        "Respeto a la naturaleza: Somos guardianes del entorno que recorremos.\n"
        "Solidaridad: Tenemos la responsabilidad sobre los demás, especialmente sobre los vulnerables y el medio ambiente."
    ),
    'oracion': (
        "GRACIAS SEÑOR POR ESTE HERMOSO DÍA QUE NOS HAS REGALADO.\n\n"
        "POR NUESTROS AMIGOS Y AMIGAS QUE NOS ACOMPAÑAN EN ESTA ACTIVIDAD Y AQUELLOS QUE NO PUDIERON ESTAR HOY CON NOSOTROS.\n\n"
        "NOS AMPARAMOS A TU PROTECCIÓN Y LA DE NUESTROS FAMILIARES QUE NOS ESPERAN EN CASA.\n\n"
        "PROTEGE A LOS INDEFENSOS QUE SUFREN LA AGRESIÓN Y ABANDONO DE CUALQUIER TIPO.\n\n"
        "PONEMOS A TODAS LAS PERSONAS QUE ESTÁN EN LOS HOSPITALES, A LOS PRIVADOS DE LIBERTAD Y DE MOVIMIENTO QUE DESEAN TENER LA OPORTUNIDAD QUE NOSOTROS TENEMOS EN ESTE DÍA... ACOMPÁÑALOS Y DALES FUERZA PARA VENCER SU ANGUSTIA.\n\n"
        "QUE TU PROTECCIÓN LLEGUE A LOS DEMÁS GRUPOS Y SENDERISTAS DEL MUNDO QUE COMPARTEN NUESTRA MISMA PASIÓN PARA QUE LLEVEMOS UN CORAZÓN PASIVO, ALEGRE Y SERENO CON UN ESPÍRITU PROTECTOR DE LA NATURALEZA Y NUESTRO ENTORNO, DISFRUTANDO ASÍ CADA PASO QUE DAMOS EN NUESTRA NACIÓN Y NUESTRA TIERRA.\n\n"
        "QUE HOY LA NATURALEZA Y LA MONTAÑA SE SOMETAN A TU ORDEN Y A TU PROTECCIÓN..... PARA QUE CONVIVAMOS CON ELLA DE MANERA PASIVA Y ARMONIOSA.\n\n"
        "FORTALECE NUESTRA AMISTAD, NUESTRA HERMANDAD Y DIOS CUBRA CON SU SANGRE PRECIOSA A ESTE GRUPO LLAMADO LA TRIBU."
    )
}

def inject_site_content():
    for key, value in DEFAULT_SITE_CONTENT.items():
        if not SiteContent.query.filter_by(key=key).first():
            db.session.add(SiteContent(key=key, value=value))
    db.session.commit()


@bp.route('/api/about', methods=['GET'])
def get_about():
    rows = SiteContent.query.filter(SiteContent.key.in_(DEFAULT_SITE_CONTENT.keys())).all()
    data = {row.key: row.value for row in rows}
    return jsonify(data)


@bp.route('/api/about', methods=['POST'])
def update_about():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    payload = request.get_json()
    for key in DEFAULT_SITE_CONTENT.keys():
        if key in payload:
            row = SiteContent.query.filter_by(key=key).first()
            if row:
                row.value = payload[key]
            else:
                db.session.add(SiteContent(key=key, value=payload[key]))
    db.session.commit()
    return jsonify({'ok': True})
