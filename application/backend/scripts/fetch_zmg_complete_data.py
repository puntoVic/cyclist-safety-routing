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
        output_file = f"C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/zmg_complete_network_{timestamp}.pkl"
         
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
    output_file = f"C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/zmg_complete_network_{timestamp}.pkl"
    
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
            zone_file = f"C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/zmg_zone_{zone_name}.pkl"
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
