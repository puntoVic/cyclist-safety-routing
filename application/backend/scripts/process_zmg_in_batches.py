import pickle
import osmnx as ox
from pathlib import Path

def process_zmg_in_batches():
    """
    Procesar ZMG en lotes para evitar problemas de memoria
    """
    print("Procesando ZMG en lotes...")
    
    # Cargar grafo completo
    graph_file = "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/zmg_complete_network.pkl"
    
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
    
    output_dir = Path("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/zmg_subgraphs")
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
