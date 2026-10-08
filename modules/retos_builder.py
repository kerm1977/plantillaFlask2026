# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/retos_builder.py - Constructor de retos (superusuario).
# Crea retos personalizados que aparecen en "Ganar puntos desde
# casa" con boton de confirmacion, puntos propios y enlace opcional.
from db import db
from models import Reto, SiteContent
from modules.retos import estado_reto, proximo_disponible, dias_reto, RETOS


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


def set_frecuencia(reto, dias):
    """Cambia la frecuencia (días) de un reto fijo ('datos'...) o personalizado ('custom_<id>')."""
    try:
        dias = int(dias)
    except (TypeError, ValueError):
        dias = 0
    if dias <= 0 or dias > 365:
        return {'ok': False, 'error': 'La frecuencia debe ser entre 1 y 365 días.'}
    if reto in RETOS:
        key = 'reto_dias_' + reto
        fila = SiteContent.query.filter_by(key=key).first()
        if fila:
            fila.value = str(dias)
        else:
            db.session.add(SiteContent(key=key, value=str(dias)))
        db.session.commit()
        return {'ok': True, 'mensaje': f'«{RETOS[reto]["label"]}» ahora se repite cada {dias} días.'}
    if reto.startswith('custom_'):
        try:
            r = Reto.query.get(int(reto.split('_', 1)[1]))
        except ValueError:
            r = None
        if not r:
            return {'ok': False, 'error': 'Reto no encontrado.'}
        r.frecuencia_dias = dias
        db.session.commit()
        return {'ok': True, 'mensaje': f'«{r.titulo}» ahora se repite cada {dias} días.'}
    return {'ok': False, 'error': 'Reto desconocido.'}


def fijos_con_dias():
    """Los 3 retos fijos con su frecuencia actual (para editarla en el panel)."""
    return [{'key': k, 'label': v['label'], 'dias': dias_reto(k)} for k, v in RETOS.items()]
