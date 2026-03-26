import pickle
import networkx as nx
import osmnx as ox

def test_route_comparison(graph_file):
    """
    Test: Comparar ruta más segura vs ruta más rápida
    """
    print("=" * 60)
    print("TEST: Comparación de Rutas")
    print("=" * 60)
    
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    
    # Puntos de prueba
    origin = (20.6767, -103.3475)  # Catedral
    destination = (20.6800, -103.3400)  # Punto más lejano
    
    orig_node = ox.distance.nearest_nodes(G, origin[1], origin[0])
    dest_node = ox.distance.nearest_nodes(G, destination[1], destination[0])
    
    print(f"\nCalculando rutas entre:")
    print(f"  Origen: {origin}")
    print(f"  Destino: {destination}")
    
    # Ruta 1: Más rápida (menor distancia)
    try:
        route_fast = nx.shortest_path(G, orig_node, dest_node, weight='length')
        
        dist_fast = sum(G[route_fast[i]][route_fast[i+1]][0].get('length', 0) 
                       for i in range(len(route_fast) - 1))
        risk_fast = sum(G[route_fast[i]][route_fast[i+1]][0].get('risk_score', 0.5) 
                       for i in range(len(route_fast) - 1)) / (len(route_fast) - 1)
        
        print(f"\n1. Ruta Más Rápida:")
        print(f"   Distancia: {dist_fast:.0f} m")
        print(f"   Riesgo promedio: {risk_fast:.3f}")
        print(f"   Segmentos: {len(route_fast) - 1}")
        
    except:
        print("\n✗ No se pudo calcular ruta rápida")
        route_fast = None
    
    # Ruta 2: Más segura (menor riesgo)
    # Actualizar pesos basados en riesgo
    for u, v, key, data in G.edges(keys=True, data=True):
        risk = data.get('risk_score', 0.5)
        length = data.get('length', 0)
        # Peso combinado: 70% riesgo, 30% distancia
        data['safe_weight'] = (0.7 * risk * length) + (0.3 * length)
    
    try:
        route_safe = nx.shortest_path(G, orig_node, dest_node, weight='safe_weight')
        
        dist_safe = sum(G[route_safe[i]][route_safe[i+1]][0].get('length', 0) 
                       for i in range(len(route_safe) - 1))
        risk_safe = sum(G[route_safe[i]][route_safe[i+1]][0].get('risk_score', 0.5) 
                       for i in range(len(route_safe) - 1)) / (len(route_safe) - 1)
        
        print(f"\n2. Ruta Más Segura:")
        print(f"   Distancia: {dist_safe:.0f} m")
        print(f"   Riesgo promedio: {risk_safe:.3f}")
        print(f"   Segmentos: {len(route_safe) - 1}")
        
    except:
        print("\n✗ No se pudo calcular ruta segura")
        route_safe = None
    
    # Comparación
    if route_fast and route_safe:
        print(f"\n" + "=" * 60)
        print("COMPARACIÓN:")
        print(f"  Diferencia en distancia: {abs(dist_safe - dist_fast):.0f} m ({abs(dist_safe - dist_fast) / dist_fast * 100:.1f}%)")
        print(f"  Reducción de riesgo: {(risk_fast - risk_safe) / risk_fast * 100:.1f}%")
        print("=" * 60)
    
    return route_fast, route_safe

if __name__ == "__main__":
    import glob
    import os
    
    files = glob.glob("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_*_with_risks.pkl")
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        test_route_comparison(latest_file)
    else:
        print("No se encontró grafo con riesgos.")
