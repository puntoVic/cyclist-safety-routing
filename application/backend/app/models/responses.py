from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class RouteSegment(BaseModel):
    """Segmento de una ruta"""
    segment_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    length: float = Field(..., description="Longitud en metros")
    risk_score: float = Field(..., ge=0, le=1)
    risk_category: str = Field(..., description="bajo, medio, alto")
    street_name: Optional[str] = None
    highway_type: Optional[str] = None
    has_bike_lane: bool = False

class RouteResponse(BaseModel):
    """Respuesta de cálculo de ruta"""
    route_id: str
    origin: Dict[str, float]
    destination: Dict[str, float]
    segments: List[RouteSegment]
    total_distance: float = Field(..., description="Distancia total en metros")
    estimated_time: float = Field(..., description="Tiempo estimado en segundos")
    average_risk: float = Field(..., ge=0, le=1)
    max_risk: float = Field(..., ge=0, le=1)
    critical_segments: List[int] = Field(
        default=[],
        description="Índices de segmentos críticos"
    )
    warnings: List[str] = Field(default=[])
    computation_time: float = Field(..., description="Tiempo de cálculo en ms")

class AlternativeRoutesResponse(BaseModel):
    """Respuesta con rutas alternativas"""
    routes: List[RouteResponse]
    comparison: Dict[str, Any] = Field(
        description="Comparación entre rutas"
    )

class HeatmapCell(BaseModel):
    """Celda del mapa de calor"""
    lat: float
    lon: float
    risk_score: float = Field(..., ge=0, le=1)
    accident_count: int = Field(default=0)

class HeatmapResponse(BaseModel):
    """Respuesta de mapa de calor"""
    cells: List[HeatmapCell]
    bbox: List[float]
    resolution: int
    risk_factors: Dict[str, float] = Field(
        description="Factores de riesgo dominantes"
    )
    generated_at: datetime

class SegmentDetailResponse(BaseModel):
    """Detalle de un segmento"""
    segment_id: str
    geometry: List[List[float]]
    risk_score: float
    risk_category: str
    risk_factors: List[Dict[str, Any]]
    recent_accidents: int
    recommendations: List[str]
    nearby_alternatives: List[str]

class HealthResponse(BaseModel):
    """Estado del servicio"""
    status: str = Field(..., description="healthy, degraded, unhealthy")
    version: str
    uptime: float = Field(..., description="Tiempo activo en segundos")
    graph_loaded: bool
    graph_nodes: int
    graph_edges: int
    cache_status: str
    last_update: datetime
