from fastapi import APIRouter, Request
from datetime import datetime
import time

from app.models.responses import HealthResponse

router = APIRouter()

start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Verificar estado del servicio
    """
    routing_service = request.app.state.routing_service
    
    # Verificar estado del grafo
    graph_loaded = routing_service.G is not None
    graph_nodes = len(routing_service.G.nodes) if graph_loaded else 0
    graph_edges = len(routing_service.G.edges) if graph_loaded else 0
    
    # Determinar estado general
    if graph_loaded and graph_nodes > 1000:
        status = "healthy"
    elif graph_loaded:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
        uptime=time.time() - start_time,
        graph_loaded=graph_loaded,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        cache_status="active",
        last_update=datetime.now()
    )

@router.get("/metrics")
async def get_metrics():
    """
    Obtener métricas de uso del servicio
    """
    # Implementar con Prometheus o similar
    return {
        "requests_total": 0,
        "requests_per_minute": 0,
        "average_response_time": 0,
        "cache_hit_rate": 0
    }
