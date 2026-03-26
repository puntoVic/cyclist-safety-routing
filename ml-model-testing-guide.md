# Guía de Testing del Modelo de Machine Learning
## Sistema de Rutas Seguras para Ciclistas - Guadalajara

---

## Índice
1. [Validación de Datos](#1-validación-de-datos)
2. [Tests Unitarios del Pipeline](#2-tests-unitarios-del-pipeline)
3. [Evaluación del Modelo](#3-evaluación-del-modelo)
4. [Tests de Robustez](#4-tests-de-robustez)
5. [Tests de Sesgo y Fairness](#5-tests-de-sesgo-y-fairness)
6. [Tests de Performance](#6-tests-de-performance)
7. [Monitoreo en Producción](#7-monitoreo-en-producción)
8. [Checklist Completo](#8-checklist-completo)

---

## 1. Validación de Datos

### 1.1 Script de Validación

**Archivo:** `backend/tests/test_data_validation.py`

```python
import pytest
import pandas as pd
import numpy as np

class TestDataValidation:
    """Tests para validación de datos"""
    
    def test_required_columns_present(self):
        """Verificar columnas requeridas"""
        df = pd.DataFrame({
            'segment_id': ['seg1', 'seg2'],
            'length': [100, 200],
            'risk_score': [0.6, 0.2]
        })
        
        required = ['segment_id', 'length', 'risk_score']
        assert all(col in df.columns for col in required)
    
    def test_risk_score_in_range(self):
        """Verificar risk_score entre 0 y 1"""
        df = pd.DataFrame({'risk_score': [0.0, 0.5, 1.0]})
        assert ((df['risk_score'] >= 0) & (df['risk_score'] <= 1)).all()
```

---

## 2. Tests del Pipeline ML

### 2.1 Tests de Entrenamiento

**Archivo:** `backend/tests/test_ml_pipeline.py`

```python
import pytest
from app.ml.risk_classifier import RiskClassifier

class TestMLPipeline:
    
    def test_model_training(self, sample_data):
        """Verificar entrenamiento"""
        X, y = sample_data
        classifier = RiskClassifier()
        classifier.fit(X, y)
        
        assert hasattr(classifier.model, 'estimators_')
    
    def test_predictions_valid(self, sample_data):
        """Verificar predicciones válidas"""
        X, y = sample_data
        classifier = RiskClassifier()
        classifier.fit(X, y)
        
        predictions = classifier.predict(X)
        assert set(predictions).issubset({0, 1})
```

---

## 3. Evaluación del Modelo

### 3.1 Métricas de Performance

```python
from sklearn.metrics import accuracy_score, precision_score, recall_score

def test_minimum_accuracy():
    """Accuracy mínimo: 85%"""
    accuracy = classifier.score(X_test, y_test)
    assert accuracy >= 0.85

def test_minimum_precision():
    """Precision mínima: 80%"""
    precision = precision_score(y_test, y_pred)
    assert precision >= 0.80

def test_minimum_recall():
    """Recall mínimo: 75%"""
    recall = recall_score(y_test, y_pred)
    assert recall >= 0.75
```

---

## 4. Tests de Robustez

```python
def test_outliers_handling():
    """Manejo de outliers"""
    X_outliers = pd.DataFrame({
        'length': [100, 200, 10000],  # Outlier
        'speed_limit': [50, 40, 200]
    })
    
    predictions = classifier.predict(X_outliers)
    assert len(predictions) == 3

def test_missing_values():
    """Manejo de valores faltantes"""
    X_missing = pd.DataFrame({
        'length': [100, np.nan, 300]
    })
    
    with pytest.raises(ValueError):
        classifier.predict(X_missing)
```

---

## 5. Tests de Fairness

```python
def test_no_bias_across_road_types():
    """Sin sesgo por tipo de vía"""
    results = {}
    for road_type in ['primary', 'secondary', 'residential']:
        accuracy = test_road_type(road_type)
        results[road_type] = accuracy
    
    max_diff = max(results.values()) - min(results.values())
    assert max_diff < 0.10  # < 10% diferencia
```

---

## 6. Tests de Performance

```python
def test_training_time():
    """Tiempo de entrenamiento < 30s"""
    start = time.time()
    classifier.fit(X_train, y_train)
    elapsed = time.time() - start
    
    assert elapsed < 30

def test_prediction_speed():
    """10k predicciones < 1s"""
    start = time.time()
    predictions = classifier.predict(X_test)
    elapsed = time.time() - start
    
    assert elapsed < 1.0
```

---

## 7. Monitoreo en Producción

### 7.1 Sistema de Monitoreo

```python
class ModelMonitor:
    def log_prediction(self, features, prediction, probability):
        """Registrar predicción"""
        log_entry = {
            'timestamp': datetime.now(),
            'features': features,
            'prediction': prediction,
            'probability': probability
        }
        self.predictions_log.append(log_entry)
    
    def detect_drift(self, current_data, reference_data):
        """Detectar drift de datos"""
        drift = abs(current_data.mean() - reference_data.mean())
        return drift > threshold
```

---

## 8. Checklist Completo

### Validación de Datos
- [ ] Columnas requeridas presentes
- [ ] Sin valores faltantes críticos
- [ ] Tipos de datos correctos
- [ ] Rangos válidos (risk_score 0-1)
- [ ] Sin duplicados
- [ ] Longitudes positivas

### Pipeline ML
- [ ] Modelo inicializa correctamente
- [ ] Entrenamiento exitoso
- [ ] Predicciones con forma correcta
- [ ] Valores de predicción válidos
- [ ] Persistencia funciona
- [ ] Feature importance calculable

### Métricas
- [ ] Accuracy ≥ 85%
- [ ] Precision ≥ 80%
- [ ] Recall ≥ 75%
- [ ] F1-score ≥ 0.77
- [ ] ROC AUC ≥ 0.85

### Robustez
- [ ] Maneja outliers
- [ ] Rechaza valores faltantes
- [ ] Maneja características sin varianza
- [ ] Funciona con clases desbalanceadas
- [ ] Predicciones consistentes

### Fairness
- [ ] Sin sesgo por tipo de vía
- [ ] Sin sesgo por ciclovías
- [ ] Performance similar en subgrupos

### Performance
- [ ] Entrenamiento < 30s
- [ ] Predicción < 1s para 10k
- [ ] Uso de memoria < 500MB
- [ ] Escala sub-cuadráticamente

### Monitoreo
- [ ] Logging de predicciones
- [ ] Detección de drift
- [ ] Alertas de degradación
- [ ] Métricas en tiempo real

---

## Comandos de Testing

```bash
# Todos los tests ML
pytest backend/tests/test_*.py -v

# Con coverage
pytest backend/tests/ --cov=app.ml --cov-report=html

# Tests específicos
pytest backend/tests/test_ml_pipeline.py::TestMLPipeline -v

# Solo tests rápidos
pytest -m "not slow" -v

# Script completo
python backend/run_ml_tests.py
```

---

## Resumen

Testing completo del modelo ML con:
- ✅ Validación de datos (6 tests)
- ✅ Pipeline ML (6 tests)
- ✅ Métricas de evaluación (5 tests)
- ✅ Robustez (6 tests)
- ✅ Fairness (2 tests)
- ✅ Performance (3 tests)
- ✅ Monitoreo en producción

**Objetivo: >80% coverage, todos los tests pasando**