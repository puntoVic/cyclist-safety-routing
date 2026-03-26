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
    df = pd.read_pickle("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/training_data.pkl")
    
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
    classifier.save_model("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/models/risk_classifier_v1.pkl")
    
    print("\n" + "=" * 60)
    print("ENTRENAMIENTO COMPLETADO")
    print("=" * 60)
    
    return classifier, metrics

if __name__ == "__main__":
    classifier, metrics = train_risk_model()
