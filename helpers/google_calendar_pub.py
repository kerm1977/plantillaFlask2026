from urllib.parse import quote
from datetime import datetime, timedelta


def generate_google_calendar_link_pub(pub):
    """
    Genera un enlace para agregar un evento a Google Calendar.
    
    Args:
        pub: Objeto Publicacion con los datos de la actividad
    
    Returns:
        str: URL de Google Calendar para agregar el evento
    """
    # Título del evento
    title = pub.nombre or "Actividad"
    
    # Fechas
    start_date = pub.fecha_inicio
    end_date = pub.fecha_fin
    
    # Si no hay fecha de fin, usar la misma fecha de inicio + 1 día
    if start_date and not end_date:
        end_date = start_date + timedelta(days=1)
    
    # Formato de fechas para Google Calendar: YYYYMMDDTHHMMSS (sin Z para usar hora local)
    start_str = ""
    end_str = ""
    
    if start_date:
        start_str = start_date.strftime("%Y%m%d")
        # Usar siempre 00:00 (todo el día) - sin Z para evitar conversión UTC
        start_str += "T000000"
    
    if end_date:
        end_str = end_date.strftime("%Y%m%d")
        # Usar 00:00 del día siguiente por defecto - sin Z para evitar conversión UTC
        end_str += "T000000"
    
    # Descripción
    description_parts = []
    description_parts.append(f"Nombre del Lugar: {pub.nombre}")
    if pub.tipo_evento:
        description_parts.append(f"Actividad: {pub.tipo_evento}")
    if pub.lugar:
        description_parts.append(f"Lugar: {pub.lugar}")
    if pub.punto_salida:
        description_parts.append(f"Lugar de Salida: {pub.punto_salida}")
    if pub.hora_encuentro:
        description_parts.append(f"Hora de Salida: {pub.hora_encuentro}")
    if pub.fecha_inicio:
        fecha_str = pub.fecha_inicio.strftime('%d/%m/%Y')
        if pub.fecha_fin:
            fecha_str += f" al {pub.fecha_fin.strftime('%d/%m/%Y')}"
        description_parts.append(f"Fecha de Actividad: {fecha_str}")
    if pub.descripcion:
        description_parts.append(f"Descripción: {pub.descripcion}")
    if pub.recomendaciones:
        description_parts.append(f"Recomendaciones: {pub.recomendaciones}")
    if pub.desc_caminata:
        description_parts.append(f"Detalles de la caminata: {pub.desc_caminata}")
    if pub.telefono:
        description_parts.append(f"Teléfono: {pub.telefono}")
    if pub.whatsapp:
        description_parts.append(f"WhatsApp: {pub.whatsapp}")
    if pub.direccion:
        description_parts.append(f"Dirección: {pub.direccion}")
    
    description = "\n\n".join(description_parts)
    
    # Ubicación
    location = pub.lugar or pub.punto_salida or pub.direccion or ""
    
    # Construir URL de Google Calendar
    base_url = "https://www.google.com/calendar/render"
    params = {
        "action": "TEMPLATE",
        "text": quote(title),
        "dates": f"{start_str}/{end_str}" if start_str and end_str else "",
        "details": quote(description),
        "location": quote(location),
        "rem": "popup:P7D,popup:P2D",  # Recordatorios: 1 semana y 2 días antes
        "ctz": "America/Costa_Rica"  # Zona horaria de Costa Rica
    }
    
    # Filtrar parámetros vacíos
    params = {k: v for k, v in params.items() if v}
    
    url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    return url
