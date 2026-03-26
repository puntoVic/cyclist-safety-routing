import pickle
import networkx as nx
import osmnx as ox

# Rutas de prueba en Guadalajara
TEST_ROUTES = {
    'centro_corta': {
        'name': 'Catedral a Hospicio Cabañas',
        'origin': (20.6767, -103.3475),
        'destination': (20.6745, -103.3370),
        'expected_distance_km': 0.8,
        'description': 'Ruta corta en el centro histórico'
    },
    'centro_zapopan': {
        'name': 'Centro a Zapopan Centro',
        'origin': (20.6767, -103.3475),
        'destination': (20.7206, -103.3897),
        'expected_distance_km': 8.5,
        'description': 'Ruta larga atravesando Av. Vallarta'
    },
    'minerva_circuit': {
        'name': 'Circuito Minerva',
        'origin': (20.6738, -103.3925),
        'destination': (20.6738, -103.3925),
        'expected_distance_km': 5.0,
        'description': 'Ruta circular alrededor de la Minerva'
    }
}

def test_guadalajara_routes(graph_file):
    """
    Test: Probar rutas específicas de Guadalajara
    """
    print("=" * 60)
    print("TEST: Rutas Reales de Guadalajara")
    print("=" * 60)
    
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    
    results = {}
    
    for route_id, route_info in TEST_ROUTES.items():
        print(f"\n{'=' * 60}")
        print(f"Probando: {route_info['name']}")
        print(f"Descripción: {route_info['description']}")
        print(f"{'=' * 60}")
        
        origin = route_info['origin']
        destination = route_info['destination']
        
        try:
            orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
            dest_node = ox.distance.nearest_nodes(G, destination[1], destination[0])
            
            # Calcular ruta
            route = nx.shortest_path(G, orig_node, dest_node, weight='length')
            
            # Estadísticas
            total_distance = sum(G[route[i]][route[i+1]][0].get('length', 0) 
                               for i in range(len(route) - 1))
            avg_risk = sum(G[route[i]][route[i+1]][0].get('risk_score', 0.5) 
                          for i in range(len(route) - 1)) / (len(route) - 1)
            
            print(f"\n✓ Ruta calculada exitosamente")
            print(f"  Distancia: {total_distance/1000:.2f} km")
            print(f"  Distancia esperada: {route_info['expected_distance_km']} km")
            print(f"  Riesgo promedio: {avg_risk:.3f}")
            print(f"  Segmentos: {len(route) - 1}")
            
            results[route_id] = {
                'success': True,
                'distance_km': total_distance / 1000,
                'risk': avg_risk,
                'segments': len(route) - 1
            }
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            results[route_id] = {'success': False, 'error': str(e)}
    
    # Resumen
    print(f"\n{'=' * 60}")
    print("RESUMEN DE PRUEBAS")
    print(f"{'=' * 60}")
    successful = sum(1 for r in results.values() if r.get('success', False))
    print(f"Rutas exitosas: {successful}/{len(TEST_ROUTES)}")
    
    return results

if __name__ == "__main__":
    import glob
    import os
    
    files = glob.glob("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_*_with_risks.pkl")
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        test_guadalajara_routes(latest_file)
    else:
        print("No se encontró grafo con riesgos.")
