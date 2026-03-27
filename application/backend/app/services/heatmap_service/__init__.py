"""
Servicio de Heatmap - generación de mapas de calor de riesgo
"""

class HeatmapService:
    """Servicio para generar mapas de calor de riesgo ciclista"""
    
    def __init__(self):
        print("[OK] HeatmapService inicializado")
    
    def generate_heatmap(self, bbox, zoom=14, resolution=50):
        """Generar datos de mapa de calor para un bounding box"""
        min_lon, min_lat, max_lon, max_lat = bbox
        
        return {
            "cells": [],
            "bbox": {
                "min_lon": min_lon,
                "min_lat": min_lat,
                "max_lon": max_lon,
                "max_lat": max_lat
            },
            "resolution": resolution,
            "zoom": zoom,
            "total_cells": 0,
            "risk_stats": {
                "min_risk": 0.0,
                "max_risk": 0.0,
                "avg_risk": 0.0
            }
        }
