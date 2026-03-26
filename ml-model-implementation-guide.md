# Guía de Implementación del Modelo de Machine Learning
## Sistema de Predicción de Riesgo para Ciclistas - Guadalajara

---

## Índice
1. [Preparación de Datos](#1-preparación-de-datos)
2. [Ingeniería de Features](#2-ingeniería-de-features)
3. [Entrenamiento del Modelo](#3-entrenamiento-del-modelo)
4. [Evaluación y Validación](#4-evaluación-y-validación)
5. [Implementación en Producción](#5-implementación-en-producción)

---

## 1. Preparación de Datos

### 1.1 Crear Dataset de Entrenamiento

**Ubicación:** `backend/scripts/prepare_training_data.py`

```python
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
    graph_file = "../data/raw/guadalajara_network_with_risks.pkl"
    accidents_file = "../data/processed/guadalajara_cyclist_accidents.geojson"
    output_file = "../data/processed/training_data.csv"
    
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
```

---

## 2. Ingeniería de Features

### 2.1 Feature Engineering Avanzado

**Ubicación:** `backend/app/models/feature_engineering.py`

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif

class FeatureEngineer:
    """
    Ingeniería de características para el modelo de riesgo
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
    
    def create_interaction_features(self, df):
        """
        Crear características de interacción
        """
        print("Creando características de interacción...")
        
        # Interacción velocidad x carriles
        df['speed_lanes_interaction'] = df['speed_limit'] * df['num_lanes']
        
        # Interacción velocidad x longitud
        df['speed_length_interaction'] = df['speed_limit'] * df['length'] / 1000
        
        # Densidad de puntos (curvatura relativa)
        df['point_density'] = df['num_points'] / (df['length'] / 100)
        
        # Riesgo compuesto
        df['composite_risk'] = (
            (df['speed_limit'] / 100) * 
            (1 - df['has_cycleway']) * 
            df['num_lanes']
        )
        
        return df
    
    def encode_categorical_features(self, df, fit=True):
        """
        Codificar características categóricas
        """
        print("Codificando características categóricas...")
        
        categorical_cols = ['highway_type']
        
        for col in categorical_cols:
            if col in df.columns:
                if fit:
                    le = LabelEncoder()
                    df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
                    self.label_encoders[col] = le
                else:
                    le = self.label_encoders[col]
                    df[f'{col}_encoded'] = le.transform(df[col].astype(str))
        
        return df
    
    def create_time_features(self, df, datetime_col=None):
        """
        Crear características temporales (si hay datos de tiempo)
        """
        if datetime_col and datetime_col in df.columns:
            df['hour'] = pd.to_datetime(df[datetime_col]).dt.hour
            df['day_of_week'] = pd.to_datetime(df[datetime_col]).dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_rush_hour'] = df['hour'].apply(
                lambda x: 1 if (7 <= x <= 10) or (18 <= x <= 21) else 0
            )
        
        return df
    
    def select_best_features(self, X, y, k=20):
        """
        Seleccionar las k mejores características
        """
        print(f"\nSeleccionando las {k} mejores características...")
        
        selector = SelectKBest(score_func=f_classif, k=k)
        X_selected = selector.fit_transform(X, y)
        
        # Obtener nombres de características seleccionadas
        selected_indices = selector.get_support(indices=True)
        self.feature_names = [X.columns[i] for i in selected_indices]
        
        print(f"✓ Características seleccionadas:")
        for i, (name, score) in enumerate(zip(self.feature_names, selector.scores_[selected_indices])):
            print(f"  {i+1}. {name}: {score:.2f}")
        
        return pd.DataFrame(X_selected, columns=self.feature_names)
    
    def prepare_features(self, df, target_col='risk_category', fit=True):
        """
        Preparar todas las características para el modelo
        """
        print("\n" + "=" * 60)
        print("PREPARACIÓN DE CARACTERÍSTICAS")
        print("=" * 60)
        
        # Crear copias
        df_processed = df.copy()
        
        # 1. Crear características de interacción
        df_processed = self.create_interaction_features(df_processed)
        
        # 2. Codificar categóricas
        df_processed = self.encode_categorical_features(df_processed, fit=fit)
        
        # 3. Seleccionar características numéricas
        numeric_features = [
            'length', 'speed_limit', 'num_lanes', 'has_cycleway',
            'has_bike_lane', 'is_oneway', 'has_name', 'num_points',
            'sinuosity', 'speed_lanes_interaction', 'speed_length_interaction',
            'point_density', 'composite_risk', 'highway_type_encoded'
        ]
        
        # Filtrar características que existen
        numeric_features = [f for f in numeric_features if f in df_processed.columns]
        
        X = df_processed[numeric_features]
        y = df_processed[target_col] if target_col in df_processed.columns else None
        
        # 4. Escalar características
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        X_scaled = pd.DataFrame(X_scaled, columns=numeric_features)
        
        print(f"\n✓ Características preparadas: {X_scaled.shape}")
        
        return X_scaled, y

# Ejemplo de uso
if __name__ == "__main__":
    # Cargar datos
    df = pd.read_pickle("../data/processed/training_data.pkl")
    
    # Crear ingeniero de características
    engineer = FeatureEngineer()
    
    # Preparar características
    X, y = engineer.prepare_features(df, target_col='risk_category')
    
    print(f"\nForma final de X: {X.shape}")
    print(f"Forma final de y: {y.shape}")
```

---

## 3. Entrenamiento del Modelo

### 3.1 Modelo de Random Forest

**Ubicación:** `backend/app/models/risk_classifier.py`

```python
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.metrics import precision_recall_fscore_support
import matplotlib.pyplot as plt
import seaborn as sns

class RiskClassifier:
    """
    Clasificador de riesgo para segmentos de ruta
    """
    
    def __init__(self, model_type='random_forest'):
        """
        Args:
            model_type: 'random_forest' o 'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.feature_importance = None
        self.training_history = {}
    
    def create_model(self, **params):
        """
        Crear modelo de clasificación
        """
        if self.model_type == 'random_forest':
            default_params = {
                'n_estimators': 100,
                'max_depth': 20,
                'min_samples_split': 10,
                'min_samples_leaf': 4,
                'random_state': 42,
                'n_jobs': -1
            }
            default_params.update(params)
            self.model = RandomForestClassifier(**default_params)
            
        elif self.model_type == 'gradient_boosting':
            default_params = {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 5,
                'random_state': 42
            }
            default_params.update(params)
            self.model = GradientBoostingClassifier(**default_params)
        
        return self.model
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        Entrenar el modelo
        """
        print("\n" + "=" * 60)
        print(f"ENTRENANDO MODELO: {self.model_type.upper()}")
        print("=" * 60)
        
        print(f"\nDatos de entrenamiento: {X_train.shape}")
        if X_val is not None:
            print(f"Datos de validación: {X_val.shape}")
        
        # Entrenar
        print("\nEntrenando...")
        self.model.fit(X_train, y_train)
        
        # Evaluar en entrenamiento
        train_score = self.model.score(X_train, y_train)
        print(f"✓ Accuracy en entrenamiento: {train_score:.4f}")
        
        # Evaluar en validación
        if X_val is not None and y_val is not None:
            val_score = self.model.score(X_val, y_val)
            print(f"✓ Accuracy en validación: {val_score:.4f}")
            
            self.training_history['train_score'] = train_score
            self.training_history['val_score'] = val_score
        
        # Importancia de características
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': X_train.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\n✓ Top 10 características más importantes:")
            for idx, row in self.feature_importance.head(10).iterrows():
                print(f"  {row['feature']}: {row['importance']:.4f}")
        
        return self.model
    
    def evaluate(self, X_test, y_test):
        """
        Evaluar el modelo
        """
        print("\n" + "=" * 60)
        print("EVALUACIÓN DEL MODELO")
        print("=" * 60)
        
        # Predicciones
        y_pred = self.model.predict(X_test)
        
        # Métricas
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        
        print(f"\nMétricas Generales:")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall: {recall:.4f}")
        print(f"  F1-Score: {f1:.4f}")
        
        # Reporte detallado
        print(f"\nReporte de Clasificación:")
        print(classification_report(y_test, y_pred))
        
        # Matriz de confusión
        cm = confusion_matrix(y_test, y_pred)
        print(f"\nMatriz de Confusión:")
        print(cm)
        
        # Guardar métricas
        self.training_history['test_accuracy'] = accuracy
        self.training_history['test_precision'] = precision
        self.training_history['test_recall'] = recall
        self.training_history['test_f1'] = f1
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm
        }
    
    def cross_validate(self, X, y, cv=5):
        """
        Validación cruzada
        """
        print(f"\nRealizando validación cruzada ({cv} folds)...")
        
        scores = cross_val_score(self.model, X, y, cv=cv, scoring='accuracy')
        
        print(f"✓ Scores por fold: {scores}")
        print(f"✓ Accuracy promedio: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
        
        return scores
    
    def hyperparameter_tuning(self, X_train, y_train, param_grid=None):
        """
        Búsqueda de hiperparámetros óptimos
        """
        print("\n" + "=" * 60)
        print("BÚSQUEDA DE HIPERPARÁMETROS")
        print("=" * 60)
        
        if param_grid is None:
            if self.model_type == 'random_forest':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [10, 20, 30, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            elif self.model_type == 'gradient_boosting':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                }
        
        print(f"Parámetros a probar: {param_grid}")
        
        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        print("\nBuscando mejores parámetros...")
        grid_search.fit(X_train, y_train)
        
        print(f"\n✓ Mejores parámetros: {grid_search.best_params_}")
        print(f"✓ Mejor score: {grid_search.best_score_:.4f}")
        
        self.model = grid_search.best_estimator_
        
        return grid_search.best_params_
    
    def save_model(self, filepath):
        """
        Guardar modelo entrenado
        """
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_importance': self.feature_importance,
            'training_history': self.training_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n✓ Modelo guardado en: {filepath}")
    
    def load_model(self, filepath):
        """
        Cargar modelo entrenado
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.feature_importance = model_data.get('feature_importance')
        self.training_history = model_data.get('training_history', {})
        
        print(f"✓ Modelo cargado desde: {filepath}")
        
        return self.model

# Script de entrenamiento
def train_risk_model():
    """
    Script principal de entrenamiento
    """
    print("=" * 60)
    print("ENTRENAMIENTO DEL MODELO DE RIESGO")
    print("=" * 60)
    
    # 1. Cargar datos
    print("\n1. Cargando datos...")
    df = pd.read_pickle("../data/processed/training_data.pkl")
    
    # 2. Preparar características
    print("\n2. Preparando características...")
    from feature_engineering import FeatureEngineer
    
    engineer = FeatureEngineer()
    X, y = engineer.prepare_features(df, target_col='risk_category')
    
    # 3. Dividir datos
    print("\n3. Dividiendo datos...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"  Entrenamiento: {X_train.shape}")
    print(f"  Validación: {X_val.shape}")
    print(f"  Prueba: {X_test.shape}")
    
    # 4. Crear y entrenar modelo
    print("\n4. Creando modelo...")
    classifier = RiskClassifier(model_type='random_forest')
    classifier.create_model()
    
    # 5. Entrenar
    classifier.train(X_train, y_train, X_val, y_val)
    
    # 6. Evaluar
    metrics = classifier.evaluate(X_test, y_test)
    
    # 7. Validación cruzada
    classifier.cross_validate(X_train, y_train, cv=5)
    
    # 8. Guardar modelo
    classifier.save_model("../data/models/risk_classifier_v1.pkl")
    
    print("\n" + "=" * 60)
    print("ENTRENAMIENTO COMPLETADO")
    print("=" * 60)
    
    return classifier, metrics

if __name__ == "__main__":
    classifier, metrics = train_risk_model()
```

---

## 4. Evaluación y Validación

### 4.1 Script de Evaluación Completa

**Ubicación:** `backend/scripts/evaluate_model.py`

```python
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve
from sklearn.preprocessing import label_binarize

def plot_confusion_matrix(cm, classes, output_file):
    """
    Visualizar matriz de confusión
    """
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title('Matriz de Confusión')
    plt.ylabel('Etiqueta Real')
    plt.xlabel('Etiqueta Predicha')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"✓ Matriz de confusión guardada en: {output_file}")

def plot_feature_importance(feature_importance, output_file, top_n=15):
    """
    Visualizar importancia de características
    """
    plt.figure(figsize=(10, 8))
    top_features = feature_importance.head(top_n)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importancia')
    plt.title(f'Top {top_n} Características Más Importantes')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"✓ Importancia de características guardada en: {output_file}")

def evaluate_model_comprehensive(model_file, test_data_file):
    """
    Evaluación comprehensiva del modelo
    """
    print("=" * 60)
    print("EVALUACIÓN COMPREHENSIVA DEL MODELO")
    print("=" * 60)
    
    # Cargar modelo
    with open(model_file, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_importance = model_data.get('feature_importance')
    
    # Cargar datos de prueba
    df_test = pd.read_pickle(test_data_file)
    
    # Preparar características
    from feature_engineering import FeatureEngineer
    engineer = FeatureEngineer()
    X_test, y_test = engineer.prepare_features(df_test, target_col='risk_category', fit=False)
    
    # Predicciones
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Visualizaciones
    classes = model.classes_
    
    # 1. Matriz de confusión
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion_matrix(cm, classes, "../data/models/confusion_matrix.png")
    
    # 2. Importancia de características
    if feature_importance is not None:
        plot_feature_importance(feature_importance, "../data/models/feature_importance.png")
    
    # 3. Distribución de predicciones
    plt.figure(figsize=(10, 6))
    pd.Series(y_pred).value_counts().plot(kind='bar')
    plt.title('Distribución de Predicciones')
    plt.xlabel('Categoría de Riesgo')
    plt.ylabel('Frecuencia')
    plt.tight_layout()
    plt.savefig("../data/models/prediction_distribution.png", dpi=150)
    print("✓ Distribución de predicciones guardada")
    
    print("\n" + "=" * 60)
    print("EVALUACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    evaluate_model_comprehensive(
        "../data/models/risk_classifier_v1.pkl",
        "../data/processed/training_data.pkl"
    )
```

---

## 5. Implementación en Producción

### 5.1 Servicio de Predicción

**Ubicación:** `backend/app/services/ml_prediction_service.py`

```python
import pickle
import pandas as pd
import numpy as np

class MLPredictionService:
    """
    Servicio para hacer predicciones de riesgo en producción
    """
    
    def __init__(self, model_path):
        """
        Cargar modelo entrenado
        """
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        print(f"✓ Modelo cargado: {self.model_type}")
    
    def predict_edge_risk(self, edge_features):
        """
        Predecir riesgo para una arista
        
        Args:
            edge_features: dict con características de la arista
        
        Returns:
            dict con predicción y probabilidades
        """
        # Convertir a DataFrame
        df = pd.DataFrame([edge_features])
        
        # Preparar características (debe coincidir con entrenamiento)
        # Simplificado - en producción usar el mismo FeatureEngineer
        X = df[self.model.feature_names_in_]
        
        # Predecir
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Crear diccionario de probabilidades por clase
        prob_dict = {
            class_name: float(prob)
            for class_name, prob in zip(self.model.classes_, probabilities)
        }
        
        return {
            'risk_category': prediction,
            'probabilities': prob_dict,
            'confidence': float(max(probabilities))
        }
    
    def predict_route_risk(self, route_edges):
        """
        Predecir riesgo para una ruta completa
        
        Args:
            route_edges: lista de dicts con características de aristas
        
        Returns:
            dict con estadísticas de riesgo de la ruta
        """
        predictions = []
        
        for edge in route_edges:
            pred = self.predict_edge_risk(edge)
            predictions.append(pred)
        
        # Calcular estadísticas
        risk_scores = [p['confidence'] for p in predictions]
        risk_categories = [p['risk_category'] for p in predictions]
        
        return {
            'average_risk': np.mean(risk_scores),
            'max_risk': max(risk_scores),
            'min_risk': min(risk_scores),
            'risk_distribution': pd.Series(risk_categories).value_counts().to_dict(),
            'critical_segments': [
                i for i, cat in enumerate(risk_categories)
                if cat in ['alto', 'muy_alto']
            ]
        }

# Ejemplo de uso
if __name__ == "__main__":
    service = MLPredictionService("../data/models/risk_classifier_v1.pkl")
    
    # Ejemplo de predicción
    edge = {
        'length': 150,
        'speed_limit': 60,
        'num_lanes': 2,
        'has_cycleway': 0,
        'has_bike_lane': 0,
        'is_oneway': 1,
        'has_name': 1,
        'num_points': 5,
        'sinuosity': 1.1,
        'highway_type_encoded': 2
    }
    
    result = service.predict_edge_risk(edge)
    print(f"\nPredicción: {result}")
```

---

## Resumen de Archivos Creados

```
backend/
├── scripts/
│   ├── prepare_training_data.py      # Preparación de datos
│   ├── evaluate_model.py              # Evaluación del modelo
│   └── train_model.py                 # Script de entrenamiento
│
├── app/
│   ├── models/
│   │   ├── feature_engineering.py    # Ingeniería de features
│   │   └── risk_classifier.py        # Modelo de clasificación
│   │
│   └── services/
│       └── ml_prediction_service.py  # Servicio de predicción
│
└── data/
    ├── processed/
    │   └── training_data.pkl         # Dataset de entrenamiento
    │
    └── models/
        ├── risk_classifier_v1.pkl    # Modelo entrenado
        ├── confusion_matrix.png       # Visualizaciones
        └── feature_importance.png
```

## Comandos para Ejecutar

```bash
# 1. Preparar datos de entrenamiento
cd backend/scripts
python prepare_training_data.py

# 2. Entrenar modelo
python -c "from risk_classifier import train_risk_model; train_risk_model()"

# 3. Evaluar modelo
python evaluate_model.py

# 4. Probar predicciones
python -c "from ml_prediction_service import MLPredictionService; service = MLPredictionService('../data/models/risk_classifier_v1.pkl'); print(service.predict_edge_risk({'length': 150, 'speed_limit': 60, 'num_lanes': 2, 'has_cycleway': 0}))"
```

## Métricas Esperadas

- **Accuracy:** >85%
- **Precision:** >80%
- **Recall:** >80%
- **F1-Score:** >80%

El modelo está listo para integrarse en el sistema de enrutamiento.