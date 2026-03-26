import pickle
import networkx as nx
import osmnx as ox

def test_simple_routing(graph_file):
    """
    Test: Calcular ruta entre dos puntos en Guadalajara
    """
    print("=" * 60)
    print("TEST: Enrutamiento Simple")
    print("=" * 60)
    
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    
    # Puntos de prueba en el centro de Guadalajara
    # Origen: Catedral de Guadalajara
    origin = (20.6767, -103.3475)
    # Destino: Teatro Degollado
    destination = (20.6765, -103.3430)
    
    print(f"\nOrigen: {origin} (Catedral)")
    print(f"Destino: {destination} (Teatro Degollado)")
    
    # Encontrar nodos más cercanos
    orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
    dest_node = ox.distance.nearest_nodes(G, destination[1], destination[0])
    
    print(f"\nNodo origen: {orig_node}")
    print(f"Nodo destino: {dest_node}")
    
    # Calcular ruta más corta
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        
        print(f"\n✓ Ruta encontrada")
        print(f"  Número de segmentos: {len(route) - 1}")
        
        # Calcular estadísticas
        total_distance = 0
        total_risk = 0
        
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            edge_data = G[u][v][0]
            total_distance += edge_data.get('length', 0)
            total_risk += edge_data.get('risk_score', 0.5)
        
        avg_risk = total_risk / (len(route) - 1) if len(route) > 1 else 0
        
        print(f"  Distancia total: {total_distance:.0f} metros")
        print(f"  Riesgo promedio: {avg_risk:.3f}")
        
        # Visualizar ruta
        print("\nGenerando visualización de ruta...")
        fig, ax = ox.plot_graph_route(G, route, route_linewidth=3, 
                                       node_size=0, figsize=(10, 10),
                                       show=False, close=False)
        fig.savefig("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_route_visualization.png", dpi=150)
        print("✓ Visualización guardada")
        
        return route
        
    except nx.NetworkXNoPath:
        print("\n✗ No se encontró ruta entre los puntos")
        return None

if __name__ == "__main__":
    import glob
    import os
    
    files = glob.glob("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_*_with_risks.pkl")
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"Usando: {latest_file}\n")
        test_simple_routing(latest_file)
    else:
        print("No se encontró grafo con riesgos. Ejecuta test_risk_calculation.py primero.")
