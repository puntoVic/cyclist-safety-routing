from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()

@router.get("")
async def get_segments(
    min_lon: float = Query(..., description="Longitud mínima"),
    min_lat: float = Query(..., description="Latitud mínima"),
    max_lon: float = Query(..., description="Longitud máxima"),
    max_lat: float = Query(..., description="Latitud máxima"),
):
    """
    Obtener segmentos de calle con información de riesgo
    """
    return {
        "segments": [],
        "total": 0,
        "bbox": {
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat
        }
    }

@router.get("/{segment_id}")
async def get_segment_detail(segment_id: str):
    """
    Obtener detalle de un segmento específico
    """
    raise HTTPException(status_code=404, detail="Segmento no encontrado")
