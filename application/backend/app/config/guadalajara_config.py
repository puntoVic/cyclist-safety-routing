GUADALAJARA_RISK_FACTORS = {
    'traffic_volume': {
        'weight': 0.30,  # Higher due to aggressive driving culture
        'thresholds': {
            'low': 0.0-0.3,
            'medium': 0.3-0.7,
            'high': 0.7-1.0
        }
    },
    'speed_limit': {
        'weight': 0.25,
        'values': {
            '≤40 km/h': 0.1,
            '41-60 km/h': 0.4,
            '61-80 km/h': 0.7,
            '>80 km/h': 1.0
        }
    },
    'bike_infrastructure': {
        'weight': 0.20,
        'values': {
            'protected_lane': 0.1,
            'painted_lane': 0.4,
            'shared_road': 0.7,
            'no_infrastructure': 1.0
        }
    },
    'road_surface': {
        'weight': 0.10,  # Important in Guadalajara (baches)
        'values': {
            'excellent': 0.1,
            'good': 0.3,
            'poor': 0.7,
            'very_poor': 1.0
        }
    },
    'lighting': {
        'weight': 0.08,  # Safety concern at night
        'values': {
            'well_lit': 0.2,
            'moderate': 0.5,
            'poor': 0.9
        }
    },
    'accident_history': {
        'weight': 0.07,
        'calculation': 'accidents_per_km_per_year'
    }
}