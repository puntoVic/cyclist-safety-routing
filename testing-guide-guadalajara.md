# Guía de Pruebas - Sistema de Rutas Seguras para Ciclistas en Guadalajara

## Objetivo
Esta guía te ayudará a probar cada componente del sistema usando datos reales de Guadalajara, Jalisco.

---

## Fase 1: Pruebas de Recolección de Datos

### Test 1.1: Verificar Instalación de Dependencias

```bash
# Activar entorno virtual
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install osmnx networkx geopandas pandas numpy matplotlib

# Verificar instalación
python -c "import osmnx as ox; print(f'OSMnx version: {ox.__version__}')"
python -c "import networkx as nx; print(f'NetworkX version: {nx.__version__}')"
```

**Resultado Esperado:**
```
OSMnx version: 1.6.0
NetworkX version: 3.1
```

### Test 1.2: Descargar Red Vial de Guadalajara

Crea el archivo `backend/scripts/test_guadalajara_download.py`:

```python
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
    north, south = 20.6850, 20.6650
    east, west = -103.3350, -103.3550
    
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
        output_file = f"../data/raw/test_guadalajara_{timestamp}.pkl"
        
        with open(output_file, 'wb') as f:
            pickle.dump(G, f)
        
        print(f"\n✓ Red guardada en: {output_file}")
        
        # Visualizar (opcional)
        print("\nGenerando visualización...")
        fig, ax = ox.plot_graph(G, node_size=0, edge_linewidth=0.5, 
                                figsize=(10, 10), show=False, close=False)
        fig.savefig(f"../data/raw/test_guadalajara_map_{timestamp}.png", dpi=150)
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
```

**Ejecutar:**
```bash
cd backend/scripts
python test_guadalajara_download.py
```

**Resultado Esperado:**
- Archivo `.pkl` en `backend/data/raw/`
- Imagen del mapa en `backend/data/raw/`
- Aproximadamente 500-1000 nodos y 1000-2000 aristas

### Test 1.3: Verificar Calidad de Datos OSM

```python
# backend/scripts/test_osm_data_quality.py
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
    
    files = glob.glob("../data/raw/test_guadalajara_*.pkl")
    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"Analizando: {latest_file}\n")
        test_osm_data_quality(latest_file)
    else:
        print("No se encontraron archivos de prueba. Ejecuta test_guadalajara_download.py primero.")
```

---

## Fase 2: Pruebas de Procesamiento de Datos

### Test 2.1: Construir Grafo con Atributos de Riesgo

```python
# backend/scripts/test_risk_calculation.py
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
    
    files = glob.glob("../data/raw/test_guadalajara_*.pkl")
    files = [f for f in files if 'with_risks' not in f]
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"Procesando: {latest_file}\n")
        test_risk_calculation(latest_file)
    else:
        print("No se encontraron archivos de prueba.")
```

---

## Fase 3: Pruebas de Enrutamiento

### Test 3.1: Calcular Ruta Simple

```python
# backend/scripts/test_routing.py
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
        fig.savefig("../data/raw/test_route_visualization.png", dpi=150)
        print("✓ Visualización guardada")
        
        return route
        
    except nx.NetworkXNoPath:
        print("\n✗ No se encontró ruta entre los puntos")
        return None

if __name__ == "__main__":
    import glob
    import os
    
    files = glob.glob("../data/raw/test_guadalajara_*_with_risks.pkl")
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        print(f"Usando: {latest_file}\n")
        test_simple_routing(latest_file)
    else:
        print("No se encontró grafo con riesgos. Ejecuta test_risk_calculation.py primero.")
```

### Test 3.2: Comparar Rutas (Segura vs Rápida)

```python
# backend/scripts/test_route_comparison.py
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
    
    files = glob.glob("../data/raw/test_guadalajara_*_with_risks.pkl")
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        test_route_comparison(latest_file)
    else:
        print("No se encontró grafo con riesgos.")
```

---

## Fase 4: Pruebas de Rutas Reales en Guadalajara

### Test 4.1: Rutas de Prueba Específicas

```python
# backend/scripts/test_guadalajara_routes.py
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
    
    files = glob.glob("../data/raw/test_guadalajara_*_with_risks.pkl")
    
    if files:
        latest_file = max(files, key=os.path.getctime)
        test_guadalajara_routes(latest_file)
    else:
        print("No se encontró grafo con riesgos.")
```

---

## Resumen de Comandos de Prueba

### Secuencia Completa de Pruebas

```bash
# 1. Preparar entorno
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Crear carpetas necesarias
mkdir -p data/raw data/processed

# 3. Ejecutar pruebas en orden
cd scripts

# Test 1: Descargar datos
python test_guadalajara_download.py

# Test 2: Verificar calidad
python test_osm_data_quality.py

# Test 3: Calcular riesgos
python test_risk_calculation.py

# Test 4: Enrutamiento simple
python test_routing.py

# Test 5: Comparar rutas
python test_route_comparison.py

# Test 6: Rutas reales de Guadalajara
python test_guadalajara_routes.py
```

---

## Criterios de Éxito

### ✅ Test Exitoso Si:

1. **Descarga de Datos:**
   - Se descarga red con >500 nodos
   - Se genera visualización del mapa
   - Archivo .pkl se guarda correctamente

2. **Calidad de Datos:**
   - >90% de aristas tienen longitud
   - >80% tienen tipo de vía
   - Se identifican vías principales de Guadalajara

3. **Cálculo de Riesgo:**
   - Todos los segmentos tienen score de riesgo
   - Distribución de riesgo es razonable (no todo alto o bajo)
   - Promedio de riesgo entre 0.3-0.6

4. **Enrutamiento:**
   - Se encuentra ruta entre puntos
   - Distancia calculada es razonable
   - Visualización se genera correctamente

5. **Comparación de Rutas:**
   - Ruta segura tiene menor riesgo que ruta rápida
   - Diferencia en distancia <30%
   - Reducción de riesgo >10%

---

## Solución de Problemas Comunes

### Problema 1: Error al descargar datos de OSM
**Solución:**
```python
# Usar área más pequeña
north, south = 20.6800, 20.6700
east, west = -103.3400, -103.3500
```

### Problema 2: No se encuentra ruta
**Solución:**
- Verificar que los puntos estén dentro del área descargada
- Usar puntos más cercanos
- Verificar conectividad del grafo

### Problema 3: Memoria insuficiente
**Solución:**
- Reducir área de descarga
- Usar `simplify=True` en OSMnx
- Procesar por zonas

---

## Próximos Pasos

Después de completar estas pruebas exitosamente:

1. ✅ Expandir área de cobertura a toda la ZMG
2. ✅ Integrar datos de accidentes de INEGI
3. ✅ Implementar modelo de ML
4. ✅ Desarrollar API REST
5. ✅ Crear interfaz web

---

## Contacto y Soporte

Si encuentras problemas durante las pruebas:
- Revisa los logs de error
- Verifica versiones de dependencias
- Consulta documentación de OSMnx
- Contacta a comunidades de ciclistas locales para validación