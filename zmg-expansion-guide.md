# Guía de Expansión a Toda la ZMG
## De Centro de Guadalajara a Zona Metropolitana Completa

---

## Cambios Necesarios

### 1. Coordenadas del Bounding Box

**Cambio en:** `backend/scripts/fetch_guadalajara_data.py`

```python
# ANTES (Solo Centro de Guadalajara - ~4 km²)
north, south = 20.6850, 20.6650
east, west = -103.3350, -103.3550

# DESPUÉS (Toda la ZMG - ~2,734 km²)
north, south = 20.8000, 20.5500
east, west = -103.2000, -103.5500
```

**Coordenadas de la ZMG Completa:**
```python
ZMG_BOUNDS = {
    'north': 20.8000,   # Límite norte (Zapopan Norte)
    'south': 20.5500,   # Límite sur (Tlajomulco)
    'east': -103.2000,  # Límite este (Tonalá)
    'west': -103.5500   # Límite oeste (Zapopan Oeste)
}
```

### 2. Municipios a Incluir

**Cambio en:** `backend/scripts/process_inegi_accidents.py`

```python
# ANTES (Solo 4 municipios principales)
gdl_municipalities = {
    39: 'Guadalajara',
    120: 'Zapopan',
    97: 'Tlaquepaque',
    101: 'Tonalá'
}

# DESPUÉS (Todos los municipios de la ZMG)
ZMG_MUNICIPALITIES = {
    39: 'Guadalajara',
    120: 'Zapopan',
    97: 'Tlaquepaque',
    101: 'Tonalá',
    70: 'El Salto',
    98: 'Tlajomulco de Zúñiga',
    51: 'Ixtlahuacán de los Membrillos',
    65: 'Juanacatlán'
}
```

---

## Script Actualizado para ZMG Completa

### Archivo: `backend/scripts/fetch_zmg_complete_data.py`

```python
import osmnx as ox
import pickle
from datetime import datetime
import time

# Configuración de la ZMG completa
ZMG_CONFIG = {
    'name': 'Zona Metropolitana de Guadalajara',
    'bounds': {
        'north': 20.8000,
        'south': 20.5500,
        'east': -103.2000,
        'west': -103.5500
    },
    'municipalities': [
        'Guadalajara, Jalisco, México',
        'Zapopan, Jalisco, México',
        'Tlaquepaque, Jalisco, México',
        'Tonalá, Jalisco, México',
        'El Salto, Jalisco, México',
        'Tlajomulco de Zúñiga, Jalisco, México'
    ]
}

def fetch_zmg_by_bbox():
    """
    Método 1: Descargar toda la ZMG usando bounding box
    Más rápido pero incluye áreas fuera de municipios
    """
    print("=" * 60)
    print("DESCARGA DE RED VIAL - ZMG COMPLETA (BBOX)")
    print("=" * 60)
    
    bounds = ZMG_CONFIG['bounds']
    
    print(f"\nÁrea de cobertura:")
    print(f"  Norte: {bounds['north']}")
    print(f"  Sur: {bounds['south']}")
    print(f"  Este: {bounds['east']}")
    print(f"  Oeste: {bounds['west']}")
    
    # Calcular área aproximada
    lat_diff = bounds['north'] - bounds['south']
    lon_diff = bounds['east'] - bounds['west']
    area_km2 = abs(lat_diff * lon_diff) * 111 * 111  # Aproximación
    print(f"  Área aproximada: {area_km2:.0f} km²")
    
    try:
        print("\nDescargando red vial...")
        print("⚠ ADVERTENCIA: Esto puede tomar 5-15 minutos")
        
        start_time = time.time()
        
        G = ox.graph_from_bbox(
            bounds['north'],
            bounds['south'],
            bounds['east'],
            bounds['west'],
            network_type='bike',
            simplify=True,
            retain_all=False
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Red descargada en {elapsed/60:.1f} minutos")
        print(f"  Nodos: {len(G.nodes):,}")
        print(f"  Aristas: {len(G.edges):,}")
        
        # Agregar atributos
        print("\nAgregando atributos...")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        
        # Guardar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/raw/zmg_complete_network_{timestamp}.pkl"
        
        with open(output_file, 'wb') as f:
            pickle.dump(G, f)
        
        print(f"\n✓ Red guardada: {output_file}")
        
        # Estadísticas
        print("\nEstadísticas de la red:")
        print(f"  Densidad de nodos: {len(G.nodes)/area_km2:.1f} nodos/km²")
        print(f"  Densidad de aristas: {len(G.edges)/area_km2:.1f} aristas/km²")
        
        return G
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nSugerencias:")
        print("  1. Reduce el área (divide en zonas)")
        print("  2. Usa network_type='drive' en lugar de 'bike'")
        print("  3. Aumenta el timeout de OSMnx")
        return None

def fetch_zmg_by_municipalities():
    """
    Método 2: Descargar por municipios individuales y combinar
    Más lento pero más preciso
    """
    print("=" * 60)
    print("DESCARGA DE RED VIAL - ZMG POR MUNICIPIOS")
    print("=" * 60)
    
    graphs = []
    
    for i, municipality in enumerate(ZMG_CONFIG['municipalities'], 1):
        print(f"\n[{i}/{len(ZMG_CONFIG['municipalities'])}] Descargando {municipality}...")
        
        try:
            G = ox.graph_from_place(
                municipality,
                network_type='bike',
                simplify=True
            )
            
            print(f"  ✓ Nodos: {len(G.nodes):,}, Aristas: {len(G.edges):,}")
            graphs.append(G)
            
            # Pausa para no sobrecargar el servidor
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    if not graphs:
        print("\n✗ No se pudo descargar ningún municipio")
        return None
    
    # Combinar grafos
    print(f"\nCombinando {len(graphs)} grafos...")
    G_combined = graphs[0]
    
    for G in graphs[1:]:
        G_combined = ox.utils_graph.graph_from_gdfs(
            ox.graph_to_gdfs(G_combined, nodes=True, edges=True)[0].append(
                ox.graph_to_gdfs(G, nodes=True, edges=True)[0]
            ),
            ox.graph_to_gdfs(G_combined, nodes=True, edges=True)[1].append(
                ox.graph_to_gdfs(G, nodes=True, edges=True)[1]
            )
        )
    
    print(f"✓ Grafo combinado:")
    print(f"  Nodos: {len(G_combined.nodes):,}")
    print(f"  Aristas: {len(G_combined.edges):,}")
    
    # Guardar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../data/raw/zmg_complete_network_{timestamp}.pkl"
    
    with open(output_file, 'wb') as f:
        pickle.dump(G_combined, f)
    
    print(f"\n✓ Red guardada: {output_file}")
    
    return G_combined

def fetch_zmg_by_zones():
    """
    Método 3: Dividir en zonas más pequeñas
    Más confiable para áreas grandes
    """
    print("=" * 60)
    print("DESCARGA DE RED VIAL - ZMG POR ZONAS")
    print("=" * 60)
    
    # Dividir ZMG en 4 zonas
    bounds = ZMG_CONFIG['bounds']
    mid_lat = (bounds['north'] + bounds['south']) / 2
    mid_lon = (bounds['east'] + bounds['west']) / 2
    
    zones = {
        'noroeste': {
            'north': bounds['north'],
            'south': mid_lat,
            'east': mid_lon,
            'west': bounds['west']
        },
        'noreste': {
            'north': bounds['north'],
            'south': mid_lat,
            'east': bounds['east'],
            'west': mid_lon
        },
        'suroeste': {
            'north': mid_lat,
            'south': bounds['south'],
            'east': mid_lon,
            'west': bounds['west']
        },
        'sureste': {
            'north': mid_lat,
            'south': bounds['south'],
            'east': bounds['east'],
            'west': mid_lon
        }
    }
    
    graphs = []
    
    for zone_name, zone_bounds in zones.items():
        print(f"\nDescargando zona {zone_name}...")
        
        try:
            G = ox.graph_from_bbox(
                zone_bounds['north'],
                zone_bounds['south'],
                zone_bounds['east'],
                zone_bounds['west'],
                network_type='bike',
                simplify=True
            )
            
            print(f"  ✓ Nodos: {len(G.nodes):,}, Aristas: {len(G.edges):,}")
            graphs.append(G)
            
            # Guardar zona individual
            zone_file = f"../data/raw/zmg_zone_{zone_name}.pkl"
            with open(zone_file, 'wb') as f:
                pickle.dump(G, f)
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    if not graphs:
        print("\n✗ No se pudo descargar ninguna zona")
        return None
    
    print(f"\n✓ {len(graphs)} zonas descargadas exitosamente")
    
    return graphs

def main():
    """
    Ejecutar descarga de ZMG completa
    """
    print("\n" + "=" * 60)
    print("DESCARGA DE RED VIAL - ZONA METROPOLITANA DE GUADALAJARA")
    print("=" * 60)
    
    print("\nMétodos disponibles:")
    print("  1. Bounding Box completo (rápido, ~10 min)")
    print("  2. Por municipios (lento, ~20 min, más preciso)")
    print("  3. Por zonas (confiable, ~15 min)")
    
    method = input("\nSelecciona método (1/2/3) [1]: ").strip() or "1"
    
    if method == "1":
        G = fetch_zmg_by_bbox()
    elif method == "2":
        G = fetch_zmg_by_municipalities()
    elif method == "3":
        graphs = fetch_zmg_by_zones()
        G = graphs[0] if graphs else None
    else:
        print("Método inválido")
        return
    
    if G:
        print("\n" + "=" * 60)
        print("DESCARGA COMPLETADA EXITOSAMENTE")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("DESCARGA FALLIDA")
        print("=" * 60)

if __name__ == "__main__":
    main()
```

---

## Consideraciones de Rendimiento

### 1. Tamaño de Datos

**Centro de Guadalajara (4 km²):**
- Nodos: ~500-1,000
- Aristas: ~1,000-2,000
- Tamaño archivo: ~5 MB
- Tiempo descarga: 30 segundos

**ZMG Completa (2,734 km²):**
- Nodos: ~300,000-500,000
- Aristas: ~600,000-1,000,000
- Tamaño archivo: ~500 MB - 1 GB
- Tiempo descarga: 10-20 minutos

### 2. Optimizaciones Necesarias

**Archivo:** `backend/app/config/performance_config.py`

```python
# Configuración de rendimiento para ZMG completa

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
```

### 3. Procesamiento por Lotes

**Archivo:** `backend/scripts/process_zmg_in_batches.py`

```python
import pickle
import osmnx as ox
from pathlib import Path

def process_zmg_in_batches():
    """
    Procesar ZMG en lotes para evitar problemas de memoria
    """
    print("Procesando ZMG en lotes...")
    
    # Cargar grafo completo
    graph_file = "../data/raw/zmg_complete_network.pkl"
    
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    
    print(f"Grafo cargado: {len(G.nodes):,} nodos")
    
    # Dividir en subgrafos por área
    bounds = {
        'north': 20.8000,
        'south': 20.5500,
        'east': -103.2000,
        'west': -103.5500
    }
    
    # Crear grid de 5x5 (25 subáreas)
    n_divisions = 5
    lat_step = (bounds['north'] - bounds['south']) / n_divisions
    lon_step = (bounds['east'] - bounds['west']) / n_divisions
    
    output_dir = Path("../data/processed/zmg_subgraphs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(n_divisions):
        for j in range(n_divisions):
            # Calcular bounds del subgrafo
            sub_north = bounds['south'] + (i + 1) * lat_step
            sub_south = bounds['south'] + i * lat_step
            sub_east = bounds['west'] + (j + 1) * lon_step
            sub_west = bounds['west'] + j * lon_step
            
            # Extraer subgrafo
            try:
                subgraph = ox.truncate.truncate_graph_bbox(
                    G, sub_north, sub_south, sub_east, sub_west
                )
                
                if len(subgraph.nodes) > 0:
                    # Guardar subgrafo
                    filename = f"subgraph_{i}_{j}.pkl"
                    filepath = output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        pickle.dump(subgraph, f)
                    
                    print(f"✓ Subgrafo {i},{j}: {len(subgraph.nodes)} nodos")
            
            except Exception as e:
                print(f"✗ Error en subgrafo {i},{j}: {e}")
    
    print(f"\n✓ Procesamiento completado")
    print(f"  Subgrafos guardados en: {output_dir}")

if __name__ == "__main__":
    process_zmg_in_batches()
```

---

## Cambios en el Código de Enrutamiento

### Archivo: `backend/app/services/routing_service.py`

```python
import networkx as nx
import osmnx as ox
from pathlib import Path
import pickle

class ZMGRoutingService:
    """
    Servicio de enrutamiento optimizado para ZMG completa
    """
    
    def __init__(self, graph_file=None):
        """
        Cargar grafo con optimizaciones
        """
        if graph_file is None:
            graph_file = "../data/raw/zmg_complete_network.pkl"
        
        print(f"Cargando grafo de ZMG...")
        
        with open(graph_file, 'rb') as f:
            self.G = pickle.load(f)
        
        print(f"✓ Grafo cargado: {len(self.G.nodes):,} nodos")
        
        # Crear índice espacial para búsquedas rápidas
        self._build_spatial_index()
    
    def _build_spatial_index(self):
        """
        Construir índice espacial R-tree
        """
        try:
            from rtree import index
            
            print("Construyendo índice espacial...")
            
            self.spatial_index = index.Index()
            
            for node, data in self.G.nodes(data=True):
                lon, lat = data['x'], data['y']
                self.spatial_index.insert(node, (lon, lat, lon, lat))
            
            print("✓ Índice espacial construido")
            
        except ImportError:
            print("⚠ rtree no disponible, usando búsqueda lineal")
            self.spatial_index = None
    
    def find_nearest_node_fast(self, lat, lon):
        """
        Encontrar nodo más cercano usando índice espacial
        """
        if self.spatial_index:
            # Búsqueda rápida con R-tree
            nearest = list(self.spatial_index.nearest((lon, lat, lon, lat), 1))
            return nearest[0] if nearest else None
        else:
            # Fallback a OSMnx
            return ox.distance.nearest_nodes(self.G, lon, lat)
    
    def calculate_route_zmg(self, origin, destination, alpha=0.5, beta=0.5):
        """
        Calcular ruta en ZMG con optimizaciones
        """
        # Verificar distancia
        from geopy.distance import geodesic
        
        distance_km = geodesic(origin, destination).km
        
        if distance_km > 50:
            return {
                'error': 'Distancia muy larga (>50 km)',
                'suggestion': 'Usa puntos intermedios'
            }
        
        # Encontrar nodos
        orig_node = self.find_nearest_node_fast(*origin)
        dest_node = self.find_nearest_node_fast(*destination)
        
        # Calcular ruta
        try:
            route = nx.shortest_path(
                self.G,
                orig_node,
                dest_node,
                weight='length'
            )
            
            return {
                'route': route,
                'distance_km': distance_km,
                'num_segments': len(route) - 1
            }
            
        except nx.NetworkXNoPath:
            return {'error': 'No se encontró ruta'}
```

---

## Checklist de Expansión a ZMG

- [ ] Actualizar coordenadas de bounding box
- [ ] Incluir todos los municipios de la ZMG
- [ ] Descargar red vial completa (10-20 min)
- [ ] Implementar índice espacial R-tree
- [ ] Optimizar carga de grafo (lazy loading)
- [ ] Procesar en lotes si es necesario
- [ ] Actualizar límites de distancia en routing
- [ ] Probar con rutas largas (>20 km)
- [ ] Validar cobertura en todos los municipios
- [ ] Actualizar visualizaciones para área mayor

---

## Comandos de Ejecución

```bash
# 1. Descargar ZMG completa
cd backend/scripts
python fetch_zmg_complete_data.py

# 2. Procesar en lotes (opcional)
python process_zmg_in_batches.py

# 3. Probar enrutamiento
python test_zmg_routing.py
```

---

## Estimaciones de Recursos

**Requisitos mínimos:**
- RAM: 8 GB
- Disco: 5 GB libres
- CPU: 4 cores
- Tiempo: 30-60 minutos

**Recomendado:**
- RAM: 16 GB
- Disco: 10 GB libres
- CPU: 8 cores
- SSD para mejor rendimiento

---

## Resumen de Cambios

| Aspecto | Centro GDL | ZMG Completa |
|---------|------------|--------------|
| Área | 4 km² | 2,734 km² |
| Nodos | ~1,000 | ~400,000 |
| Aristas | ~2,000 | ~800,000 |
| Municipios | 1 | 6-8 |
| Tiempo descarga | 30 seg | 10-20 min |
| Tamaño archivo | 5 MB | 500 MB - 1 GB |
| RAM necesaria | 2 GB | 8-16 GB |

La expansión a ZMG completa requiere principalmente ajustar coordenadas, optimizar el código para manejar más datos, y usar técnicas de indexación espacial para mantener el rendimiento.