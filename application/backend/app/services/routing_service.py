import networkx as nx
import osmnx as ox
from pathlib import Path
import pickle

class ZMGRoutingService:
    """
    Servicio de enrutamiento optimizado para ZMG completa
    """
    
    def __init__(self, graph_file=None):
        """
        Cargar grafo con optimizaciones
        """
        if graph_file is None:
            graph_file = "C:/Users/cared/Desktop/Maestria/Seminario/cyclist-safety-routing/backend/data/raw/zmg_complete_network.pkl"
        
        print(f"Cargando grafo de ZMG...")
        
        with open(graph_file, 'rb') as f:
            self.G = pickle.load(f)
        
        print(f"[OK] Grafo cargado: {len(self.G.nodes):,} nodos")
        
        # Crear índice espacial para búsquedas rápidas
        self._build_spatial_index()
    
    def _build_spatial_index(self):
        """
        Construir índice espacial R-tree
        """
        try:
            from rtree import index
            
            print("Construyendo índice espacial...")
            
            self.spatial_index = index.Index()
            
            for node, data in self.G.nodes(data=True):
                lon, lat = data['x'], data['y']
                self.spatial_index.insert(node, (lon, lat, lon, lat))
            
            print("[OK] Indice espacial construido")
            
        except ImportError:
            print("[WARN] rtree no disponible, usando busqueda lineal")
            self.spatial_index = None
    
    def find_nearest_node_fast(self, lat, lon):
        """
        Encontrar nodo más cercano usando índice espacial
        """
        if self.spatial_index:
            # Búsqueda rápida con R-tree
            nearest = list(self.spatial_index.nearest((lon, lat, lon, lat), 1))
            return nearest[0] if nearest else None
        else:
            # Fallback a OSMnx
            return ox.distance.nearest_nodes(self.G, lon, lat)
    
    def calculate_route_zmg(self, origin, destination, alpha=0.5, beta=0.5):
        """
        Calcular ruta en ZMG con optimizaciones
        """
        # Verificar distancia
        from geopy.distance import geodesic
        
        distance_km = geodesic(origin, destination).km
        
        if distance_km > 50:
            return {
                'error': 'Distancia muy larga (>50 km)',
                'suggestion': 'Usa puntos intermedios'
            }
        
        # Encontrar nodos
        orig_node = self.find_nearest_node_fast(*origin)
        dest_node = self.find_nearest_node_fast(*destination)
        
        # Calcular ruta
        try:
            route = nx.shortest_path(
                self.G,
                orig_node,
                dest_node,
                weight='length'
            )
            
            return {
                'route': route,
                'distance_km': distance_km,
                'num_segments': len(route) - 1
            }
            
        except nx.NetworkXNoPath:
            return {'error': 'No se encontró ruta'}

# Alias para compatibilidad con la API
RoutingService = ZMGRoutingService
