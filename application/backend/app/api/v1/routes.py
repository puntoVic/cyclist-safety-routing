from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
import time
import uuid

from app.models.requests import RouteRequest
from app.models.responses import RouteResponse, AlternativeRoutesResponse
from app.services.routing_service import RoutingService
from app.core.cache import get_cache, set_cache

router = APIRouter()

def get_routing_service(request: Request) -> RoutingService:
    """Dependencia para obtener el servicio de rutas"""
    return request.app.state.routing_service

@router.post("/calculate", response_model=RouteResponse)
async def calculate_route(
    route_request: RouteRequest,
    routing_service: RoutingService = Depends(get_routing_service)
):
    """
    Calcular ruta óptima entre dos puntos
    
    - **origin**: Coordenadas de origen (lat, lon)
    - **destination**: Coordenadas de destino (lat, lon)
    - **alpha**: Peso de seguridad (0-1)
    - **beta**: Peso de distancia (0-1)
    - **avoid_critical**: Evitar segmentos de alto riesgo
    """
    start_time = time.time()
    
    try:
        # Generar cache key
        cache_key = f"route:{route_request.origin.lat},{route_request.origin.lon}:" \
                   f"{route_request.destination.lat},{route_request.destination.lon}:" \
                   f"{route_request.alpha},{route_request.beta}"
        
        # Buscar en cache
        cached_result = await get_cache(cache_key)
        if cached_result:
            print(f"✓ Ruta encontrada en cache")
            return cached_result
        
        # Calcular ruta
        result = routing_service.calculate_route(
            origin=(route_request.origin.lat, route_request.origin.lon),
            destination=(route_request.destination.lat, route_request.destination.lon),
            alpha=route_request.alpha,
            beta=route_request.beta,
            avoid_critical=route_request.avoid_critical
        )
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        # Construir respuesta
        computation_time = (time.time() - start_time) * 1000  # ms
        
        response = RouteResponse(
            route_id=str(uuid.uuid4()),
            origin={
                "lat": route_request.origin.lat,
                "lon": route_request.origin.lon
            },
            destination={
                "lat": route_request.destination.lat,
                "lon": route_request.destination.lon
            },
            segments=result['segments'],
            total_distance=result['total_distance'],
            estimated_time=result['estimated_time'],
            average_risk=result['average_risk'],
            max_risk=result['max_risk'],
            critical_segments=result.get('critical_segments', []),
            warnings=result.get('warnings', []),
            computation_time=computation_time
        )
        
        # Guardar en cache (5 minutos)
        await set_cache(cache_key, response.dict(), expire=300)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular ruta: {str(e)}"
        )

@router.post("/alternatives", response_model=AlternativeRoutesResponse)
async def get_alternative_routes(
    route_request: RouteRequest,
    routing_service: RoutingService = Depends(get_routing_service)
):
    """
    Obtener múltiples rutas alternativas
    
    Calcula hasta `max_alternatives` rutas diferentes optimizando
    diferentes criterios (más segura, más rápida, balanceada)
    """
    try:
        alternatives = routing_service.calculate_alternatives(
            origin=(route_request.origin.lat, route_request.origin.lon),
            destination=(route_request.destination.lat, route_request.destination.lon),
            max_alternatives=route_request.max_alternatives
        )
        
        if 'error' in alternatives:
            raise HTTPException(status_code=404, detail=alternatives['error'])
        
        return AlternativeRoutesResponse(
            routes=alternatives['routes'],
            comparison=alternatives['comparison']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular alternativas: {str(e)}"
        )

@router.post("/compare")
async def compare_routes(
    routes: List[str],
    routing_service: RoutingService = Depends(get_routing_service)
):
    """
    Comparar múltiples rutas guardadas
    
    - **routes**: Lista de IDs de rutas a comparar
    """
    try:
        comparison = routing_service.compare_routes(routes)
        return comparison
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al comparar rutas: {str(e)}"
        )
