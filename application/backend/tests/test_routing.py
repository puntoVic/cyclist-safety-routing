test_routes = {
    'centro_to_zapopan': {
        'origin': (20.6767, -103.3475),  # Catedral
        'destination': (20.7206, -103.3897),  # Plaza Andares
        'expected_distance': 8.5,  # km
        'known_risks': ['Av. Vallarta', 'high traffic']
    },
    'tlaquepaque_to_centro': {
        'origin': (20.6401, -103.3125),  # Tlaquepaque Centro
        'destination': (20.6767, -103.3475),  # Catedral
        'expected_distance': 6.2,  # km
        'known_risks': ['Calzada Independencia']
    },
    'minerva_circuit': {
        'origin': (20.6738, -103.3925),  # Minerva
        'destination': (20.6738, -103.3925),  # Circular route
        'expected_distance': 5.0,  # km
        'known_risks': ['Av. López Mateos', 'Av. Américas']
    }
}
