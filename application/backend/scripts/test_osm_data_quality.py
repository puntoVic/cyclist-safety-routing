import pickle
import pandas as pd

def test_osm_data_quality(graph_file):
    """
    Test: Verificar calidad y completitud de datos OSM
    """
    print("=" * 60)
    print("TEST: Calidad de Datos OSM")
    print("=" * 60)
    
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    
    # Analizar atributos de aristas
    edge_data = []
    for u, v, key, data in G.edges(keys=True, data=True):
        edge_data.append({
            'length': data.get('length', None),
            'highway': data.get('highway', None),
            'maxspeed': data.get('maxspeed', None),
            'lanes': data.get('lanes', None),
            'name': data.get('name', None),
            'oneway': data.get('oneway', None)
        })
    
    df = pd.DataFrame(edge_data)
    
    print(f"\nTotal de aristas: {len(df)}")
    print("\nCompletitud de datos:")
    print(f"  Longitud: {(df['length'].notna().sum() / len(df) * 100):.1f}%")
    print(f"  Tipo de vía: {(df['highway'].notna().sum() / len(df) * 100):.1f}%")
    print(f"  Velocidad máxima: {(df['maxspeed'].notna().sum() / len(df) * 100):.1f}%")
    print(f"  Carriles: {(df['lanes'].notna().sum() / len(df) * 100):.1f}%")
    print(f"  Nombre: {(df['name'].notna().sum() / len(df) * 100):.1f}%")
    
    print("\nTipos de vías encontradas:")
    if df['highway'].notna().any():
        highway_counts = df['highway'].value_counts()
        for highway_type, count in highway_counts.head(10).items():
            print(f"  {highway_type}: {count}")
    
    print("\nVías principales identificadas:")
    if df['name'].notna().any():
        named_streets = df[df['name'].notna()]['name'].value_counts()
        for street, count in named_streets.head(10).items():
            print(f"  {street}: {count} segmentos")
    
    return df

if __name__ == "__main__":
    # Usar el archivo más reciente
    import glob
    import os
    
    files = glob.glob("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_*.pkl")
    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"Analizando: {latest_file}\n")
        test_osm_data_quality(latest_file)
    else:
        print("No se encontraron archivos de prueba. Ejecuta test_guadalajara_download.py primero.")
