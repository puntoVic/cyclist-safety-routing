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
    df = pd.read_pickle("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/training_data.pkl")
    
    # Crear ingeniero de características
    engineer = FeatureEngineer()
    
    # Preparar características
    X, y = engineer.prepare_features(df, target_col='risk_category')
    
    print(f"\nForma final de X: {X.shape}")
    print(f"Forma final de y: {y.shape}")
