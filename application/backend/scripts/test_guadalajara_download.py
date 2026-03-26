import osmnx as ox
import pickle
from datetime import datetime

def test_guadalajara_download():
    """
    Test: Descargar red vial de una zona pequeña de Guadalajara
    """
    print("=" * 60)
    print("TEST: Descarga de Red Vial de Guadalajara")
    print("=" * 60)
    
    # Usar bounding box pequeño para prueba rápida
    # Área: Centro de Guadalajara (aprox 2km x 2km)
    north, south = 20.8000, 20.5500
    east, west = -103.2000, -103.5500
    
    print(f"\nDescargando red para área:")
    print(f"  Norte: {north}, Sur: {south}")
    print(f"  Este: {east}, Oeste: {west}")
    
    try:
        # Descargar red para bicicletas
        G = ox.graph_from_bbox(
            north, south, east, west,
            network_type='bike',
            simplify=True
        )
        
        print(f"\n✓ Red descargada exitosamente")
        print(f"  Nodos: {len(G.nodes):,}")
        print(f"  Aristas: {len(G.edges):,}")
        
        # Agregar atributos
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        
        # Guardar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_{timestamp}.pkl"
        
        with open(output_file, 'wb') as f:
            pickle.dump(G, f)
        
        print(f"\n✓ Red guardada en: {output_file}")
        
        # Visualizar (opcional)
        print("\nGenerando visualización...")
        fig, ax = ox.plot_graph(G, node_size=0, edge_linewidth=0.5, 
                                figsize=(10, 10), show=False, close=False)
        fig.savefig(f"C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_map_{timestamp}.png", dpi=150)
        print(f"✓ Mapa guardado como imagen")
        
        return G
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None

if __name__ == "__main__":
    G = test_guadalajara_download()
    
    if G:
        print("\n" + "=" * 60)
        print("TEST EXITOSO")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("TEST FALLIDO")
        print("=" * 60)
