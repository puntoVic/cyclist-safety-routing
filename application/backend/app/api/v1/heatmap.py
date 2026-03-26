from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Optional

from app.models.requests import HeatmapRequest
from app.models.responses import HeatmapResponse
from app.services.heatmap_service import HeatmapService

router = APIRouter()

def get_heatmap_service(request: Request) -> HeatmapService:
    """Dependencia para obtener el servicio de heatmap"""
    if not hasattr(request.app.state, 'heatmap_service'):
        request.app.state.heatmap_service = HeatmapService()
    return request.app.state.heatmap_service

@router.get("", response_model=HeatmapResponse)
async def get_heatmap(
    min_lon: float = Query(..., description="Longitud mínima"),
    min_lat: float = Query(..., description="Latitud mínima"),
    max_lon: float = Query(..., description="Longitud máxima"),
    max_lat: float = Query(..., description="Latitud máxima"),
    zoom: int = Query(14, ge=10, le=18),
    resolution: int = Query(50, ge=10, le=200),
    heatmap_service: HeatmapService = Depends(get_heatmap_service)
):
    """
    Obtener mapa de calor de riesgo para un área
    
    - **bbox**: Área de interés (min_lon, min_lat, max_lon, max_lat)
    - **zoom**: Nivel de zoom del mapa
    - **resolution**: Resolución del grid (celdas por lado)
    """
    try:
        heatmap_data = heatmap_service.generate_heatmap(
            bbox=(min_lon, min_lat, max_lon, max_lat),
            zoom=zoom,
            resolution=resolution
        )
        
        return heatmap_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar mapa de calor: {str(e)}"
        )
