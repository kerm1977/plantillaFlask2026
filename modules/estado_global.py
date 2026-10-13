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

MOV_VACIO = {'ganados': 0, 'perdidos': 0, 'participo': set(), 'retiro': set(),
             'donados': 0, 'obsequiados': 0, 'restados': 0}


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
            'donados': 0, 'obsequiados': 0, 'restados': 0,
        })
        pts = r.points or 0
        if pts > 0:
            info['ganados'] += pts
        elif pts < 0:
            info['perdidos'] += -pts
        if r.tipo in ('donacion_envio', 'donacion_benefica') and pts < 0:
            info['donados'] += -pts
        elif r.tipo in ('donacion_recibida', 'obsequio') and pts > 0:
            info['obsequiados'] += pts
        elif r.tipo == 'resta' and pts < 0:
            info['restados'] += -pts
        if r.event_id:
            if r.tipo == 'participacion':
                info['participo'].add(r.event_id)
            elif r.tipo == 'retiro':
                info['retiro'].add(r.event_id)
    return por_cedula


def _fila_persona(h, mov, eventos, supers):
    """Dict con el resumen de una persona para la lista y el detalle."""
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
    return {
        'cedula': h.cedula,
        'nombre': h.nombre_completo or '(Sin nombre)',
        'es_super': email in supers,
        'total': mov['ganados'] - mov['perdidos'],
        'ganados': mov['ganados'],
        'perdidos': mov['perdidos'],
        'donados': mov.get('donados', 0),
        'obsequiados': mov.get('obsequiados', 0),
        'restados': mov.get('restados', 0),
        'retiros': len(mov['retiro']),
        'caminatas_ok': caminatas_ok,
        'caminatas_no': caminatas_no,
    }


def resumen_global():
    """Lista de resumenes por hiker (ordenada por nombre) para el modal de gestion."""
    from modules import fidelidad
    from models import FidelidadAjuste
    eventos = _eventos_realizados()
    movimientos = _movimientos_por_cedula()
    supers = _superuser_emails()
    ajustes = {a.cedula: a.nivel for a in FidelidadAjuste.query.all()}
    filas = [_fila_persona(h, movimientos.get(h.cedula, MOV_VACIO), eventos, supers)
             for h in Hiker.query.order_by(Hiker.nombre_completo).all()]
    for f in filas:
        n = len(f['caminatas_ok'])
        nivel = ajustes.get(f['cedula']) or (
            'exclusivo' if n >= fidelidad.MIN_EXCLUSIVO
            else 'activo' if n >= fidelidad.MIN_ACTIVO else 'normal')
        f['vip'] = nivel
        f['vip_label'] = fidelidad.ETIQUETAS.get(nivel) or 'Sin nivel VIP'
    return filas


def detalle_persona(cedula):
    """Resumen completo de una persona + info de fidelidad, para la ventana de detalle."""
    from modules import fidelidad
    h = Hiker.query.filter_by(cedula=cedula).first()
    if not h:
        return None
    fila = _fila_persona(h, _movimientos_por_cedula().get(cedula, MOV_VACIO),
                         _eventos_realizados(), _superuser_emails())
    fila['fidelidad'] = fidelidad.info(cedula)
    return fila


def get_stats_desde():
    """Fecha/hora desde la que cuentan las estadísticas personales.
    None = cuentan desde siempre. Los puntos reales NUNCA se tocan."""
    from models import SiteContent
    from datetime import datetime
    row = SiteContent.query.filter_by(key='puntos_stats_desde').first()
    if not row or not row.value:
        return None
    try:
        return datetime.fromisoformat(row.value)
    except ValueError:
        return None


def reset_stats_desde():
    """Restaura las estadísticas a cero: todo empieza a contar desde ahora."""
    from models import SiteContent
    from db import db
    from datetime import datetime
    valor = datetime.utcnow().isoformat()
    row = SiteContent.query.filter_by(key='puntos_stats_desde').first()
    if row:
        row.value = valor
    else:
        db.session.add(SiteContent(key='puntos_stats_desde', value=valor))
    db.session.commit()


def estadisticas_persona(cedula):
    """Estadísticas detalladas de una persona para el gráfico, las listas
    paginadas de caminatas y la descarga de su propia estadística.
    Solo cuenta movimientos posteriores a `puntos_stats_desde` (los puntos
    reales de la persona no se modifican nunca)."""
    from models import SiteContent
    h = Hiker.query.filter_by(cedula=cedula).first()
    if not h:
        return None
    desde = get_stats_desde()
    rows = [r for r in HikerPoints.query.filter_by(cedula=cedula).all()
            if not desde or (r.created_at and r.created_at >= desde)]
    ganados = sum(r.points for r in rows if (r.points or 0) > 0)
    perdidos = sum(-r.points for r in rows if (r.points or 0) < 0)
    comprados = sum(r.points for r in rows if r.tipo == 'compra' and (r.points or 0) > 0)
    donados = sum(-r.points for r in rows if r.tipo in ('donacion_envio', 'donacion_benefica') and (r.points or 0) < 0)
    redimidos = sum(-r.points for r in rows if (r.tipo or '').startswith('redencion') and (r.points or 0) < 0)
    # Excedente "de la casa" generado por las compras de esta persona
    engine = get_points_engine()
    casa = sum((engine.purchase_cost(r.points) or {}).get('fee', 0)
               for r in rows if r.tipo == 'compra' and (r.points or 0) > 0)
    participo_ids = {r.event_id for r in rows if r.tipo == 'participacion' and r.event_id} \
        - {r.event_id for r in rows if r.tipo == 'retiro' and r.event_id}
    visitados = Event.query.filter_by(visitado='Visitados').all()

    def _evento_fecha(e):
        for attr in ('fecha_unica', 'fecha_inicio', 'fecha_regreso'):
            val = getattr(e, attr, None)
            if val:
                try:
                    from datetime import datetime as _dt
                    return _dt.strptime(str(val).strip()[:10], '%Y-%m-%d').date()
                except (ValueError, AttributeError):
                    continue
        return None

    if desde:
        desde_d = desde.date()
        visitados = [e for e in visitados
                     if _evento_fecha(e) and _evento_fecha(e) >= desde_d]
    caminatas_ok = sorted((e.nombre_lugar or 'Sin nombre') for e in visitados if e.id in participo_ids)
    extras = participo_ids - {e.id for e in visitados}
    if extras:
        caminatas_ok += sorted((e.nombre_lugar or 'Sin nombre')
                               for e in Event.query.filter(Event.id.in_(extras)).all())
    caminatas_no = sorted((e.nombre_lugar or 'Sin nombre') for e in visitados if e.id not in participo_ids)
    # Puntos posibles: valor configurado del evento o, si es 0 (eventos viejos),
    # el máximo que otorgó realmente en participaciones.
    max_otorgado = {}
    for r in HikerPoints.query.filter_by(tipo='participacion').all():
        if r.event_id:
            max_otorgado[r.event_id] = max(max_otorgado.get(r.event_id, 0), r.points or 0)

    def _valor_evento(e):
        return e.puntos or max_otorgado.get(e.id, 0)

    posibles = sum(_valor_evento(e) for e in visitados)
    if extras:
        posibles += sum(_valor_evento(e)
                        for e in Event.query.filter(Event.id.in_(extras)).all())
    # Participación y faltas por mes (participaciones por fecha del escaneo,
    # faltas por fecha de la caminata visitada)
    MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    por_mes = {}
    for r in rows:
        if not (r.event_id and r.created_at):
            continue
        k = r.created_at.strftime('%Y-%m')
        if r.tipo == 'participacion':
            por_mes.setdefault(k, {'ok': 0, 'no': 0})['ok'] += 1
        elif r.tipo == 'retiro':
            por_mes.setdefault(k, {'ok': 0, 'no': 0})['no'] += 1
    for e in visitados:
        if e.id in participo_ids:
            continue
        f = _evento_fecha(e)
        if f:
            por_mes.setdefault(f.strftime('%Y-%m'), {'ok': 0, 'no': 0})['no'] += 1
    meses = [{'mes': k,
              'label': f'{MESES[int(k[5:7]) - 1]} {k[:4]}',
              'ok': v['ok'], 'no': v['no']}
             for k, v in sorted(por_mes.items())]
    flag = SiteContent.query.filter_by(key='carnet_descargado_' + cedula).first()
    return {
        'nombre': h.nombre_completo or '', 'cedula': cedula,
        'ganados': ganados, 'perdidos': perdidos, 'total': ganados - perdidos,
        'comprados': comprados, 'donados': donados, 'redimidos': redimidos,
        'casa': casa, 'caminatas_ok': caminatas_ok, 'caminatas_no': caminatas_no,
        'posibles': posibles,
        'meses': meses,
        'carnet_descargado': flag.value if flag else '',
        'desde': desde.strftime('%d/%m/%Y') if desde else '',
    }


def get_points_engine():
    from modules.points_engine import get_points_engine as _g
    return _g()
