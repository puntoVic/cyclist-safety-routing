import pickle
import networkx as nx

def calculate_basic_risk_score(edge_data):
    """
    Calcular score de riesgo básico para una arista
    """
    risk_score = 0.0
    
    # Factor 1: Velocidad máxima
    maxspeed = edge_data.get('maxspeed', 50)
    if isinstance(maxspeed, list):
        maxspeed = maxspeed[0]
    try:
        speed = int(maxspeed) if isinstance(maxspeed, (int, str)) else 50
        if speed <= 40:
            risk_score += 0.1
        elif speed <= 60:
            risk_score += 0.4
        elif speed <= 80:
            risk_score += 0.7
        else:
            risk_score += 1.0
    except:
        risk_score += 0.5
    
    # Factor 2: Tipo de vía
    highway = edge_data.get('highway', 'residential')
    if isinstance(highway, list):
        highway = highway[0]
    
    road_risk = {
        'residential': 0.2,
        'tertiary': 0.3,
        'secondary': 0.5,
        'primary': 0.7,
        'trunk': 0.9,
        'motorway': 1.0
    }
    risk_score += road_risk.get(highway, 0.5)
    
    # Factor 3: Infraestructura ciclista
    cycleway = edge_data.get('cycleway', None)
    if cycleway:
        risk_score *= 0.5  # 50% reducción con ciclovía
    
    # Normalizar a 0-1
    return min(risk_score / 2.0, 1.0)

def test_risk_calculation(graph_file):
    """
    Test: Calcular scores de riesgo para todas las aristas
    """
    print("=" * 60)
    print("TEST: Cálculo de Scores de Riesgo")
    print("=" * 60)
    
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    
    print(f"\nCalculando riesgo para {len(G.edges)} aristas...")
    
    risk_scores = []
    for u, v, key, data in G.edges(keys=True, data=True):
        risk = calculate_basic_risk_score(data)
        G[u][v][key]['risk_score'] = risk
        risk_scores.append(risk)
    
    import numpy as np
    risk_scores = np.array(risk_scores)
    
    print(f"\n✓ Cálculo completado")
    print(f"\nEstadísticas de riesgo:")
    print(f"  Promedio: {risk_scores.mean():.3f}")
    print(f"  Mediana: {np.median(risk_scores):.3f}")
    print(f"  Mínimo: {risk_scores.min():.3f}")
    print(f"  Máximo: {risk_scores.max():.3f}")
    print(f"  Desv. Est.: {risk_scores.std():.3f}")
    
    # Distribución de riesgo
    print(f"\nDistribución de riesgo:")
    print(f"  Bajo (0.0-0.3): {(risk_scores < 0.3).sum()} aristas ({(risk_scores < 0.3).sum() / len(risk_scores) * 100:.1f}%)")
    print(f"  Medio (0.3-0.6): {((risk_scores >= 0.3) & (risk_scores < 0.6)).sum()} aristas ({((risk_scores >= 0.3) & (risk_scores < 0.6)).sum() / len(risk_scores) * 100:.1f}%)")
    print(f"  Alto (0.6-1.0): {(risk_scores >= 0.6).sum()} aristas ({(risk_scores >= 0.6).sum() / len(risk_scores) * 100:.1f}%)")
    
    # Guardar grafo con riesgos
    output_file = graph_file.replace('.pkl', '_with_risks.pkl')
    with open(output_file, 'wb') as f:
        pickle.dump(G, f)
    
    print(f"\n✓ Grafo con riesgos guardado en: {output_file}")
    
    return G

if __name__ == "__main__":
    import glob
    import os
    
    files = glob.glob("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/test_guadalajara_*.pkl")
    files = [f for f in files if 'with_risks' not in f]
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"Procesando: {latest_file}\n")
        test_risk_calculation(latest_file)
    else:
        print("No se encontraron archivos de prueba.")
