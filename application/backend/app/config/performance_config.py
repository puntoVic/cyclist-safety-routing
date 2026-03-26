PERFORMANCE_CONFIG = {
    'graph_loading': {
        'use_cache': True,
        'cache_timeout': 3600,  # 1 hora
        'lazy_loading': True
    },
    'routing': {
        'max_distance_km': 50,  # Limitar búsquedas muy largas
        'timeout_seconds': 30,
        'use_bidirectional': True  # Dijkstra bidireccional
    },
    'spatial_index': {
        'use_rtree': True,  # Índice espacial para búsquedas rápidas
        'grid_size': 0.01  # ~1 km
    },
    'memory': {
        'max_graph_size_mb': 2000,
        'use_memory_mapping': True
    }
}