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
