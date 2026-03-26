# Guía de Adquisición de Datos - Accidentes de Tránsito INEGI

## Objetivo
Esta guía te muestra paso a paso cómo obtener y procesar los datos de accidentes de tránsito de INEGI para Guadalajara, Jalisco.

---

## Paso 1: Descargar Datos de INEGI

### 1.1 Acceder al Portal de INEGI

**URL:** https://www.inegi.org.mx/programas/accidentes/

1. Ir al sitio web de INEGI
2. Navegar a: Programas → Accidentes de tránsito terrestre en zonas urbanas y suburbanas
3. Buscar la sección "Microdatos"

### 1.2 Descargar Archivos

Los datos están disponibles por año. Necesitas descargar:

**Archivos requeridos:**
- `ATUS_2020.csv` (o formato DBF/XLSX)
- `ATUS_2021.csv`
- `ATUS_2022.csv`
- `ATUS_2023.csv`

**Ubicación de descarga:** `backend/data/raw/inegi/`

### 1.3 Estructura de los Datos INEGI

**Columnas principales:**
```
ENTIDAD          - Código del estado (14 = Jalisco)
MUNICIPIO        - Código del municipio
ANIO             - Año del accidente
MES              - Mes del accidente
DIA              - Día del accidente
HORA             - Hora del accidente
LATITUD          - Latitud del accidente
LONGITUD         - Longitud del accidente
TIPO_ACCIDENTE   - Tipo de accidente
GRAVEDAD         - Gravedad (fatal, no fatal)
CICLISTA         - Si involucró ciclista (1=Sí, 0=No)
PEATONES         - Número de peatones involucrados
VEHICULOS        - Número de vehículos involucrados
```

**Códigos de municipios de la ZMG:**
- 39 = Guadalajara
- 120 = Zapopan
- 97 = Tlaquepaque
- 101 = Tonalá
- 70 = El Salto
- 98 = Tlajomulco de Zúñiga

---

## Paso 2: Script de Descarga Automatizada (Opcional)

Si INEGI tiene API o datos abiertos actualizados:

**Ubicación:** `backend/scripts/download_inegi_data.py`

```python
import requests
import pandas as pd
from pathlib import Path

def download_inegi_accidents(years=[2020, 2021, 2022, 2023]):
    """
    Descargar datos de accidentes de INEGI
    
    Nota: Este es un ejemplo. INEGI puede requerir descarga manual.
    """
    print("=" * 60)
    print("DESCARGA DE DATOS DE ACCIDENTES - INEGI")
    print("=" * 60)
    
    base_url = "https://www.inegi.org.mx/contenidos/programas/accidentes/"
    output_dir = Path("../data/raw/inegi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for year in years:
        print(f"\nDescargando datos de {year}...")
        
        # URL de ejemplo - verificar URL real en INEGI
        url = f"{base_url}{year}/microdatos/ATUS_{year}.csv"
        
        try:
            # Descargar
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                output_file = output_dir / f"ATUS_{year}.csv"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"✓ Descargado: {output_file}")
            else:
                print(f"✗ Error {response.status_code} al descargar {year}")
                print(f"  Descarga manual requerida desde:")
                print(f"  https://www.inegi.org.mx/programas/accidentes/")
        
        except Exception as e:
            print(f"✗ Error: {e}")
            print(f"  Descarga manual requerida")
    
    print("\n" + "=" * 60)
    print("DESCARGA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    download_inegi_accidents()
```

---

## Paso 3: Procesar Datos de INEGI

### 3.1 Script de Procesamiento Completo

**Ubicación:** `backend/scripts/process_inegi_accidents.py`

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import glob

def load_and_combine_inegi_data(data_dir="../data/raw/inegi"):
    """
    Cargar y combinar múltiples años de datos INEGI
    """
    print("=" * 60)
    print("PROCESAMIENTO DE DATOS INEGI - GUADALAJARA")
    print("=" * 60)
    
    # Buscar todos los archivos CSV
    csv_files = glob.glob(f"{data_dir}/ATUS_*.csv")
    
    if not csv_files:
        print(f"\n✗ No se encontraron archivos en {data_dir}")
        print("  Descarga los datos manualmente de:")
        print("  https://www.inegi.org.mx/programas/accidentes/")
        return None
    
    print(f"\nArchivos encontrados: {len(csv_files)}")
    for f in csv_files:
        print(f"  - {Path(f).name}")
    
    # Cargar y combinar
    dfs = []
    for file in csv_files:
        print(f"\nCargando {Path(file).name}...")
        try:
            df = pd.read_csv(file, encoding='latin-1', low_memory=False)
            print(f"  ✓ {len(df):,} registros cargados")
            dfs.append(df)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    if not dfs:
        return None
    
    # Combinar todos los años
    df_combined = pd.concat(dfs, ignore_index=True)
    print(f"\n✓ Total de registros combinados: {len(df_combined):,}")
    
    return df_combined

def filter_guadalajara_cyclists(df):
    """
    Filtrar accidentes de ciclistas en Guadalajara
    """
    print("\n" + "-" * 60)
    print("FILTRANDO DATOS PARA GUADALAJARA")
    print("-" * 60)
    
    # 1. Filtrar por estado (Jalisco = 14)
    df_jalisco = df[df['ENTIDAD'] == 14].copy()
    print(f"\n1. Accidentes en Jalisco: {len(df_jalisco):,}")
    
    # 2. Filtrar por municipios de la ZMG
    gdl_municipalities = {
        39: 'Guadalajara',
        120: 'Zapopan',
        97: 'Tlaquepaque',
        101: 'Tonalá',
        70: 'El Salto',
        98: 'Tlajomulco'
    }
    
    df_zmg = df_jalisco[df_jalisco['MUNICIPIO'].isin(gdl_municipalities.keys())].copy()
    print(f"2. Accidentes en ZMG: {len(df_zmg):,}")
    
    # Mostrar distribución por municipio
    print("\n   Distribución por municipio:")
    for mun_code, mun_name in gdl_municipalities.items():
        count = len(df_zmg[df_zmg['MUNICIPIO'] == mun_code])
        if count > 0:
            print(f"   - {mun_name}: {count:,}")
    
    # 3. Filtrar accidentes con ciclistas
    # Nota: La columna puede llamarse 'CICLISTA', 'CICLISTAS', o similar
    cyclist_columns = [col for col in df_zmg.columns if 'CICL' in col.upper()]
    
    if cyclist_columns:
        cyclist_col = cyclist_columns[0]
        print(f"\n3. Usando columna: {cyclist_col}")
        
        # Filtrar donde hay ciclistas involucrados
        df_cyclists = df_zmg[df_zmg[cyclist_col] > 0].copy()
        print(f"   Accidentes con ciclistas: {len(df_cyclists):,}")
    else:
        print("\n⚠ No se encontró columna de ciclistas")
        print("   Columnas disponibles:", df_zmg.columns.tolist())
        df_cyclists = df_zmg.copy()
    
    return df_cyclists

def create_geodataframe(df):
    """
    Crear GeoDataFrame con geometría de puntos
    """
    print("\n" + "-" * 60)
    print("CREANDO GEODATAFRAME")
    print("-" * 60)
    
    # Verificar columnas de coordenadas
    lat_col = None
    lon_col = None
    
    for col in df.columns:
        if 'LAT' in col.upper():
            lat_col = col
        if 'LON' in col.upper() or 'LONG' in col.upper():
            lon_col = col
    
    if not lat_col or not lon_col:
        print("✗ No se encontraron columnas de coordenadas")
        print(f"  Columnas disponibles: {df.columns.tolist()}")
        return None
    
    print(f"\nUsando columnas:")
    print(f"  Latitud: {lat_col}")
    print(f"  Longitud: {lon_col}")
    
    # Limpiar datos
    df_clean = df.copy()
    
    # Convertir a numérico
    df_clean[lat_col] = pd.to_numeric(df_clean[lat_col], errors='coerce')
    df_clean[lon_col] = pd.to_numeric(df_clean[lon_col], errors='coerce')
    
    # Eliminar valores nulos o inválidos
    df_clean = df_clean.dropna(subset=[lat_col, lon_col])
    
    # Filtrar coordenadas válidas para Guadalajara
    # Guadalajara está aproximadamente entre:
    # Latitud: 20.5 - 20.8
    # Longitud: -103.5 - -103.2
    df_clean = df_clean[
        (df_clean[lat_col] >= 20.5) & (df_clean[lat_col] <= 20.8) &
        (df_clean[lon_col] >= -103.5) & (df_clean[lon_col] <= -103.2)
    ]
    
    print(f"\nRegistros con coordenadas válidas: {len(df_clean):,}")
    
    # Crear geometría
    df_clean['geometry'] = df_clean.apply(
        lambda row: Point(row[lon_col], row[lat_col]),
        axis=1
    )
    
    # Convertir a GeoDataFrame
    gdf = gpd.GeoDataFrame(df_clean, geometry='geometry', crs='EPSG:4326')
    
    print(f"✓ GeoDataFrame creado: {len(gdf):,} puntos")
    
    return gdf

def add_temporal_features(gdf):
    """
    Agregar características temporales
    """
    print("\n" + "-" * 60)
    print("AGREGANDO CARACTERÍSTICAS TEMPORALES")
    print("-" * 60)
    
    # Crear columna de fecha
    if 'ANIO' in gdf.columns and 'MES' in gdf.columns and 'DIA' in gdf.columns:
        gdf['fecha'] = pd.to_datetime(
            gdf[['ANIO', 'MES', 'DIA']].rename(
                columns={'ANIO': 'year', 'MES': 'month', 'DIA': 'day'}
            ),
            errors='coerce'
        )
        
        # Día de la semana
        gdf['dia_semana'] = gdf['fecha'].dt.dayofweek
        gdf['es_fin_semana'] = gdf['dia_semana'].isin([5, 6]).astype(int)
        
        print("✓ Características temporales agregadas")
    
    # Hora del día
    if 'HORA' in gdf.columns:
        gdf['hora_dia'] = pd.to_numeric(gdf['HORA'], errors='coerce')
        gdf['es_hora_pico'] = gdf['hora_dia'].apply(
            lambda x: 1 if (7 <= x <= 10) or (18 <= x <= 21) else 0
        )
        
        print("✓ Características de hora agregadas")
    
    return gdf

def save_processed_data(gdf, output_file="../data/processed/guadalajara_cyclist_accidents.geojson"):
    """
    Guardar datos procesados
    """
    print("\n" + "-" * 60)
    print("GUARDANDO DATOS PROCESADOS")
    print("-" * 60)
    
    # Crear directorio si no existe
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Guardar como GeoJSON
    gdf.to_file(output_file, driver='GeoJSON')
    print(f"✓ GeoJSON guardado: {output_file}")
    
    # Guardar también como CSV para análisis
    csv_file = str(output_file).replace('.geojson', '.csv')
    gdf_csv = gdf.copy()
    gdf_csv['lat'] = gdf_csv.geometry.y
    gdf_csv['lon'] = gdf_csv.geometry.x
    gdf_csv = gdf_csv.drop(columns=['geometry'])
    gdf_csv.to_csv(csv_file, index=False)
    print(f"✓ CSV guardado: {csv_file}")
    
    # Estadísticas finales
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS FINALES")
    print("=" * 60)
    print(f"Total de accidentes procesados: {len(gdf):,}")
    
    if 'ANIO' in gdf.columns:
        print("\nDistribución por año:")
        print(gdf['ANIO'].value_counts().sort_index())
    
    if 'MUNICIPIO' in gdf.columns:
        print("\nDistribución por municipio:")
        print(gdf['MUNICIPIO'].value_counts())
    
    if 'GRAVEDAD' in gdf.columns:
        print("\nDistribución por gravedad:")
        print(gdf['GRAVEDAD'].value_counts())
    
    return gdf

def main():
    """
    Proceso completo de datos INEGI
    """
    print("\n" + "=" * 60)
    print("PROCESO COMPLETO DE DATOS INEGI")
    print("=" * 60)
    
    # 1. Cargar datos
    df = load_and_combine_inegi_data()
    
    if df is None:
        print("\n✗ No se pudieron cargar los datos")
        return
    
    # 2. Filtrar Guadalajara y ciclistas
    df_cyclists = filter_guadalajara_cyclists(df)
    
    # 3. Crear GeoDataFrame
    gdf = create_geodataframe(df_cyclists)
    
    if gdf is None:
        print("\n✗ No se pudo crear GeoDataFrame")
        return
    
    # 4. Agregar características
    gdf = add_temporal_features(gdf)
    
    # 5. Guardar
    gdf = save_processed_data(gdf)
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\nArchivo generado:")
    print(f"  ../data/processed/guadalajara_cyclist_accidents.geojson")
    print(f"\nEste archivo contiene {len(gdf):,} accidentes de ciclistas")
    print(f"en la Zona Metropolitana de Guadalajara")

if __name__ == "__main__":
    main()
```

---

## Paso 4: Ejecutar el Procesamiento

### 4.1 Preparar el Entorno

```bash
# Activar entorno virtual
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias adicionales si es necesario
pip install geopandas shapely
```

### 4.2 Ejecutar el Script

```bash
cd scripts
python process_inegi_accidents.py
```

### 4.3 Verificar Resultados

```bash
# Verificar que se creó el archivo
ls -lh ../data/processed/guadalajara_cyclist_accidents.geojson

# Ver primeras líneas del CSV
head ../data/processed/guadalajara_cyclist_accidents.csv
```

---

## Paso 5: Validar Datos Procesados

### 5.1 Script de Validación

**Ubicación:** `backend/scripts/validate_accident_data.py`

```python
import geopandas as gpd
import matplotlib.pyplot as plt

def validate_accident_data(geojson_file):
    """
    Validar datos de accidentes procesados
    """
    print("=" * 60)
    print("VALIDACIÓN DE DATOS DE ACCIDENTES")
    print("=" * 60)
    
    # Cargar datos
    gdf = gpd.read_file(geojson_file)
    
    print(f"\nTotal de registros: {len(gdf):,}")
    print(f"Columnas: {gdf.columns.tolist()}")
    
    # Verificar coordenadas
    print("\nRango de coordenadas:")
    print(f"  Latitud: {gdf.geometry.y.min():.4f} a {gdf.geometry.y.max():.4f}")
    print(f"  Longitud: {gdf.geometry.x.min():.4f} a {gdf.geometry.x.max():.4f}")
    
    # Visualizar en mapa
    print("\nGenerando visualización...")
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(ax=ax, markersize=5, color='red', alpha=0.5)
    ax.set_title('Accidentes de Ciclistas en Guadalajara')
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    plt.tight_layout()
    plt.savefig('../data/processed/accidents_map.png', dpi=150)
    print("✓ Mapa guardado: ../data/processed/accidents_map.png")
    
    # Estadísticas
    print("\n" + "=" * 60)
    print("VALIDACIÓN COMPLETADA")
    print("=" * 60)
    
    return gdf

if __name__ == "__main__":
    validate_accident_data("../data/processed/guadalajara_cyclist_accidents.geojson")
```

---

## Resumen del Flujo de Datos

```
1. DESCARGA
   ├─ INEGI Website
   └─ backend/data/raw/inegi/ATUS_YYYY.csv

2. PROCESAMIENTO
   ├─ Filtrar Jalisco (estado 14)
   ├─ Filtrar ZMG (municipios 39, 120, 97, 101)
   ├─ Filtrar ciclistas
   ├─ Crear geometría (Point)
   └─ Agregar características temporales

3. SALIDA
   ├─ backend/data/processed/guadalajara_cyclist_accidents.geojson
   └─ backend/data/processed/guadalajara_cyclist_accidents.csv

4. USO EN ML
   └─ Entrada para prepare_training_data.py
```

---

## Alternativas si No Hay Datos de INEGI

### Opción 1: Datos Sintéticos para Pruebas

```python
# backend/scripts/generate_synthetic_accidents.py
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

def generate_synthetic_accidents(n_accidents=500):
    """
    Generar datos sintéticos de accidentes para pruebas
    """
    print("Generando datos sintéticos de accidentes...")
    
    # Coordenadas de Guadalajara
    lat_min, lat_max = 20.60, 20.75
    lon_min, lon_max = -103.45, -103.25
    
    # Generar puntos aleatorios
    data = {
        'ANIO': np.random.choice([2020, 2021, 2022, 2023], n_accidents),
        'MES': np.random.randint(1, 13, n_accidents),
        'DIA': np.random.randint(1, 29, n_accidents),
        'HORA': np.random.randint(0, 24, n_accidents),
        'LATITUD': np.random.uniform(lat_min, lat_max, n_accidents),
        'LONGITUD': np.random.uniform(lon_min, lon_max, n_accidents),
        'GRAVEDAD': np.random.choice(['FATAL', 'NO_FATAL'], n_accidents, p=[0.1, 0.9]),
        'MUNICIPIO': np.random.choice([39, 120, 97, 101], n_accidents)
    }
    
    df = pd.DataFrame(data)
    
    # Crear geometría
    df['geometry'] = df.apply(
        lambda row: Point(row['LONGITUD'], row['LATITUD']),
        axis=1
    )
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    # Guardar
    output_file = "../data/processed/guadalajara_cyclist_accidents.geojson"
    gdf.to_file(output_file, driver='GeoJSON')
    
    print(f"✓ {n_accidents} accidentes sintéticos generados")
    print(f"✓ Guardado en: {output_file}")
    
    return gdf

if __name__ == "__main__":
    generate_synthetic_accidents()
```

### Opción 2: Datos de Otras Fuentes

- **Waze for Cities:** Reportes de incidentes
- **Gobierno Municipal:** Solicitar datos abiertos
- **Colectivos Ciclistas:** Reportes comunitarios
- **Noticias Locales:** Web scraping de accidentes reportados

---

## Checklist de Verificación

- [ ] Datos descargados de INEGI
- [ ] Script de procesamiento ejecutado
- [ ] Archivo GeoJSON generado
- [ ] Coordenadas validadas (dentro de Guadalajara)
- [ ] Visualización de mapa creada
- [ ] Estadísticas revisadas
- [ ] Archivo listo para usar en ML

---

## Soporte

Si tienes problemas:
1. Verifica que los archivos CSV estén en `backend/data/raw/inegi/`
2. Revisa los nombres de columnas en los archivos INEGI
3. Ajusta los códigos de municipio si es necesario
4. Usa datos sintéticos para pruebas iniciales