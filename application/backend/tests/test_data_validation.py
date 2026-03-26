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
