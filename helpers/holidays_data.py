# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""Datos estáticos de feriados y utilidades de música (sin DB)."""
from datetime import date, timedelta
import os


def nth_weekday(year, month, weekday, n):
    """Devuelve el n-ésimo día de la semana del mes (n empieza en 1).
    weekday: 0=lunes, 6=domingo
    """
    first = date(year, month, 1)
    delta = (weekday - first.weekday() + 7) % 7
    return first + timedelta(days=delta + (n - 1) * 7)


HOLIDAYS = [
    {
        'id': 'mothers_day',
        'month': 8,
        'day': 15,
        'title': '¡Feliz Día de la Madre!',
        'subtitle': 'A todas las madres de Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '🌹',
        'confetti_colors': ['#ff69b4', '#ffc107', '#ff4081', '#ffd700', '#ffffff'],
        'song': 'DIA DE LA MADRE.mp3',
    },
    {
        'id': 'new_year',
        'month': 1,
        'day': 1,
        'title': '¡Feliz Año Nuevo!',
        'subtitle': 'Te lo desea La Tribu de Los Libres',
        'emoji': '🎉',
        'confetti_colors': ['#ff69b4', '#ffc107', '#00bcd4', '#4caf50', '#ff4081'],
    },
    {
        'id': 'new_years_eve',
        'month': 12,
        'day': 31,
        'title': '¡Feliz Fin de Año!',
        'subtitle': 'Te lo desea La Tribu de Los Libres',
        'emoji': '🥂',
        'confetti_colors': ['#ffd700', '#ffffff', '#ff4081', '#00bcd4', '#4caf50'],
    },
    {
        'id': 'fathers_day',
        'month': 6,
        'nth_weekday': (3, 6),  # tercer domingo de junio
        'title': '¡Feliz Día del Padre!',
        'subtitle': 'A todos los padres de Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '👔',
        'confetti_colors': ['#1e88e5', '#4caf50', '#ffc107', '#8d6e63', '#ffffff'],
        'song': 'PADRES DE LA TRIBU.mp3',
    },
    {
        'id': 'childrens_day',
        'month': 6,
        'day': 1,
        'title': '¡Feliz Día del Niño!',
        'subtitle': 'A todos los niños de Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '🎈',
        'confetti_colors': ['#ff69b4', '#00bcd4', '#ffeb3b', '#4caf50', '#ff9800'],
    },
    {
        'id': 'parks_day',
        'month': 8,
        'day': 24,
        'title': '¡Feliz Día de los Parques Nacionales!',
        'subtitle': 'Celebremos nuestra naturaleza, La Tribu de Los Libres',
        'emoji': '🌲',
        'confetti_colors': ['#2e7d32', '#66bb6a', '#ffffff', '#8d6e63'],
    },
    {
        'id': 'independence',
        'month': 9,
        'day': 15,
        'title': '¡Feliz Día de la Independencia!',
        'subtitle': 'Costa Rica, con cariño de La Tribu de Los Libres',
        'emoji': '🇨🇷',
        'confetti_colors': ['#002b7f', '#ffffff', '#ce1126'],
        'background': 'rgba(0, 43, 127, 0.12)',
        'border': 'rgba(0, 43, 127, 0.4)',
    },
    {
        'id': 'christmas',
        'month': 12,
        'day': 25,
        'title': '¡Feliz Navidad!',
        'subtitle': 'Te lo desea La Tribu de Los Libres',
        'emoji': '🎄',
        'confetti_colors': ['#ff0000', '#00ff00', '#ffffff', '#ffd700'],
    },
]


_DEFAULT_CONFETTI = ['#ff69b4', '#ffc107', '#00bcd4', '#4caf50', '#ff4081']

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_OVERRIDE_FILE = os.path.join(_PROJECT_ROOT, 'data', 'holidays.json')
MUSIC_DIR = os.path.join(_PROJECT_ROOT, 'static', 'musica')


def list_music_files():
    """Retorna la lista de archivos de música disponibles."""
    if not os.path.isdir(MUSIC_DIR):
        return []
    return sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))])
