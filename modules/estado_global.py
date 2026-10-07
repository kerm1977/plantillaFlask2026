# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/estado_global.py - Estado de cuenta de todas las personas.
# Solo lo usa la vista de gestion del superusuario en Mis puntos.
# Resume por persona: estatus (superusuario/regular), total de puntos,
# caminatas participadas y no participadas (con nombres), puntos
# ganados y puntos perdidos.
from models import Event, Hiker, HikerPoints, User


def _superuser_emails():
    """Correos (en minuscula) de usuarios con rol Superusuario."""
    return {u.email.strip().lower() for u in User.query.filter_by(role='Superusuario').all() if u.email}


def _eventos_realizados():
    """Caminatas ya realizadas: visitado == 'Visitados'. Devuelve {id: nombre}."""
    return {e.id: (e.nombre_lugar or 'Sin nombre') for e in Event.query.filter_by(visitado='Visitados').all()}


def _movimientos_por_cedula():
    """Agrupa los movimientos de puntos por cedula:
    {cedula: {'ganados': int, 'perdidos': int, 'participo': set, 'retiro': set}}"""
    por_cedula = {}
    for r in HikerPoints.query.all():
        info = por_cedula.setdefault(r.cedula, {
            'ganados': 0, 'perdidos': 0, 'participo': set(), 'retiro': set(),
        })
        pts = r.points or 0
        if pts > 0:
            info['ganados'] += pts
        elif pts < 0:
            info['perdidos'] += -pts
        if r.event_id:
            if r.tipo == 'participacion':
                info['participo'].add(r.event_id)
            elif r.tipo == 'retiro':
                info['retiro'].add(r.event_id)
    return por_cedula


def resumen_global():
    """Lista de dicts por hiker (ordenada por nombre) para la tabla de gestion."""
    eventos = _eventos_realizados()
    movimientos = _movimientos_por_cedula()
    supers = _superuser_emails()
    resumen = []
    for h in Hiker.query.order_by(Hiker.nombre_completo).all():
        mov = movimientos.get(h.cedula, {'ganados': 0, 'perdidos': 0, 'participo': set(), 'retiro': set()})
        participo_ids = mov['participo'] - mov['retiro']
        caminatas_ok = sorted(eventos[eid] for eid in participo_ids if eid in eventos)
        # Participaciones en eventos no marcados 'Visitados' igual cuentan y se listan.
        otros_ids = participo_ids - set(eventos.keys())
        if otros_ids:
            nombres_extra = {e.id: (e.nombre_lugar or 'Sin nombre')
                             for e in Event.query.filter(Event.id.in_(otros_ids)).all()}
            caminatas_ok += sorted(nombres_extra.values())
        caminatas_no = sorted(nombre for eid, nombre in eventos.items() if eid not in participo_ids)
        email = (h.card_email or '').strip().lower()
        resumen.append({
            'cedula': h.cedula,
            'nombre': h.nombre_completo or '(Sin nombre)',
            'es_super': email in supers,
            'total': mov['ganados'] - mov['perdidos'],
            'ganados': mov['ganados'],
            'perdidos': mov['perdidos'],
            'caminatas_ok': caminatas_ok,
            'caminatas_no': caminatas_no,
        })
    return resumen
