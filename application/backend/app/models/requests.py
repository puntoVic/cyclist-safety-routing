from pydantic import BaseModel, Field, validator
from typing import Optional, List, Tuple
from datetime import datetime

class Coordinates(BaseModel):
    """Coordenadas geográficas"""
    lat: float = Field(..., ge=-90, le=90, description="Latitud")
    lon: float = Field(..., ge=-180, le=180, description="Longitud")
    
    @validator('lat')
    def validate_guadalajara_lat(cls, v):
        if not (20.5 <= v <= 20.8):
            raise ValueError('Latitud fuera del área de Guadalajara')
        return v
    
    @validator('lon')
    def validate_guadalajara_lon(cls, v):
        if not (-103.6 <= v <= -103.2):
            raise ValueError('Longitud fuera del área de Guadalajara')
        return v

class RouteRequest(BaseModel):
    """Solicitud de cálculo de ruta"""
    origin: Coordinates = Field(..., description="Punto de origen")
    destination: Coordinates = Field(..., description="Punto de destino")
    alpha: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Peso de seguridad (0-1)"
    )
    beta: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Peso de distancia (0-1)"
    )
    avoid_critical: bool = Field(
        True,
        description="Evitar segmentos críticos"
    )
    max_alternatives: int = Field(
        3,
        ge=1,
        le=5,
        description="Número máximo de rutas alternativas"
    )
    time: Optional[datetime] = Field(
        None,
        description="Hora para considerar tráfico"
    )
    
    @validator('beta')
    def validate_weights_sum(cls, v, values):
        if 'alpha' in values:
            if abs(values['alpha'] + v - 1.0) > 0.01:
                raise ValueError('alpha + beta debe ser igual a 1.0')
        return v

class HeatmapRequest(BaseModel):
    """Solicitud de mapa de calor"""
    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Bounding box (min_lon, min_lat, max_lon, max_lat)"
    )
    zoom: int = Field(
        14,
        ge=10,
        le=18,
        description="Nivel de zoom"
    )
    resolution: int = Field(
        50,
        ge=10,
        le=200,
        description="Resolución del grid"
    )

class SegmentQuery(BaseModel):
    """Consulta de segmentos cercanos"""
    location: Coordinates
    radius_km: float = Field(
        1.0,
        ge=0.1,
        le=10.0,
        description="Radio de búsqueda en km"
    )
