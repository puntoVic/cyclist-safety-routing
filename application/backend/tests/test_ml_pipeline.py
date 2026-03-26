import pytest
from app.models.risk_classifier import RiskClassifier


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
