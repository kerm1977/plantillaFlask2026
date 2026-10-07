# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/fidelidad.py - Programa de fidelidad: niveles VIP y multiplicador
# Niveles: 12+ participaciones -> Activo VIP (x1.2); 20+ -> Exclusivo VIP (x1.5).
# El multiplicador aplica a todo lo que suma puntos (participaciones, eventos
# de puntos, bienvenida, cumpleaños); NO a compras ni obsequios.
from datetime import datetime
from sqlalchemy import func
from db import db
from models import HikerPoints, FidelidadAjuste, FidelidadLog

NIVEL_NORMAL = 'normal'
NIVEL_ACTIVO = 'activo'
NIVEL_EXCLUSIVO = 'exclusivo'
NIVELES = (NIVEL_NORMAL, NIVEL_ACTIVO, NIVEL_EXCLUSIVO)
MIN_ACTIVO = 12
MIN_EXCLUSIVO = 20
MULTIPLICADORES = {NIVEL_NORMAL: 1.0, NIVEL_ACTIVO: 1.2, NIVEL_EXCLUSIVO: 1.5}
ETIQUETAS = {NIVEL_ACTIVO: 'Activo VIP', NIVEL_EXCLUSIVO: 'Exclusivo VIP', NIVEL_NORMAL: ''}


def participaciones(cedula):
    """Caminatas participadas: eventos con puntos de participación, menos retiros."""
    ganadas = (db.session.query(func.count(func.distinct(HikerPoints.event_id)))
               .filter(HikerPoints.cedula == cedula, HikerPoints.tipo == 'participacion',
                       HikerPoints.event_id.isnot(None)).scalar() or 0)
    retiradas = (db.session.query(func.count(func.distinct(HikerPoints.event_id)))
                 .filter(HikerPoints.cedula == cedula, HikerPoints.tipo == 'retiro',
                         HikerPoints.event_id.isnot(None)).scalar() or 0)
    return max(0, int(ganadas) - int(retiradas))


def nivel_auto(cedula):
    n = participaciones(cedula)
    if n >= MIN_EXCLUSIVO:
        return NIVEL_EXCLUSIVO
    if n >= MIN_ACTIVO:
        return NIVEL_ACTIVO
    return NIVEL_NORMAL


def nivel_efectivo(cedula):
    """Nivel vigente: el ajuste manual manda; si no hay, el automático."""
    ajuste = FidelidadAjuste.query.filter_by(cedula=cedula).first()
    if ajuste:
        return ajuste.nivel, True
    return nivel_auto(cedula), False


def multiplicador(cedula):
    nivel, _ = nivel_efectivo(cedula)
    return MULTIPLICADORES.get(nivel, 1.0)


def puntos_con_bono(cedula, puntos_base):
    """Puntos finales tras el multiplicador del nivel vigente."""
    return int(round(puntos_base * multiplicador(cedula)))


def etiqueta_bono(cedula, puntos_base):
    """Texto para el detalle: ' — Exclusivo VIP ×1.5: 500 → 750' (o '' si normal)."""
    nivel, _ = nivel_efectivo(cedula)
    if nivel == NIVEL_NORMAL:
        return ''
    return f' — {ETIQUETAS[nivel]} ×{MULTIPLICADORES[nivel]}: {puntos_base} → {puntos_con_bono(cedula, puntos_base)}'


def info(cedula):
    """Resumen para pantallas: nivel, insignia, multiplicador y participaciones."""
    nivel, manual = nivel_efectivo(cedula)
    return {
        'nivel': nivel,
        'nivel_label': ETIQUETAS.get(nivel) or 'Sin nivel VIP',
        'es_vip': nivel != NIVEL_NORMAL,
        'manual': manual,
        'multiplicador': MULTIPLICADORES.get(nivel, 1.0),
        'participaciones': participaciones(cedula),
        'nivel_auto': nivel_auto(cedula),
        'nota': (FidelidadAjuste.query.filter_by(cedula=cedula).first().nota if manual else ''),
    }


def cambiar_nivel(cedula, nivel_nuevo, nota, operator):
    """Ajuste manual del nivel. 'auto' quita el ajuste y vuelve al cálculo por
    participaciones. La nota es obligatoria cuando el nivel efectivo baja."""
    if nivel_nuevo not in ('auto', NIVEL_ACTIVO, NIVEL_EXCLUSIVO):
        return {'ok': False, 'error': 'Nivel no válido.'}
    actual, _ = nivel_efectivo(cedula)
    destino = nivel_auto(cedula) if nivel_nuevo == 'auto' else nivel_nuevo
    if NIVELES.index(destino) < NIVELES.index(actual) and not (nota or '').strip():
        return {'ok': False, 'error': 'Para degradar el nivel tenés que indicar el motivo en la nota.'}
    ajuste = FidelidadAjuste.query.filter_by(cedula=cedula).first()
    if nivel_nuevo == 'auto':
        if ajuste:
            db.session.delete(ajuste)
    elif ajuste:
        ajuste.nivel = nivel_nuevo
        ajuste.nota = (nota or '').strip()
        ajuste.created_by = operator
    else:
        db.session.add(FidelidadAjuste(cedula=cedula, nivel=nivel_nuevo,
                                       nota=(nota or '').strip(), created_by=operator))
    db.session.add(FidelidadLog(cedula=cedula, nivel_anterior=actual, nivel_nuevo=destino,
                                origen='manual', nota=(nota or '').strip(),
                                created_by=operator, created_at=datetime.utcnow()))
    db.session.commit()
    return {'ok': True, 'nivel': destino, 'nivel_label': ETIQUETAS.get(destino) or 'Sin nivel VIP'}


def historial(cedula=None):
    q = FidelidadLog.query
    if cedula:
        q = q.filter_by(cedula=cedula)
    return q.order_by(FidelidadLog.created_at.desc()).limit(50).all()
