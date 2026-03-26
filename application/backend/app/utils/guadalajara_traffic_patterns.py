GUADALAJARA_TRAFFIC_PATTERNS = {
    'rush_hours': {
        'morning': (7, 10),    # 7 AM - 10 AM
        'evening': (18, 21),   # 6 PM - 9 PM
        'risk_multiplier': 1.5
    },
    'high_traffic_days': {
        'monday': 1.2,
        'friday': 1.3,
        'saturday': 1.1
    },
    'special_events': {
        'fiestas_octubre': {
            'months': [10],
            'areas': ['centro', 'minerva'],
            'risk_multiplier': 1.8
        },
        'feria_libro': {
            'months': [11],
            'areas': ['expo_guadalajara'],
            'risk_multiplier': 1.4
        }
    }
}

def adjust_for_local_patterns(risk_score, datetime_obj, location):
    """
    Adjust risk score based on Guadalajara-specific patterns
    """
    hour = datetime_obj.hour
    day = datetime_obj.weekday()
    month = datetime_obj.month
    
    # Rush hour adjustment
    if (7 <= hour <= 10) or (18 <= hour <= 21):
        risk_score *= 1.5
    
    # Weekend adjustment (less traffic)
    if day in [5, 6]:  # Saturday, Sunday
        risk_score *= 0.8
    
    return min(risk_score, 1.0)
