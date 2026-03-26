from datetime import datetime

class ViaRecreActivaService:
    """
    Handle Via RecreActiva (Sunday cycling routes) special routing
    """
    
    RECREACTIVA_ROUTES = {
        'centro': {
            'active_days': ['sunday'],
            'hours': (8, 14),  # 8 AM - 2 PM
            'segments': [
                # List of OSM way IDs that are part of Via RecreActiva
            ]
        },
        'zapopan': {
            'active_days': ['sunday'],
            'hours': (8, 14),
            'segments': []
        }
    }
    
    def is_recreactiva_active(self, datetime_obj=None):
        """Check if Via RecreActiva is currently active"""
        if datetime_obj is None:
            datetime_obj = datetime.now()
        
        # Check if Sunday
        if datetime_obj.weekday() != 6:  # 6 = Sunday
            return False
        
        # Check time
        hour = datetime_obj.hour
        return 8 <= hour <= 14
    
    def adjust_risk_for_recreactiva(self, G, datetime_obj=None):
        """
        Reduce risk scores for Via RecreActiva routes when active
        """
        if not self.is_recreactiva_active(datetime_obj):
            return G
        
        # Reduce risk by 70% on RecreActiva routes
        for route_data in self.RECREACTIVA_ROUTES.values():
            for segment_id in route_data['segments']:
                # Find edge in graph and reduce risk
                # Implementation depends on how segments are stored
                pass
        
        return G
