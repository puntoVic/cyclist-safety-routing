import pandas as pd
import geopandas as gpd
import pickle
import numpy as np
from datetime import datetime

class TrainingDataPreparator:
    """
    Prepara datos de entrenamiento para el modelo de predicción de riesgo
    """
    
    def __init__(self, graph_file, accidents_file):
        """
        Args:
            graph_file: Ruta al archivo .pkl del grafo
            accidents_file: Ruta al archivo de accidentes (GeoJSON o CSV)
        """
        with open(graph_file, 'rb') as f:
            self.G = pickle.load(f)
        
        if accidents_file.endswith('.geojson'):
            self.accidents = gpd.read_file(accidents_file)
        else:
            self.accidents = pd.read_csv(accidents_file)
    
    def extract_edge_features(self):
        """
        Extraer características de cada arista del grafo
        """
        print("Extrayendo características de aristas...")
        
        features = []
        
        for u, v, key, data in self.G.edges(keys=True, data=True):
            feature_dict = {
                'edge_id': f"{u}_{v}_{key}",
                'u': u,
                'v': v,
                'key': key
            }
            
            # 1. Características de la vía
            feature_dict['length'] = data.get('length', 0)
            
            # Tipo de vía
            highway = data.get('highway', 'unknown')
            if isinstance(highway, list):
                highway = highway[0]
            feature_dict['highway_type'] = highway
            
            # Velocidad máxima
            maxspeed = data.get('maxspeed', 50)
            if isinstance(maxspeed, list):
                maxspeed = maxspeed[0]
            try:
                feature_dict['speed_limit'] = int(maxspeed)
            except:
                feature_dict['speed_limit'] = 50
            
            # Número de carriles
            lanes = data.get('lanes', 1)
            if isinstance(lanes, list):
                lanes = lanes[0]
            try:
                feature_dict['num_lanes'] = int(lanes)
            except:
                feature_dict['num_lanes'] = 1
            
            # 2. Infraestructura ciclista
            feature_dict['has_cycleway'] = 1 if data.get('cycleway') else 0
            feature_dict['has_bike_lane'] = 1 if 'cycleway' in str(data.get('highway', '')) else 0
            
            # 3. Características del entorno
            feature_dict['is_oneway'] = 1 if data.get('oneway', False) else 0
            feature_dict['has_name'] = 1 if data.get('name') else 0
            
            # 4. Geometría
            if 'geometry' in data:
                coords = list(data['geometry'].coords)
                feature_dict['num_points'] = len(coords)
                
                # Calcular sinuosidad (curvatura)
                if len(coords) > 1:
                    straight_distance = np.sqrt(
                        (coords[-1][0] - coords[0][0])**2 + 
                        (coords[-1][1] - coords[0][1])**2
                    )
                    actual_distance = data.get('length', 0)
                    feature_dict['sinuosity'] = actual_distance / max(straight_distance, 1)
                else:
                    feature_dict['sinuosity'] = 1.0
            else:
                feature_dict['num_points'] = 2
                feature_dict['sinuosity'] = 1.0
            
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        print(f"✓ Extraídas {len(df)} aristas con {len(df.columns)} características")
        
        return df
    
    def add_accident_labels(self, df_features):
        """
        Agregar etiquetas de accidentes a las características
        """
        print("\nAgregando etiquetas de accidentes...")
        
        # Inicializar contadores
        df_features['accident_count'] = 0
        df_features['has_accident'] = 0
        
        # Mapear accidentes a aristas (simplificado)
        # En producción, usar KD-tree para búsqueda espacial eficiente
        for idx, row in df_features.iterrows():
            u, v, key = row['u'], row['v'], row['key']
            if self.G.has_edge(u, v, key):
                edge_data = self.G[u][v][key]
                accident_count = edge_data.get('accident_count', 0)
                df_features.at[idx, 'accident_count'] = accident_count
                df_features.at[idx, 'has_accident'] = 1 if accident_count > 0 else 0
        
        print(f"✓ Aristas con accidentes: {df_features['has_accident'].sum()}")
        print(f"✓ Total de accidentes: {df_features['accident_count'].sum()}")
        
        return df_features
    
    def create_risk_labels(self, df_features):
        """
        Crear etiquetas de riesgo categóricas
        """
        print("\nCreando etiquetas de riesgo...")
        
        # Método 1: Basado en accidentes
        df_features['risk_from_accidents'] = pd.cut(
            df_features['accident_count'],
            bins=[-1, 0, 1, 5, 100],
            labels=['bajo', 'medio', 'alto', 'muy_alto']
        )
        
        # Método 2: Basado en características de la vía
        risk_score = 0
        
        # Factor velocidad
        speed_risk = df_features['speed_limit'].apply(
            lambda x: 0.1 if x <= 40 else (0.4 if x <= 60 else (0.7 if x <= 80 else 1.0))
        )
        
        # Factor tipo de vía
        highway_risk_map = {
            'residential': 0.2,
            'tertiary': 0.3,
            'secondary': 0.5,
            'primary': 0.7,
            'trunk': 0.9,
            'motorway': 1.0
        }
        highway_risk = df_features['highway_type'].map(highway_risk_map).fillna(0.5)
        
        # Factor infraestructura ciclista
        infra_risk = 1.0 - (df_features['has_cycleway'] * 0.5 + df_features['has_bike_lane'] * 0.3)
        
        # Combinar factores
        df_features['calculated_risk_score'] = (
            0.4 * speed_risk + 
            0.4 * highway_risk + 
            0.2 * infra_risk
        )
        
        # Crear etiquetas categóricas
        df_features['risk_category'] = pd.cut(
            df_features['calculated_risk_score'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['bajo', 'medio', 'alto']
        )
        
        print(f"✓ Distribución de riesgo:")
        print(df_features['risk_category'].value_counts())
        
        return df_features
    
    def save_training_data(self, df_features, output_file):
        """
        Guardar dataset de entrenamiento
        """
        df_features.to_csv(output_file, index=False)
        print(f"\n✓ Dataset guardado en: {output_file}")
        
        # Guardar también en formato pickle para preservar tipos
        pickle_file = output_file.replace('.csv', '.pkl')
        df_features.to_pickle(pickle_file)
        print(f"✓ Dataset guardado en: {pickle_file}")
        
        return df_features

def main():
    """
    Ejecutar preparación de datos
    """
    print("=" * 60)
    print("PREPARACIÓN DE DATOS DE ENTRENAMIENTO")
    print("=" * 60)
    
    # Rutas de archivos
    graph_file = "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/guadalajara_network_with_risks.pkl"
    accidents_file = "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/guadalajara_cyclist_accidents.geojson"
    output_file = "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/training_data.csv"
    
    # Crear preparador
    preparator = TrainingDataPreparator(graph_file, accidents_file)
    
    # Extraer características
    df_features = preparator.extract_edge_features()
    
    # Agregar accidentes
    df_features = preparator.add_accident_labels(df_features)
    
    # Crear etiquetas de riesgo
    df_features = preparator.create_risk_labels(df_features)
    
    # Guardar
    preparator.save_training_data(df_features, output_file)
    
    print("\n" + "=" * 60)
    print("PREPARACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
