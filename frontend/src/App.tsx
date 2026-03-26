import { useState, useCallback } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

/* ——— Types ——— */
interface CityConfig {
  name: string
  center: [number, number]
  zoom: number
}

interface RouteResult {
  distance_km: number
  time_min: number
  risk_avg: number
  risk_label: string
  segments: [number, number][][]
  risk_scores: number[]
  warnings: string[]
}

/* ——— City Configs ——— */
const CITIES: Record<string, CityConfig> = {
  guadalajara: { name: 'Guadalajara', center: [20.6597, -103.3496], zoom: 13 },
  cdmx: { name: 'CDMX', center: [19.4326, -99.1332], zoom: 12 },
  merida: { name: 'Mérida', center: [20.9674, -89.6237], zoom: 13 },
}

/* ——— Mock route generator ——— */
function generateMockRoute(
  origin: [number, number],
  dest: [number, number],
  mode: string
): RouteResult {
  const numPoints = 8 + Math.floor(Math.random() * 6)
  const segments: [number, number][][] = []
  const riskScores: number[] = []
  const warnings: string[] = []

  for (let i = 0; i < numPoints - 1; i++) {
    const t1 = i / (numPoints - 1)
    const t2 = (i + 1) / (numPoints - 1)
    const jitter = () => (Math.random() - 0.5) * 0.008

    const p1: [number, number] = [
      origin[0] + (dest[0] - origin[0]) * t1 + jitter(),
      origin[1] + (dest[1] - origin[1]) * t1 + jitter(),
    ]
    const p2: [number, number] = [
      origin[0] + (dest[0] - origin[0]) * t2 + jitter(),
      origin[1] + (dest[1] - origin[1]) * t2 + jitter(),
    ]

    segments.push([p1, p2])

    let risk: number
    if (mode === 'safe') {
      risk = 0.05 + Math.random() * 0.35
    } else if (mode === 'fast') {
      risk = 0.2 + Math.random() * 0.7
    } else {
      risk = 0.1 + Math.random() * 0.5
    }
    riskScores.push(risk)
  }

  const avgRisk = riskScores.reduce((a, b) => a + b, 0) / riskScores.length
  const distFactor = mode === 'safe' ? 1.35 : mode === 'fast' ? 0.95 : 1.1

  const baseDist =
    Math.sqrt(
      Math.pow((dest[0] - origin[0]) * 111, 2) +
      Math.pow((dest[1] - origin[1]) * 85, 2)
    ) * distFactor

  const distance_km = Math.max(0.5, baseDist * (0.9 + Math.random() * 0.3))
  const time_min = distance_km * (mode === 'fast' ? 3.5 : mode === 'safe' ? 5.5 : 4.2)

  const highRiskSegments = riskScores.filter(r => r > 0.6).length
  if (highRiskSegments > 0) {
    warnings.push(`⚠️ ${highRiskSegments} segmento(s) con riesgo alto detectados`)
  }
  if (mode === 'fast') {
    warnings.push('⚡ Esta ruta prioriza rapidez sobre seguridad')
  }

  let risk_label: string
  if (avgRisk < 0.3) risk_label = 'Bajo'
  else if (avgRisk < 0.6) risk_label = 'Medio'
  else risk_label = 'Alto'

  return {
    distance_km: +distance_km.toFixed(2),
    time_min: +time_min.toFixed(0),
    risk_avg: +avgRisk.toFixed(2),
    risk_label,
    segments,
    risk_scores: riskScores,
    warnings,
  }
}

function riskColor(score: number): string {
  if (score < 0.3) return '#22c55e'
  if (score < 0.6) return '#f59e0b'
  return '#ef4444'
}

/* ——— Custom Marker Icons ——— */
const originIcon = new L.DivIcon({
  html: '<div style="width:18px;height:18px;border-radius:50%;background:#22c55e;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>',
  className: '',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

const destIcon = new L.DivIcon({
  html: '<div style="width:18px;height:18px;border-radius:50%;background:#ef4444;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>',
  className: '',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

/* ——— Map Click Handler ——— */
function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

/* ——— Main App ——— */
export default function App() {
  const [city, setCity] = useState('guadalajara')
  const [mode, setMode] = useState<'safe' | 'balanced' | 'fast'>('safe')
  const [alpha, setAlpha] = useState(0.7)

  const [originLat, setOriginLat] = useState('')
  const [originLon, setOriginLon] = useState('')
  const [destLat, setDestLat] = useState('')
  const [destLon, setDestLon] = useState('')

  const [clickTarget, setClickTarget] = useState<'origin' | 'dest'>('origin')
  const [route, setRoute] = useState<RouteResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [mapKey, setMapKey] = useState(0)

  const cityConfig = CITIES[city]

  const handleCityChange = useCallback((newCity: string) => {
    setCity(newCity)
    setRoute(null)
    setOriginLat('')
    setOriginLon('')
    setDestLat('')
    setDestLon('')
    setMapKey(k => k + 1)
  }, [])

  const handleMapClick = useCallback(
    (lat: number, lng: number) => {
      if (clickTarget === 'origin') {
        setOriginLat(lat.toFixed(5))
        setOriginLon(lng.toFixed(5))
        setClickTarget('dest')
      } else {
        setDestLat(lat.toFixed(5))
        setDestLon(lng.toFixed(5))
        setClickTarget('origin')
      }
    },
    [clickTarget],
  )

  const handleCalculate = useCallback(() => {
    const oLat = parseFloat(originLat)
    const oLon = parseFloat(originLon)
    const dLat = parseFloat(destLat)
    const dLon = parseFloat(destLon)

    if (isNaN(oLat) || isNaN(oLon) || isNaN(dLat) || isNaN(dLon)) return

    setLoading(true)
    setTimeout(() => {
      const result = generateMockRoute([oLat, oLon], [dLat, dLon], mode)
      setRoute(result)
      setLoading(false)
    }, 800)
  }, [originLat, originLon, destLat, destLon, mode])

  const handleModeChange = (m: 'safe' | 'balanced' | 'fast') => {
    setMode(m)
    if (m === 'safe') setAlpha(0.8)
    else if (m === 'balanced') setAlpha(0.5)
    else setAlpha(0.2)
  }

  const canCalculate = originLat && originLon && destLat && destLon && !loading

  const riskClass = route ? (route.risk_avg < 0.3 ? 'risk-low' : route.risk_avg < 0.6 ? 'risk-med' : 'risk-high') : ''

  return (
    <div className="app-layout">
      {/* ——— SIDEBAR ——— */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>
            <span className="icon">🚴</span>
            Rutas Seguras para Ciclistas
          </h1>
          <p>Sistema inteligente de enrutamiento con IA</p>
        </div>

        <div className="sidebar-content">
          {/* City Selector */}
          <div className="city-selector">
            {Object.entries(CITIES).map(([id, cfg]) => (
              <button
                key={id}
                className={`city-btn ${city === id ? 'active' : ''}`}
                onClick={() => handleCityChange(id)}
              >
                {cfg.name}
              </button>
            ))}
          </div>

          {/* Origin / Destination */}
          <div className="card">
            <div className="card-title">📍 Origen y Destino</div>
            <div className="input-group">
              <div className="coord-row">
                <div className="coord-dot origin" />
                <div className="coord-inputs">
                  <input
                    className="coord-input"
                    type="text"
                    placeholder="Latitud"
                    value={originLat}
                    onChange={e => setOriginLat(e.target.value)}
                    onFocus={() => setClickTarget('origin')}
                  />
                  <input
                    className="coord-input"
                    type="text"
                    placeholder="Longitud"
                    value={originLon}
                    onChange={e => setOriginLon(e.target.value)}
                    onFocus={() => setClickTarget('origin')}
                  />
                </div>
              </div>
              <div className="connector-line" />
              <div className="coord-row">
                <div className="coord-dot dest" />
                <div className="coord-inputs">
                  <input
                    className="coord-input"
                    type="text"
                    placeholder="Latitud"
                    value={destLat}
                    onChange={e => setDestLat(e.target.value)}
                    onFocus={() => setClickTarget('dest')}
                  />
                  <input
                    className="coord-input"
                    type="text"
                    placeholder="Longitud"
                    value={destLon}
                    onChange={e => setDestLon(e.target.value)}
                    onFocus={() => setClickTarget('dest')}
                  />
                </div>
              </div>
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 8 }}>
              💡 Haz clic en el mapa para seleccionar {clickTarget === 'origin' ? 'origen' : 'destino'}
            </p>
          </div>

          {/* Route Mode */}
          <div className="card">
            <div className="card-title">🛣️ Modo de Ruta</div>
            <div className="route-modes">
              <button
                className={`mode-btn safe ${mode === 'safe' ? 'active' : ''}`}
                onClick={() => handleModeChange('safe')}
              >
                <span className="mode-icon">🛡️</span>
                Segura
              </button>
              <button
                className={`mode-btn balanced ${mode === 'balanced' ? 'active' : ''}`}
                onClick={() => handleModeChange('balanced')}
              >
                <span className="mode-icon">⚖️</span>
                Balanceada
              </button>
              <button
                className={`mode-btn fast ${mode === 'fast' ? 'active' : ''}`}
                onClick={() => handleModeChange('fast')}
              >
                <span className="mode-icon">⚡</span>
                Rápida
              </button>
            </div>
          </div>

          {/* Alpha Slider */}
          <div className="card">
            <div className="card-title">⚙️ Parámetros α/β</div>
            <div className="slider-container">
              <div className="slider-header">
                <span className="slider-label">🛡️ Seguridad (α)</span>
                <span className="slider-value">{(alpha * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                className="slider"
                min="0"
                max="1"
                step="0.05"
                value={alpha}
                onChange={e => setAlpha(parseFloat(e.target.value))}
              />
              <div className="slider-header" style={{ marginTop: 8 }}>
                <span className="slider-label">⚡ Distancia (β)</span>
                <span className="slider-value">{((1 - alpha) * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {/* Calculate */}
          <button
            className="calc-btn"
            disabled={!canCalculate}
            onClick={handleCalculate}
          >
            {loading ? (
              <>
                <div className="spinner" />
                Calculando...
              </>
            ) : (
              <>🗺️ Calcular Ruta</>
            )}
          </button>

          {/* Results */}
          {route && (
            <div className="card results-card">
              <div className="card-title">📊 Resultados</div>
              <div className="results-grid">
                <div className="result-item">
                  <div className="value">{route.distance_km}</div>
                  <div className="label">km</div>
                </div>
                <div className="result-item">
                  <div className="value">{route.time_min}</div>
                  <div className="label">min</div>
                </div>
                <div className={`result-item ${riskClass}`}>
                  <div className="value">{route.risk_label}</div>
                  <div className="label">Riesgo ({(route.risk_avg * 100).toFixed(0)}%)</div>
                </div>
              </div>
              {route.warnings.length > 0 && (
                <div className="warnings">
                  {route.warnings.map((w, i) => (
                    <div className="warning-item" key={i}>
                      {w}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* ——— MAP ——— */}
      <div className="map-container">
        <div className="map-status">
          <div className="status-dot" />
          {cityConfig.name} — Haz clic para seleccionar{' '}
          {clickTarget === 'origin' ? 'origen 🟢' : 'destino 🔴'}
        </div>

        <MapContainer
          key={mapKey}
          center={cityConfig.center}
          zoom={cityConfig.zoom}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onMapClick={handleMapClick} />

          {/* Origin Marker */}
          {originLat && originLon && (
            <Marker
              position={[parseFloat(originLat), parseFloat(originLon)]}
              icon={originIcon}
            >
              <Popup>
                <strong>Origen</strong><br />
                {parseFloat(originLat).toFixed(4)}, {parseFloat(originLon).toFixed(4)}
              </Popup>
            </Marker>
          )}

          {/* Destination Marker */}
          {destLat && destLon && (
            <Marker
              position={[parseFloat(destLat), parseFloat(destLon)]}
              icon={destIcon}
            >
              <Popup>
                <strong>Destino</strong><br />
                {parseFloat(destLat).toFixed(4)}, {parseFloat(destLon).toFixed(4)}
              </Popup>
            </Marker>
          )}

          {/* Route segments colored by risk */}
          {route &&
            route.segments.map((seg, i) => (
              <Polyline
                key={i}
                positions={seg}
                pathOptions={{
                  color: riskColor(route.risk_scores[i]),
                  weight: 5,
                  opacity: 0.85,
                }}
              >
                <Popup>
                  <strong>Segmento {i + 1}</strong><br />
                  Riesgo: {(route.risk_scores[i] * 100).toFixed(0)}%<br />
                  Categoría: {route.risk_scores[i] < 0.3 ? 'Bajo' : route.risk_scores[i] < 0.6 ? 'Medio' : 'Alto'}
                </Popup>
              </Polyline>
            ))}
        </MapContainer>

        {/* Legend */}
        <div className="map-legend">
          <h4>Nivel de Riesgo</h4>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#22c55e' }} />
              Bajo (&lt;30%)
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#f59e0b' }} />
              Medio (30–60%)
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#ef4444' }} />
              Alto (&gt;60%)
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
