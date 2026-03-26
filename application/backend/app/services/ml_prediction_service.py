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
    service = MLPredictionService("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/models/risk_classifier_v1.pkl")
    
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
