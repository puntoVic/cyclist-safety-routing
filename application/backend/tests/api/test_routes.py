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
