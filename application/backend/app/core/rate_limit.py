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
