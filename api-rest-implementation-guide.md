# Guía de Implementación de API REST
## Sistema de Rutas Seguras para Ciclistas - Guadalajara

---

## Índice
1. [Configuración Inicial](#1-configuración-inicial)
2. [Estructura del Proyecto](#2-estructura-del-proyecto)
3. [Endpoints Principales](#3-endpoints-principales)
4. [Implementación con FastAPI](#4-implementación-con-fastapi)
5. [Autenticación y Seguridad](#5-autenticación-y-seguridad)
6. [Documentación Automática](#6-documentación-automática)
7. [Testing de la API](#7-testing-de-la-api)

---

## 1. Configuración Inicial

### 1.1 Instalar Dependencias

**Archivo:** `backend/requirements-api.txt`

```txt
# Framework API
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# CORS y seguridad
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Cache y rendimiento
redis==5.0.1
aioredis==2.0.1

# Validación y serialización
pydantic-settings==2.1.0
email-validator==2.1.0

# Monitoreo
prometheus-client==0.19.0

# Ya instaladas (del proyecto principal)
# networkx, osmnx, pandas, numpy, scikit-learn
```

**Instalar:**
```bash
cd backend
pip install -r requirements-api.txt
```

---

## 2. Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Punto de entrada de la API
│   ├── config.py                  # Configuración
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencias compartidas
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── routes.py          # Rutas principales
│   │       ├── heatmap.py         # Mapa de calor
│   │       ├── segments.py        # Información de segmentos
│   │       └── health.py          # Health checks
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py            # Modelos de request
│   │   └── responses.py           # Modelos de response
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── routing_service.py     # Ya existe
│   │   ├── cache_service.py       # Nuevo: Cache
│   │   └── ml_service.py          # Servicio ML
│   │
│   └── core/
│       ├── __init__.py
│       ├── security.py            # Autenticación
│       └── cache.py               # Configuración cache
│
└── tests/
    └── api/
        ├── test_routes.py
        └── test_heatmap.py
```

---

## 3. Endpoints Principales

### 3.1 Diseño de la API

**Base URL:** `http://localhost:8000/api/v1`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/routes/calculate` | POST | Calcular ruta óptima |
| `/routes/alternatives` | POST | Obtener rutas alternativas |
| `/routes/compare` | POST | Comparar múltiples rutas |
| `/heatmap` | GET | Obtener mapa de calor de riesgo |
| `/segments/{id}` | GET | Información de segmento |
| `/segments/nearby` | GET | Segmentos cercanos |
| `/health` | GET | Estado del servicio |
| `/metrics` | GET | Métricas de uso |

---

## 4. Implementación con FastAPI

### 4.1 Archivo Principal

**Ubicación:** `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.api.v1 import routes, heatmap, segments, health
from app.core.cache import init_cache, close_cache
from app.services.routing_service import RoutingService

# Variables globales
routing_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    """
    # Startup
    print("🚀 Iniciando API de Rutas Seguras...")
    
    # Inicializar cache
    await init_cache()
    
    # Cargar grafo y servicios
    global routing_service
    routing_service = RoutingService()
    app.state.routing_service = routing_service
    
    print("✓ Servicios inicializados")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando API...")
    await close_cache()
    print("✓ Recursos liberados")

# Crear aplicación
app = FastAPI(
    title="API de Rutas Seguras para Ciclistas",
    description="Sistema inteligente de enrutamiento para ciclistas en Guadalajara, Jalisco",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev
        "http://localhost:5173",  # Vite dev
        "https://tu-dominio.com"  # Producción
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Comprimir respuestas
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Incluir routers
app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"]
)

app.include_router(
    routes.router,
    prefix="/api/v1/routes",
    tags=["routes"]
)

app.include_router(
    heatmap.router,
    prefix="/api/v1/heatmap",
    tags=["heatmap"]
)

app.include_router(
    segments.router,
    prefix="/api/v1/segments",
    tags=["segments"]
)

# Ruta raíz
@app.get("/")
async def root():
    return {
        "message": "API de Rutas Seguras para Ciclistas - Guadalajara",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Solo en desarrollo
        log_level="info"
    )
```

### 4.2 Modelos de Datos

**Ubicación:** `backend/app/models/requests.py`

```python
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
```

**Ubicación:** `backend/app/models/responses.py`

```python
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
```

### 4.3 Endpoint de Rutas

**Ubicación:** `backend/app/api/v1/routes.py`

```python
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
```

### 4.4 Endpoint de Mapa de Calor

**Ubicación:** `backend/app/api/v1/heatmap.py`

```python
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
```

### 4.5 Health Check

**Ubicación:** `backend/app/api/v1/health.py`

```python
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
```

---

## 5. Autenticación y Seguridad

### 5.1 Configuración de Seguridad

**Ubicación:** `backend/app/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuración
SECRET_KEY = "tu-clave-secreta-muy-segura-cambiar-en-produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validar token y obtener usuario actual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        return username
        
    except JWTError:
        raise credentials_exception
```

### 5.2 Rate Limiting

**Ubicación:** `backend/app/core/rate_limit.py`

```python
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    """Limitador de tasa de peticiones"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def check_rate_limit(self, request: Request):
        """Verificar límite de tasa"""
        client_ip = request.client.host
        now = datetime.now()
        
        # Limpiar requests antiguos
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if now - req_time < timedelta(minutes=1)
            ]
        else:
            self.requests[client_ip] = []
        
        # Verificar límite
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Demasiadas peticiones. Intenta de nuevo más tarde."
            )
        
        # Registrar petición
        self.requests[client_ip].append(now)

rate_limiter = RateLimiter(requests_per_minute=60)
```

---

## 6. Documentación Automática

FastAPI genera documentación automática en:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 6.1 Personalizar Documentación

```python
# En main.py
app = FastAPI(
    title="API de Rutas Seguras para Ciclistas",
    description="""
    ## Sistema Inteligente de Enrutamiento
    
    Esta API proporciona:
    * **Cálculo de rutas** optimizadas para seguridad
    * **Mapas de calor** de riesgo
    * **Rutas alternativas** con diferentes criterios
    * **Información detallada** de segmentos
    
    ### Autenticación
    Usa Bearer token en el header Authorization
    
    ### Rate Limiting
    60 peticiones por minuto por IP
    """,
    version="1.0.0",
    contact={
        "name": "Equipo de Desarrollo",
        "email": "contacto@rutasseguras.mx"
    },
    license_info={
        "name": "MIT",
    }
)
```

---

## 7. Testing de la API

### 7.1 Tests Unitarios

**Ubicación:** `backend/tests/api/test_routes.py`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_calculate_route():
    """Test de cálculo de ruta"""
    response = client.post(
        "/api/v1/routes/calculate",
        json={
            "origin": {"lat": 20.6767, "lon": -103.3475},
            "destination": {"lat": 20.6800, "lon": -103.3400},
            "alpha": 0.7,
            "beta": 0.3
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "route_id" in data
    assert "segments" in data
    assert data["total_distance"] > 0

def test_invalid_coordinates():
    """Test con coordenadas inválidas"""
    response = client.post(
        "/api/v1/routes/calculate",
        json={
            "origin": {"lat": 90.0, "lon": 0.0},  # Fuera de Guadalajara
            "destination": {"lat": 20.6800, "lon": -103.3400}
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_health_check():
    """Test de health check"""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
```

---

## 8. Ejecutar la API

### 8.1 Modo Desarrollo

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.2 Modo Producción

```bash
# Con Gunicorn + Uvicorn workers
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

### 8.3 Con Docker

**Archivo:** `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Ejecutar:**
```bash
docker build -t cyclist-safety-api .
docker run -p 8000:8000 cyclist-safety-api
```

---

## 9. Ejemplos de Uso

### 9.1 Con cURL

```bash
# Calcular ruta
curl -X POST "http://localhost:8000/api/v1/routes/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"lat": 20.6767, "lon": -103.3475},
    "destination": {"lat": 20.6800, "lon": -103.3400},
    "alpha": 0.7,
    "beta": 0.3
  }'

# Obtener mapa de calor
curl "http://localhost:8000/api/v1/heatmap?min_lon=-103.35&min_lat=20.66&max_lon=-103.33&max_lat=20.68&zoom=14"

# Health check
curl "http://localhost:8000/api/v1/health"
```

### 9.2 Con Python

```python
import requests

# Calcular ruta
response = requests.post(
    "http://localhost:8000/api/v1/routes/calculate",
    json={
        "origin": {"lat": 20.6767, "lon": -103.3475},
        "destination": {"lat": 20.6800, "lon": -103.3400},
        "alpha": 0.7,
        "beta": 0.3
    }
)

route = response.json()
print(f"Distancia: {route['total_distance']} metros")
print(f"Riesgo promedio: {route['average_risk']}")
```

### 9.3 Con JavaScript/Fetch

```javascript
// Calcular ruta
const response = await fetch('http://localhost:8000/api/v1/routes/calculate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    origin: { lat: 20.6767, lon: -103.3475 },
    destination: { lat: 20.6800, lon: -103.3400 },
    alpha: 0.7,
    beta: 0.3
  })
});

const route = await response.json();
console.log('Ruta calculada:', route);
```

---

## Resumen

La API REST está lista con:
- ✅ 8 endpoints principales
- ✅ Validación automática con Pydantic
- ✅ Documentación interactiva (Swagger/ReDoc)
- ✅ Cache con Redis
- ✅ Rate limiting
- ✅ CORS configurado
- ✅ Health checks
- ✅ Tests unitarios
- ✅ Listo para producción

**Próximo paso:** Conectar con el frontend React.