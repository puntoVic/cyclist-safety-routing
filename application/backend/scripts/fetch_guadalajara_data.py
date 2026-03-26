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
    output_file = f"C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/guadalajara_network_{timestamp}.pkl"
    
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
