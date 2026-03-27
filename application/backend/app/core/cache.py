"""
Módulo de cache - implementación in-memory para desarrollo
"""
import json
from typing import Optional, Any

# Cache in-memory simple para desarrollo
_cache = {}

async def init_cache():
    """Inicializar cache"""
    print("[OK] Cache in-memory inicializado")

async def close_cache():
    """Cerrar cache"""
    _cache.clear()
    print("[OK] Cache cerrado")

async def get_cache(key: str) -> Optional[Any]:
    """Obtener valor del cache"""
    return _cache.get(key)

async def set_cache(key: str, value: Any, expire: int = 300):
    """Guardar valor en cache"""
    _cache[key] = value
