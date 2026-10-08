# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/retos_builder.py - Constructor de retos (superusuario).
# Crea retos personalizados que aparecen en "Ganar puntos desde
# casa" con boton de confirmacion, puntos propios y enlace opcional.
from db import db
from models import Reto
from modules.retos import estado_reto, proximo_disponible


def crear_custom(titulo, texto, puntos, enlace, frecuencia, operador):
    """Crea un reto personalizado que aparece en "Ganar puntos desde casa"."""
    titulo = (titulo or '').strip()[:120]
    texto = (texto or '').strip()[:500]
    enlace = (enlace or '').strip()[:300]
    try:
        puntos = int(puntos)
    except (TypeError, ValueError):
        puntos = 0
    try:
        frecuencia = int(frecuencia)
    except (TypeError, ValueError):
        frecuencia = 30
    if frecuencia <= 0 or frecuencia > 365:
        frecuencia = 30
    if not titulo or not texto:
        return {'ok': False, 'error': 'El reto necesita título y descripción.'}
    if puntos <= 0 or puntos > 100000:
        return {'ok': False, 'error': 'Los puntos deben ser un número entre 1 y 100.000.'}
    if enlace and not enlace.startswith(('http://', 'https://')):
        return {'ok': False, 'error': 'El enlace debe empezar con http:// o https://'}
    db.session.add(Reto(titulo=titulo, texto=texto, puntos=puntos, enlace=enlace,
                        frecuencia_dias=frecuencia, activo=True, created_by=operador or 'admin'))
    db.session.commit()
    return {'ok': True, 'mensaje': f'Reto creado: «{titulo}» por {puntos} puntos cada {frecuencia} días.'}


def toggle_custom(rid):
    """Activa o desactiva un reto personalizado (no se borra para no perder el historial)."""
    r = Reto.query.get(rid)
    if not r:
        return {'ok': False, 'error': 'Reto no encontrado.'}
    r.activo = not r.activo
    db.session.commit()
    return {'ok': True, 'mensaje': f'Reto «{r.titulo}» {"activado" if r.activo else "desactivado"}.'}


def lista_custom(cedula):
    """Retos personalizados activos con el estado que tienen para esta cédula."""
    out = []
    for r in Reto.query.filter_by(activo=True).order_by(Reto.id).all():
        key = 'custom_' + str(r.id)
        out.append({'key': key, 'titulo': r.titulo, 'texto': r.texto, 'puntos': r.puntos,
                    'enlace': r.enlace or '', 'dias': r.frecuencia_dias or 30,
                    'estado': estado_reto(cedula, key),
                    'proximo': proximo_disponible(cedula, key)})
    return out


def todos_custom():
    return Reto.query.order_by(Reto.id.desc()).all()
