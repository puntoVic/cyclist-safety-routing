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
    output_dir = Path("C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/inegi")
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
