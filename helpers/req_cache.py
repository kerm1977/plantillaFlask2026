# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
import time

_cache = {}

def cached(key, ttl, fn):
    """Devuelve el valor cacheado si no pasó el TTL, si no ejecuta fn()."""
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    value = fn()
    _cache[key] = (time.time(), value)
    return value

def invalidate(key):
    _cache.pop(key, None)
