# Cyclist Safety Routing System - Guadalajara, Jalisco Implementation Guide

## Location-Specific Overview

**Target City:** Guadalajara, Jalisco, México  
**Coordinates:** 20.6597° N, 103.3496° W  
**Metropolitan Area:** Zona Metropolitana de Guadalajara (ZMG)  
**Coverage Area:** Guadalajara, Zapopan, Tlaquepaque, Tonalá

---

## Guadalajara-Specific Data Sources

### 1. OpenStreetMap Data for Guadalajara

**Primary Coverage:**
- Guadalajara Centro
- Zapopan (including Andares, Plaza del Sol)
- Tlaquepaque
- Tonalá
- Periférico and major avenues

**OSM Data Quality in Guadalajara:**
- ✅ Good: Major roads, avenues, and highways
- ✅ Good: Commercial areas and downtown
- ⚠️ Moderate: Residential neighborhoods
- ⚠️ Limited: Bike lane infrastructure data (requires manual validation)

### 2. Local Government Data Sources

**Instituto de Información Estadística y Geográfica de Jalisco (IIEG):**
- Website: https://iieg.gob.mx/
- Data: Demographics, urban planning, infrastructure
- Format: Shapefiles, CSV, GeoJSON

**Secretaría de Movilidad del Estado de Jalisco:**
- Traffic accident reports
- Road infrastructure data
- Public transportation routes
- Bike lane locations (Vía RecreActiva)

**Gobierno de Guadalajara - Datos Abiertos:**
- Portal: https://datos.guadalajara.gob.mx/
- Available data:
  - Vialidades (road network)
  - Accidentes viales (traffic accidents)
  - Infraestructura ciclista (cycling infrastructure)
  - Semáforos (traffic lights)

### 3. Traffic and Accident Data

**INEGI (Instituto Nacional de Estadística y Geografía):**
- Accidentes de tránsito terrestre en zonas urbanas
- Dataset: https://www.inegi.org.mx/programas/accidentes/
- Coverage: Guadalajara metropolitan area
- Format: CSV, Excel
- Historical data: 2010-present

**Waze for Cities:**
- Real-time traffic data
- Incident reports
- Road closures
- API access for government partners

**Google Maps Traffic API:**
- Real-time traffic conditions
- Historical traffic patterns
- Travel time estimates

### 4. Cycling Infrastructure Data

**Vía RecreActiva Guadalajara:**
- Sunday cycling routes
- Temporary bike lanes
- Popular cycling corridors

**MiBici (Bike-sharing System):**
- Station locations
- Usage patterns
- Popular routes
- API: https://www.mibici.net/

**Colectivos Ciclistas:**
- Guadalajara en Bici
- Bicitekas Jalisco
- Community-reported dangerous areas

---

## Guadalajara-Specific Risk Factors

### High-Risk Areas Identified

1. **Major Avenues (High Traffic Volume):**
   - Av. López Mateos
   - Av. Vallarta
   - Calzada Independencia
   - Av. Américas
   - Periférico

2. **Dangerous Intersections:**
   - Glorieta Colón
   - Glorieta Chapalita
   - Minerva
   - Intersections without traffic lights in colonias

3. **Areas with Poor Infrastructure:**
   - Colonias without sidewalks
   - Streets with potholes (baches)
   - Areas without street lighting
   - Narrow streets in historic center

4. **High-Speed Corridors:**
   - Periférico Norte/Sur
   - Carretera a Chapala
   - Carretera a Nogales
   - Anillo Periférico

### Local Risk Factor Weights (Adjusted for Guadalajara)

```python
GUADALAJARA_RISK_FACTORS = {
    'traffic_volume': {
        'weight': 0.30,  # Higher due to aggressive driving culture
        'thresholds': {
            'low': 0.0-0.3,
            'medium': 0.3-0.7,
            'high': 0.7-1.0
        }
    },
    'speed_limit': {
        'weight': 0.25,
        'values': {
            '≤40 km/h': 0.1,
            '41-60 km/h': 0.4,
            '61-80 km/h': 0.7,
            '>80 km/h': 1.0
        }
    },
    'bike_infrastructure': {
        'weight': 0.20,
        'values': {
            'protected_lane': 0.1,
            'painted_lane': 0.4,
            'shared_road': 0.7,
            'no_infrastructure': 1.0
        }
    },
    'road_surface': {
        'weight': 0.10,  # Important in Guadalajara (baches)
        'values': {
            'excellent': 0.1,
            'good': 0.3,
            'poor': 0.7,
            'very_poor': 1.0
        }
    },
    'lighting': {
        'weight': 0.08,  # Safety concern at night
        'values': {
            'well_lit': 0.2,
            'moderate': 0.5,
            'poor': 0.9
        }
    },
    'accident_history': {
        'weight': 0.07,
        'calculation': 'accidents_per_km_per_year'
    }
}
```

---

## Data Collection Script for Guadalajara

### Step 1: Fetch Guadalajara OSM Data

```python
# backend/scripts/fetch_guadalajara_data.py
import osmnx as ox
import geopandas as gpd
import pickle
from datetime import datetime

def fetch_guadalajara_network():
    """
    Fetch road network for Guadalajara Metropolitan Area
    """
    print("Fetching Guadalajara road network...")
    
    # Define Guadalajara metropolitan area
    place_name = "Guadalajara, Jalisco, México"
    
    # Option 1: By place name
    G = ox.graph_from_place(place_name, network_type='bike')
    
    # Option 2: By bounding box (more precise)
    # north, south, east, west = 20.75, 20.60, -103.25, -103.45
    # G = ox.graph_from_bbox(north, south, east, west, network_type='bike')
    
    # Add edge attributes
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    # Save network
    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = f"../data/raw/guadalajara_network_{timestamp}.pkl"
    
    with open(output_file, 'wb') as f:
        pickle.dump(G, f)
    
    print(f"✓ Network saved: {output_file}")
    print(f"  Nodes: {len(G.nodes):,}")
    print(f"  Edges: {len(G.edges):,}")
    
    return G

def fetch_guadalajara_pois():
    """
    Fetch Points of Interest relevant for cyclist safety
    """
    print("\nFetching POIs...")
    
    place_name = "Guadalajara, Jalisco, México"
    
    # Schools (higher traffic during certain hours)
    schools = ox.geometries_from_place(
        place_name,
        tags={'amenity': 'school'}
    )
    
    # Hospitals (emergency vehicle traffic)
    hospitals = ox.geometries_from_place(
        place_name,
        tags={'amenity': 'hospital'}
    )
    
    # Markets (high pedestrian/vehicle traffic)
    markets = ox.geometries_from_place(
        place_name,
        tags={'amenity': 'marketplace'}
    )
    
    # Traffic lights
    traffic_signals = ox.geometries_from_place(
        place_name,
        tags={'highway': 'traffic_signals'}
    )
    
    print(f"✓ Schools: {len(schools)}")
    print(f"✓ Hospitals: {len(hospitals)}")
    print(f"✓ Markets: {len(markets)}")
    print(f"✓ Traffic signals: {len(traffic_signals)}")
    
    return {
        'schools': schools,
        'hospitals': hospitals,
        'markets': markets,
        'traffic_signals': traffic_signals
    }

def fetch_mibici_stations():
    """
    Fetch MiBici bike-sharing station locations
    """
    import requests
    
    print("\nFetching MiBici stations...")
    
    # MiBici API endpoint (if available)
    # Note: Check current API documentation
    url = "https://www.mibici.net/es/datos-abiertos/"
    
    # Alternative: Manual data from website
    # For now, we'll use OSM data
    place_name = "Guadalajara, Jalisco, México"
    
    try:
        bike_stations = ox.geometries_from_place(
            place_name,
            tags={'amenity': 'bicycle_rental'}
        )
        print(f"✓ MiBici stations found: {len(bike_stations)}")
        return bike_stations
    except:
        print("⚠ MiBici data not available in OSM")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("GUADALAJARA CYCLIST SAFETY DATA COLLECTION")
    print("=" * 60)
    
    # Fetch road network
    G = fetch_guadalajara_network()
    
    # Fetch POIs
    pois = fetch_guadalajara_pois()
    
    # Fetch MiBici stations
    mibici = fetch_mibici_stations()
    
    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)
```

### Step 2: Process INEGI Accident Data

```python
# backend/scripts/process_inegi_accidents.py
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def load_inegi_accident_data(filepath):
    """
    Load and process INEGI accident data for Guadalajara
    
    Expected columns:
    - ANIO (year)
    - MES (month)
    - ENTIDAD (state)
    - MUNICIPIO (municipality)
    - LATITUD (latitude)
    - LONGITUD (longitude)
    - TIPO_ACCIDENTE (accident type)
    - GRAVEDAD (severity)
    - CICLISTA_INVOLUCRADO (cyclist involved)
    """
    print("Loading INEGI accident data...")
    
    # Load data
    df = pd.read_csv(filepath, encoding='latin-1')
    
    # Filter for Jalisco (state code 14)
    df = df[df['ENTIDAD'] == 14]
    
    # Filter for Guadalajara metropolitan area municipalities
    gdl_municipalities = [
        39,  # Guadalajara
        120, # Zapopan
        97,  # Tlaquepaque
        101  # Tonalá
    ]
    df = df[df['MUNICIPIO'].isin(gdl_municipalities)]
    
    # Filter for cyclist-involved accidents
    df_cyclists = df[df['CICLISTA_INVOLUCRADO'] == 1].copy()
    
    # Create geometry
    df_cyclists['geometry'] = df_cyclists.apply(
        lambda row: Point(row['LONGITUD'], row['LATITUD']),
        axis=1
    )
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df_cyclists, geometry='geometry', crs='EPSG:4326')
    
    print(f"✓ Total accidents loaded: {len(df):,}")
    print(f"✓ Cyclist accidents: {len(gdf):,}")
    print(f"✓ Date range: {df['ANIO'].min()}-{df['ANIO'].max()}")
    
    return gdf

def aggregate_accidents_by_segment(gdf_accidents, G):
    """
    Map accidents to road segments in the graph
    """
    import networkx as nx
    from scipy.spatial import cKDTree
    
    print("\nMapping accidents to road segments...")
    
    # Get edge coordinates
    edge_coords = []
    edge_ids = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        if 'geometry' in data:
            # Use midpoint of edge
            coords = list(data['geometry'].coords)
            midpoint = coords[len(coords)//2]
            edge_coords.append(midpoint)
            edge_ids.append((u, v, key))
    
    # Build KD-tree for fast nearest neighbor search
    tree = cKDTree(edge_coords)
    
    # Find nearest edge for each accident
    accident_coords = [(point.x, point.y) for point in gdf_accidents.geometry]
    distances, indices = tree.query(accident_coords, k=1)
    
    # Count accidents per edge
    accident_counts = {}
    for idx in indices:
        edge_id = edge_ids[idx]
        accident_counts[edge_id] = accident_counts.get(edge_id, 0) + 1
    
    # Add to graph
    for u, v, key in G.edges(keys=True):
        edge_id = (u, v, key)
        G[u][v][key]['accident_count'] = accident_counts.get(edge_id, 0)
    
    print(f"✓ Accidents mapped to {len(accident_counts)} segments")
    
    return G

if __name__ == "__main__":
    # Example usage
    accident_file = "../data/raw/inegi_accidents_jalisco_2020_2023.csv"
    gdf = load_inegi_accident_data(accident_file)
    
    # Save processed data
    gdf.to_file("../data/processed/guadalajara_cyclist_accidents.geojson", driver='GeoJSON')
    print("\n✓ Processed data saved")
```

---

## Guadalajara-Specific Features

### 1. Via RecreActiva Integration

```python
# backend/app/services/via_recreactiva_service.py
from datetime import datetime

class ViaRecreActivaService:
    """
    Handle Via RecreActiva (Sunday cycling routes) special routing
    """
    
    RECREACTIVA_ROUTES = {
        'centro': {
            'active_days': ['sunday'],
            'hours': (8, 14),  # 8 AM - 2 PM
            'segments': [
                # List of OSM way IDs that are part of Via RecreActiva
            ]
        },
        'zapopan': {
            'active_days': ['sunday'],
            'hours': (8, 14),
            'segments': []
        }
    }
    
    def is_recreactiva_active(self, datetime_obj=None):
        """Check if Via RecreActiva is currently active"""
        if datetime_obj is None:
            datetime_obj = datetime.now()
        
        # Check if Sunday
        if datetime_obj.weekday() != 6:  # 6 = Sunday
            return False
        
        # Check time
        hour = datetime_obj.hour
        return 8 <= hour <= 14
    
    def adjust_risk_for_recreactiva(self, G, datetime_obj=None):
        """
        Reduce risk scores for Via RecreActiva routes when active
        """
        if not self.is_recreactiva_active(datetime_obj):
            return G
        
        # Reduce risk by 70% on RecreActiva routes
        for route_data in self.RECREACTIVA_ROUTES.values():
            for segment_id in route_data['segments']:
                # Find edge in graph and reduce risk
                # Implementation depends on how segments are stored
                pass
        
        return G
```

### 2. MiBici Station Integration

```python
# backend/app/services/mibici_service.py
import requests

class MiBiciService:
    """
    Integration with MiBici bike-sharing system
    """
    
    def get_nearby_stations(self, lat, lon, radius_km=1.0):
        """
        Find MiBici stations near a location
        """
        # Implementation using MiBici API or stored data
        pass
    
    def suggest_mibici_route(self, origin, destination):
        """
        Suggest route that includes MiBici stations
        """
        # Find nearest station to origin
        # Calculate route to destination
        # Find nearest station to destination
        pass
```

### 3. Local Traffic Patterns

```python
# backend/app/utils/guadalajara_traffic_patterns.py

GUADALAJARA_TRAFFIC_PATTERNS = {
    'rush_hours': {
        'morning': (7, 10),    # 7 AM - 10 AM
        'evening': (18, 21),   # 6 PM - 9 PM
        'risk_multiplier': 1.5
    },
    'high_traffic_days': {
        'monday': 1.2,
        'friday': 1.3,
        'saturday': 1.1
    },
    'special_events': {
        'fiestas_octubre': {
            'months': [10],
            'areas': ['centro', 'minerva'],
            'risk_multiplier': 1.8
        },
        'feria_libro': {
            'months': [11],
            'areas': ['expo_guadalajara'],
            'risk_multiplier': 1.4
        }
    }
}

def adjust_for_local_patterns(risk_score, datetime_obj, location):
    """
    Adjust risk score based on Guadalajara-specific patterns
    """
    hour = datetime_obj.hour
    day = datetime_obj.weekday()
    month = datetime_obj.month
    
    # Rush hour adjustment
    if (7 <= hour <= 10) or (18 <= hour <= 21):
        risk_score *= 1.5
    
    # Weekend adjustment (less traffic)
    if day in [5, 6]:  # Saturday, Sunday
        risk_score *= 0.8
    
    return min(risk_score, 1.0)
```

---

## Sample Routes for Testing

### Test Route 1: Centro Histórico to Zapopan
```python
test_routes = {
    'centro_to_zapopan': {
        'origin': (20.6767, -103.3475),  # Catedral
        'destination': (20.7206, -103.3897),  # Plaza Andares
        'expected_distance': 8.5,  # km
        'known_risks': ['Av. Vallarta', 'high traffic']
    },
    'tlaquepaque_to_centro': {
        'origin': (20.6401, -103.3125),  # Tlaquepaque Centro
        'destination': (20.6767, -103.3475),  # Catedral
        'expected_distance': 6.2,  # km
        'known_risks': ['Calzada Independencia']
    },
    'minerva_circuit': {
        'origin': (20.6738, -103.3925),  # Minerva
        'destination': (20.6738, -103.3925),  # Circular route
        'expected_distance': 5.0,  # km
        'known_risks': ['Av. López Mateos', 'Av. Américas']
    }
}
```

---

## Local Deployment Considerations

### Hosting Options in Mexico

1. **Cloud Providers with Mexico Data Centers:**
   - Google Cloud Platform (GCP) - Mexico City region
   - AWS - São Paulo (closest)
   - Microsoft Azure - Mexico Central

2. **Local Hosting:**
   - Universidad de Guadalajara servers
   - ITESO infrastructure
   - Local VPS providers

3. **CDN for Frontend:**
   - Cloudflare (has Mexico PoP)
   - Fastly
   - AWS CloudFront

### Language Considerations

```javascript
// Frontend localization
const translations = {
  es_MX: {
    'route.calculate': 'Calcular ruta',
    'route.safest': 'Ruta más segura',
    'route.fastest': 'Ruta más rápida',
    'risk.high': 'Riesgo alto',
    'risk.medium': 'Riesgo medio',
    'risk.low': 'Riesgo bajo',
    'alert.dangerous_segment': 'Segmento peligroso detectado',
    'alert.alternative_route': 'Ruta alternativa disponible',
    // ... more translations
  }
}
```

---

## Academic Partnerships in Guadalajara

### Potential Collaborators

1. **Universidad de Guadalajara (UdeG)**
   - Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI)
   - Departamento de Ciencias Computacionales
   - Contact: Research groups in AI and urban computing

2. **ITESO - Universidad Jesuita de Guadalajara**
   - Departamento de Electrónica, Sistemas e Informática
   - Proyectos de innovación social
   - Focus on sustainable mobility

3. **Tecnológico de Monterrey - Campus Guadalajara**
   - School of Engineering and Sciences
   - Smart Cities research groups

4. **Gobierno de Guadalajara**
   - Secretaría de Movilidad
   - Dirección de Innovación
   - Open data initiatives

### Data Sharing Agreements

- Request access to municipal accident databases
- Collaborate with Secretaría de Movilidad
- Partner with cycling advocacy groups
- Engage with MiBici for usage data

---

## Implementation Timeline for Guadalajara

### Month 1: Local Data Collection
- Week 1: Fetch OSM data for ZMG
- Week 2: Obtain INEGI accident data
- Week 3: Contact local government for additional data
- Week 4: Process and validate all data sources

### Month 2: Guadalajara-Specific Features
- Week 5-6: Implement local risk factors
- Week 7: Add Via RecreActiva integration
- Week 8: Integrate MiBici stations

### Month 3: ML Training with Local Data
- Week 9-10: Train models on Guadalajara data
- Week 11: Validate with local cycling groups
- Week 12: Fine-tune based on feedback

### Month 4: Testing and Deployment
- Week 13-14: Test with real Guadalajara routes
- Week 15: User testing with local cyclists
- Week 16: Deploy and present results

---

## Success Metrics for Guadalajara

### Quantitative Metrics
- Route safety improvement: 35%+ vs. Google Maps shortest route
- Coverage: 90%+ of ZMG urban area
- Response time: <500ms for route calculation
- Accuracy: 85%+ match with known dangerous areas

### Qualitative Metrics
- Validation by local cycling groups
- Adoption by Guadalajara en Bici community
- Recognition by municipal government
- Media coverage in local news

### Academic Metrics
- Publishable research paper
- Presentation at local conferences
- Potential for thesis/dissertation
- Contribution to open data ecosystem

---

## Next Steps

1. **Immediate Actions:**
   - Run OSM data fetch for Guadalajara
   - Download INEGI accident data
   - Contact Secretaría de Movilidad for data access
   - Join local cycling groups for feedback

2. **Week 1 Deliverables:**
   - Guadalajara road network graph
   - Accident data processed and mapped
   - Initial risk assessment for major routes
   - Documentation of data sources

3. **Validation Strategy:**
   - Compare with known dangerous intersections
   - Test routes used by local cyclists
   - Validate against Via RecreActiva routes
   - Cross-reference with news reports of accidents

---

## Resources Specific to Guadalajara

### Government Contacts
- Secretaría de Movilidad: movilidad@jalisco.gob.mx
- Datos Abiertos GDL: datos@guadalajara.gob.mx

### Cycling Organizations
- Guadalajara en Bici: @gdlenbi (Twitter)
- Bicitekas Jalisco
- Colectivo Ecologista Jalisco

### Data Sources
- INEGI: https://www.inegi.org.mx/
- IIEG Jalisco: https://iieg.gob.mx/
- Datos Abiertos GDL: https://datos.guadalajara.gob.mx/
- MiBici: https://www.mibici.net/

### Academic Resources
- UdeG Digital Library
- ITESO Research Repository
- Red de Movilidad Sustentable

---

## Conclusion

This Guadalajara-specific implementation guide provides all the necessary context, data sources, and local considerations for your cyclist safety routing system. The system will be tailored to the unique characteristics of Guadalajara's urban environment, traffic patterns, and cycling infrastructure.

**Key Advantages of Guadalajara Focus:**
- Access to local government data
- Partnership opportunities with universities
- Real-world validation with local cycling community
- Contribution to improving cyclist safety in your city
- Potential for municipal adoption and scaling

The 4-month timeline remains realistic with this localized approach, and the project will have greater impact by addressing specific local needs.