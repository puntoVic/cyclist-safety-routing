import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import glob

def load_and_combine_inegi_data(data_dir="C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/inegi"):
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

def save_processed_data(gdf, output_file="C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/guadalajara_cyclist_accidents.geojson"):
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
    print(f"  C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/processed/guadalajara_cyclist_accidents.geojson")
    print(f"\nEste archivo contiene {len(gdf):,} accidentes de ciclistas")
    print(f"en la Zona Metropolitana de Guadalajara")

if __name__ == "__main__":
    main()
