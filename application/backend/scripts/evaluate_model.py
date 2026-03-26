import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve
from sklearn.preprocessing import label_binarize
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
    from app.models.feature_engineering import FeatureEngineer
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
    plot_confusion_matrix(cm, classes, "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/models/confusion_matrix.png")
    
    # 2. Importancia de características
    if feature_importance is not None:
        plot_feature_importance(feature_importance, "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/models/feature_importance.png")
    
    # 3. Distribución de predicciones
    plt.figure(figsize=(10, 6))
    pd.Series(y_pred).value_counts().plot(kind='bar')
    plt.title('Distribución de Predicciones')
    plt.xlabel('Categoría de Riesgo')
    plt.ylabel('Frecuencia')
    plt.tight_layout()
    plt.savefig("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/models/prediction_distribution.png", dpi=150)
    print("✓ Distribución de predicciones guardada")
    
    print("\n" + "=" * 60)
    print("EVALUACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    evaluate_model_comprehensive(
        "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/models/risk_classifier_v1.pkl",
        "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/training_data.pkl"
    )
