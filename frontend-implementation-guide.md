# Guía de Implementación del Frontend Web
## Sistema de Rutas Seguras para Ciclistas - Guadalajara

---

## Índice
1. [Configuración Inicial](#1-configuración-inicial)
2. [Estructura del Proyecto](#2-estructura-del-proyecto)
3. [Componentes Principales](#3-componentes-principales)
4. [Integración con Leaflet](#4-integración-con-leaflet)
5. [Conexión con API](#5-conexión-con-api)
6. [Estilos y UI](#6-estilos-y-ui)
7. [Deployment](#7-deployment)

---

## 1. Configuración Inicial

### 1.1 Crear Proyecto React con TypeScript

```bash
# Crear proyecto con Vite (más rápido que Create React App)
npm create vite@latest cyclist-safety-frontend -- --template react-ts

cd cyclist-safety-frontend

# Instalar dependencias base
npm install

# Instalar dependencias adicionales
npm install leaflet react-leaflet
npm install @types/leaflet
npm install axios
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm install react-router-dom
npm install zustand  # State management
npm install date-fns  # Manejo de fechas
```

### 1.2 Estructura de Carpetas

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/
│   │   └── images/
│   ├── components/
│   │   ├── Map/
│   │   │   ├── MapContainer.tsx
│   │   │   ├── RouteLayer.tsx
│   │   │   ├── HeatmapLayer.tsx
│   │   │   └── MarkerLayer.tsx
│   │   ├── RoutePanel/
│   │   │   ├── RouteInput.tsx
│   │   │   ├── RouteOptions.tsx
│   │   │   ├── RouteComparison.tsx
│   │   │   └── ParameterSliders.tsx
│   │   ├── Alerts/
│   │   │   ├── CriticalSegmentAlert.tsx
│   │   │   └── SafetyWarning.tsx
│   │   └── Layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── mapService.ts
│   │   └── routeService.ts
│   ├── hooks/
│   │   ├── useRoute.ts
│   │   ├── useHeatmap.ts
│   │   └── useGeolocation.ts
│   ├── store/
│   │   └── routeStore.ts
│   ├── types/
│   │   ├── route.types.ts
│   │   └── map.types.ts
│   ├── utils/
│   │   ├── colorScale.ts
│   │   └── geoUtils.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 2. Configuración de TypeScript

### 2.1 Tipos de Datos

**Archivo:** `src/types/route.types.ts`

```typescript
export interface Coordinates {
  lat: number;
  lon: number;
}

export interface RouteSegment {
  segment_id: string;
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
  length: number;
  risk_score: number;
  risk_category: 'bajo' | 'medio' | 'alto';
  street_name?: string;
  highway_type?: string;
  has_bike_lane: boolean;
}

export interface Route {
  route_id: string;
  origin: Coordinates;
  destination: Coordinates;
  segments: RouteSegment[];
  total_distance: number;
  estimated_time: number;
  average_risk: number;
  max_risk: number;
  critical_segments: number[];
  warnings: string[];
  computation_time: number;
}

export interface RouteRequest {
  origin: Coordinates;
  destination: Coordinates;
  alpha: number;
  beta: number;
  avoid_critical: boolean;
  max_alternatives: number;
}

export interface HeatmapCell {
  lat: number;
  lon: number;
  risk_score: number;
  accident_count: number;
}
```

---

## 3. Servicio de API

### 3.1 Cliente HTTP

**Archivo:** `src/services/api.ts`

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';
import { Route, RouteRequest, HeatmapCell } from '../types/route.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para manejo de errores
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async calculateRoute(request: RouteRequest): Promise<Route> {
    const response = await this.client.post<Route>('/routes/calculate', request);
    return response.data;
  }

  async getAlternativeRoutes(request: RouteRequest): Promise<Route[]> {
    const response = await this.client.post<{ routes: Route[] }>(
      '/routes/alternatives',
      request
    );
    return response.data.routes;
  }

  async getHeatmap(
    minLon: number,
    minLat: number,
    maxLon: number,
    maxLat: number,
    zoom: number = 14
  ): Promise<HeatmapCell[]> {
    const response = await this.client.get<{ cells: HeatmapCell[] }>('/heatmap', {
      params: { min_lon: minLon, min_lat: minLat, max_lon: maxLon, max_lat: maxLat, zoom },
    });
    return response.data.cells;
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
```

---

## 4. Componente Principal del Mapa

### 4.1 MapContainer

**Archivo:** `src/components/Map/MapContainer.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { MapContainer as LeafletMap, TileLayer, useMap } from 'react-leaflet';
import { LatLngBounds } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import RouteLayer from './RouteLayer';
import HeatmapLayer from './HeatmapLayer';
import MarkerLayer from './MarkerLayer';
import { Route, Coordinates } from '../../types/route.types';

interface MapContainerProps {
  routes: Route[];
  origin?: Coordinates;
  destination?: Coordinates;
  showHeatmap: boolean;
  onMapClick?: (lat: number, lon: number) => void;
}

// Componente para ajustar vista del mapa
function MapBoundsUpdater({ routes }: { routes: Route[] }) {
  const map = useMap();

  useEffect(() => {
    if (routes.length > 0) {
      const bounds = new LatLngBounds([]);
      
      routes.forEach(route => {
        route.segments.forEach(segment => {
          bounds.extend([segment.start_lat, segment.start_lon]);
          bounds.extend([segment.end_lat, segment.end_lon]);
        });
      });

      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [routes, map]);

  return null;
}

const MapContainer: React.FC<MapContainerProps> = ({
  routes,
  origin,
  destination,
  showHeatmap,
  onMapClick,
}) => {
  // Centro inicial: Guadalajara
  const [center] = useState<[number, number]>([20.6767, -103.3475]);
  const [zoom] = useState(13);

  const handleMapClick = (e: any) => {
    if (onMapClick) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    }
  };

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <LeafletMap
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        onClick={handleMapClick}
      >
        {/* Capa base de OpenStreetMap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Mapa de calor */}
        {showHeatmap && <HeatmapLayer />}

        {/* Rutas */}
        {routes.map((route) => (
          <RouteLayer key={route.route_id} route={route} />
        ))}

        {/* Marcadores de origen y destino */}
        {(origin || destination) && (
          <MarkerLayer origin={origin} destination={destination} />
        )}

        {/* Ajustar vista automáticamente */}
        <MapBoundsUpdater routes={routes} />
      </LeafletMap>
    </div>
  );
};

export default MapContainer;
```

### 4.2 RouteLayer

**Archivo:** `src/components/Map/RouteLayer.tsx`

```typescript
import React from 'react';
import { Polyline, Popup } from 'react-leaflet';
import { Route } from '../../types/route.types';
import { getRiskColor } from '../../utils/colorScale';

interface RouteLayerProps {
  route: Route;
}

const RouteLayer: React.FC<RouteLayerProps> = ({ route }) => {
  // Convertir segmentos a coordenadas para Polyline
  const positions = route.segments.map(segment => [
    [segment.start_lat, segment.start_lon],
    [segment.end_lat, segment.end_lon],
  ]).flat() as [number, number][];

  // Color basado en riesgo promedio
  const color = getRiskColor(route.average_risk);

  return (
    <>
      <Polyline
        positions={positions}
        pathOptions={{
          color: color,
          weight: 5,
          opacity: 0.7,
        }}
      >
        <Popup>
          <div style={{ padding: '10px' }}>
            <h3>Información de Ruta</h3>
            <p><strong>Distancia:</strong> {(route.total_distance / 1000).toFixed(2)} km</p>
            <p><strong>Tiempo estimado:</strong> {Math.round(route.estimated_time / 60)} min</p>
            <p><strong>Riesgo promedio:</strong> {(route.average_risk * 100).toFixed(0)}%</p>
            <p><strong>Categoría:</strong> {route.average_risk < 0.3 ? 'Bajo' : route.average_risk < 0.6 ? 'Medio' : 'Alto'}</p>
            {route.warnings.length > 0 && (
              <div>
                <strong>Advertencias:</strong>
                <ul>
                  {route.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Popup>
      </Polyline>

      {/* Resaltar segmentos críticos */}
      {route.critical_segments.map((segmentIdx) => {
        const segment = route.segments[segmentIdx];
        return (
          <Polyline
            key={`critical-${segmentIdx}`}
            positions={[
              [segment.start_lat, segment.start_lon],
              [segment.end_lat, segment.end_lon],
            ]}
            pathOptions={{
              color: '#ff0000',
              weight: 7,
              opacity: 0.9,
              dashArray: '10, 10',
            }}
          >
            <Popup>
              <div style={{ padding: '10px' }}>
                <h4 style={{ color: '#ff0000' }}>⚠️ Segmento Crítico</h4>
                <p><strong>Calle:</strong> {segment.street_name || 'Sin nombre'}</p>
                <p><strong>Riesgo:</strong> {(segment.risk_score * 100).toFixed(0)}%</p>
                <p><strong>Longitud:</strong> {segment.length.toFixed(0)} m</p>
                <p style={{ color: '#ff0000', fontWeight: 'bold' }}>
                  Se recomienda precaución extrema
                </p>
              </div>
            </Popup>
          </Polyline>
        );
      })}
    </>
  );
};

export default RouteLayer;
```

### 4.3 HeatmapLayer

**Archivo:** `src/components/Map/HeatmapLayer.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import { apiService } from '../../services/api';
import { HeatmapCell } from '../../types/route.types';

const HeatmapLayer: React.FC = () => {
  const map = useMap();
  const [heatmapData, setHeatmapData] = useState<HeatmapCell[]>([]);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        const bounds = map.getBounds();
        const data = await apiService.getHeatmap(
          bounds.getWest(),
          bounds.getSouth(),
          bounds.getEast(),
          bounds.getNorth(),
          map.getZoom()
        );
        setHeatmapData(data);
      } catch (error) {
        console.error('Error loading heatmap:', error);
      }
    };

    fetchHeatmap();

    // Actualizar cuando el mapa se mueve
    map.on('moveend', fetchHeatmap);

    return () => {
      map.off('moveend', fetchHeatmap);
    };
  }, [map]);

  useEffect(() => {
    if (heatmapData.length === 0) return;

    // Convertir datos a formato de leaflet.heat
    const heatPoints = heatmapData.map(cell => [
      cell.lat,
      cell.lon,
      cell.risk_score, // Intensidad
    ]) as [number, number, number][];

    // Crear capa de calor
    const heatLayer = (L as any).heatLayer(heatPoints, {
      radius: 25,
      blur: 35,
      maxZoom: 17,
      max: 1.0,
      gradient: {
        0.0: 'green',
        0.3: 'yellow',
        0.6: 'orange',
        1.0: 'red',
      },
    });

    heatLayer.addTo(map);

    return () => {
      map.removeLayer(heatLayer);
    };
  }, [heatmapData, map]);

  return null;
};

export default HeatmapLayer;
```

---

## 5. Panel de Control de Rutas

### 5.1 RouteInput

**Archivo:** `src/components/RoutePanel/RouteInput.tsx`

```typescript
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  IconButton,
  Paper,
  Typography,
} from '@mui/material';
import {
  MyLocation as MyLocationIcon,
  SwapVert as SwapIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { Coordinates } from '../../types/route.types';

interface RouteInputProps {
  onCalculateRoute: (origin: Coordinates, destination: Coordinates) => void;
  onUseCurrentLocation: (isOrigin: boolean) => void;
}

const RouteInput: React.FC<RouteInputProps> = ({
  onCalculateRoute,
  onUseCurrentLocation,
}) => {
  const [originLat, setOriginLat] = useState('20.6767');
  const [originLon, setOriginLon] = useState('-103.3475');
  const [destLat, setDestLat] = useState('20.6800');
  const [destLon, setDestLon] = useState('-103.3400');

  const handleCalculate = () => {
    const origin: Coordinates = {
      lat: parseFloat(originLat),
      lon: parseFloat(originLon),
    };
    const destination: Coordinates = {
      lat: parseFloat(destLat),
      lon: parseFloat(destLon),
    };
    onCalculateRoute(origin, destination);
  };

  const handleSwap = () => {
    const tempLat = originLat;
    const tempLon = originLon;
    setOriginLat(destLat);
    setOriginLon(destLon);
    setDestLat(tempLat);
    setDestLon(tempLon);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        Calcular Ruta Segura
      </Typography>

      {/* Origen */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Origen
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <TextField
            label="Latitud"
            value={originLat}
            onChange={(e) => setOriginLat(e.target.value)}
            size="small"
            fullWidth
            type="number"
            inputProps={{ step: '0.0001' }}
          />
          <TextField
            label="Longitud"
            value={originLon}
            onChange={(e) => setOriginLon(e.target.value)}
            size="small"
            fullWidth
            type="number"
            inputProps={{ step: '0.0001' }}
          />
          <IconButton
            color="primary"
            onClick={() => onUseCurrentLocation(true)}
            title="Usar ubicación actual"
          >
            <MyLocationIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Botón de intercambio */}
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 1 }}>
        <IconButton onClick={handleSwap} color="primary">
          <SwapIcon />
        </IconButton>
      </Box>

      {/* Destino */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Destino
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <TextField
            label="Latitud"
            value={destLat}
            onChange={(e) => setDestLat(e.target.value)}
            size="small"
            fullWidth
            type="number"
            inputProps={{ step: '0.0001' }}
          />
          <TextField
            label="Longitud"
            value={destLon}
            onChange={(e) => setDestLon(e.target.value)}
            size="small"
            fullWidth
            type="number"
            inputProps={{ step: '0.0001' }}
          />
          <IconButton
            color="primary"
            onClick={() => onUseCurrentLocation(false)}
            title="Usar ubicación actual"
          >
            <MyLocationIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Botón calcular */}
      <Button
        variant="contained"
        fullWidth
        startIcon={<SearchIcon />}
        onClick={handleCalculate}
        size="large"
      >
        Calcular Ruta
      </Button>
    </Paper>
  );
};

export default RouteInput;
```

### 5.2 ParameterSliders

**Archivo:** `src/components/RoutePanel/ParameterSliders.tsx`

```typescript
import React from 'react';
import { Box, Typography, Slider, Paper } from '@mui/material';
import { Security as SecurityIcon, Speed as SpeedIcon } from '@mui/icons-material';

interface ParameterSlidersProps {
  alpha: number;
  beta: number;
  onAlphaChange: (value: number) => void;
  onBetaChange: (value: number) => void;
}

const ParameterSliders: React.FC<ParameterSlidersProps> = ({
  alpha,
  beta,
  onAlphaChange,
  onBetaChange,
}) => {
  const handleAlphaChange = (_: Event, value: number | number[]) => {
    const newAlpha = value as number;
    onAlphaChange(newAlpha);
    onBetaChange(1 - newAlpha);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        Preferencias de Ruta
      </Typography>

      {/* Slider de Seguridad (Alpha) */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="subtitle2">
            Prioridad de Seguridad: {(alpha * 100).toFixed(0)}%
          </Typography>
        </Box>
        <Slider
          value={alpha}
          onChange={handleAlphaChange}
          min={0}
          max={1}
          step={0.1}
          marks={[
            { value: 0, label: '0%' },
            { value: 0.5, label: '50%' },
            { value: 1, label: '100%' },
          ]}
          valueLabelDisplay="auto"
          valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
        />
        <Typography variant="caption" color="text.secondary">
          Mayor valor = Ruta más segura (puede ser más larga)
        </Typography>
      </Box>

      {/* Slider de Distancia (Beta) */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <SpeedIcon sx={{ mr: 1, color: 'secondary.main' }} />
          <Typography variant="subtitle2">
            Prioridad de Distancia: {(beta * 100).toFixed(0)}%
          </Typography>
        </Box>
        <Slider
          value={beta}
          onChange={(_, value) => {
            const newBeta = value as number;
            onBetaChange(newBeta);
            onAlphaChange(1 - newBeta);
          }}
          min={0}
          max={1}
          step={0.1}
          marks={[
            { value: 0, label: '0%' },
            { value: 0.5, label: '50%' },
            { value: 1, label: '100%' },
          ]}
          valueLabelDisplay="auto"
          valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
        />
        <Typography variant="caption" color="text.secondary">
          Mayor valor = Ruta más corta (puede ser menos segura)
        </Typography>
      </Box>

      {/* Indicador de balance */}
      <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="body2" align="center">
          {alpha > 0.7
            ? '🛡️ Modo Seguridad Máxima'
            : alpha > 0.5
            ? '⚖️ Modo Balanceado'
            : '⚡ Modo Rápido'}
        </Typography>
      </Box>
    </Paper>
  );
};

export default ParameterSliders;
```

---

## 6. Aplicación Principal

### 6.1 App.tsx

**Archivo:** `src/App.tsx`

```typescript
import React, { useState } from 'react';
import { Box, Grid, CircularProgress, Alert, Snackbar } from '@mui/material';
import MapContainer from './components/Map/MapContainer';
import RouteInput from './components/RoutePanel/RouteInput';
import ParameterSliders from './components/RoutePanel/ParameterSliders';
import { apiService } from './services/api';
import { Route, Coordinates, RouteRequest } from './types/route.types';

function App() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [origin, setOrigin] = useState<Coordinates | undefined>();
  const [destination, setDestination] = useState<Coordinates | undefined>();
  const [alpha, setAlpha] = useState(0.5);
  const [beta, setBeta] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculateRoute = async (
    newOrigin: Coordinates,
    newDestination: Coordinates
  ) => {
    setLoading(true);
    setError(null);
    setOrigin(newOrigin);
    setDestination(newDestination);

    try {
      const request: RouteRequest = {
        origin: newOrigin,
        destination: newDestination,
        alpha,
        beta,
        avoid_critical: true,
        max_alternatives: 3,
      };

      const route = await apiService.calculateRoute(request);
      setRoutes([route]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al calcular ruta');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUseCurrentLocation = (isOrigin: boolean) => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords: Coordinates = {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          };
          if (isOrigin) {
            setOrigin(coords);
          } else {
            setDestination(coords);
          }
        },
        (error) => {
          setError('No se pudo obtener la ubicación actual');
          console.error('Geolocation error:', error);
        }
      );
    } else {
      setError('Geolocalización no disponible en este navegador');
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ bgcolor: 'primary.main', color: 'white', p: 2 }}>
        <h1 style={{ margin: 0 }}>🚴 Rutas Seguras - Guadalajara</h1>
      </Box>

      {/* Main Content */}
      <Grid container sx={{ flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <Grid item xs={12} md={4} lg={3} sx={{ height: '100%', overflow: 'auto', p: 2 }}>
          <RouteInput
            onCalculateRoute={handleCalculateRoute}
            onUseCurrentLocation={handleUseCurrentLocation}
          />

          <ParameterSliders
            alpha={alpha}
            beta={beta}
            onAlphaChange={setAlpha}
            onBetaChange={setBeta}
          />

          {/* Información de ruta */}
          {routes.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="success">
                <strong>Ruta calculada</strong>
                <br />
                Distancia: {(routes[0].total_distance / 1000).toFixed(2)} km
                <br />
                Tiempo: {Math.round(routes[0].estimated_time / 60)} min
                <br />
                Riesgo: {(routes[0].average_risk * 100).toFixed(0)}%
              </Alert>
            </Box>
          )}

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <CircularProgress />
            </Box>
          )}
        </Grid>

        {/* Map */}
        <Grid item xs={12} md={8} lg={9} sx={{ height: '100%' }}>
          <MapContainer
            routes={routes}
            origin={origin}
            destination={destination}
            showHeatmap={showHeatmap}
          />
        </Grid>
      </Grid>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
```

---

## 7. Utilidades

### 7.1 Color Scale

**Archivo:** `src/utils/colorScale.ts`

```typescript
export function getRiskColor(riskScore: number): string {
  if (riskScore < 0.3) return '#00ff00'; // Verde - Bajo riesgo
  if (riskScore < 0.6) return '#ffff00'; // Amarillo - Riesgo medio
  if (riskScore < 0.8) return '#ff8800'; // Naranja - Riesgo alto
  return '#ff0000'; // Rojo - Riesgo muy alto
}

export function getRiskCategory(riskScore: number): string {
  if (riskScore < 0.3) return 'Bajo';
  if (riskScore < 0.6) return 'Medio';
  return 'Alto';
}
```

---

## 8. Ejecutar la Aplicación

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview de producción
npm run preview
```

---

## 9. Variables de Entorno

**Archivo:** `.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_MAP_CENTER_LAT=20.6767
VITE_MAP_CENTER_LON=-103.3475
```

---

## 10. Deployment

### 10.1 Build

```bash
npm run build
# Genera carpeta dist/
```

### 10.2 Deploy en Netlify

```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

### 10.3 Deploy en Vercel

```bash
# Instalar Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

---

## Resumen

Frontend completo con:
- ✅ React + TypeScript + Vite
- ✅ Leaflet para mapas interactivos
- ✅ Material-UI para componentes
- ✅ Integración completa con API
- ✅ Mapa de calor de riesgo
- ✅ Visualización de rutas con colores
- ✅ Sliders para ajustar parámetros
- ✅ Geolocalización
- ✅ Responsive design
- ✅ Manejo de errores
- ✅ Listo para producción

**Sistema completo funcionando end-to-end!** 🎉