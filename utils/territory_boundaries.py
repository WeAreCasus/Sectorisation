import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import folium

class TerritoryBoundaryManager:
    def __init__(self):
        self.territories = {}
        self.overlaps = []
    
    def create_voronoi_territories(self, managers: pd.DataFrame) -> Dict[str, Polygon]:
        """Create non-overlapping territories using Voronoi diagrams."""
        if managers.empty or 'Latitude' not in managers.columns or 'Longitude' not in managers.columns:
            return {}
        
        points = managers[['Longitude', 'Latitude']].values
        manager_codes = managers['Code_secteur'].values
        
        if len(points) < 3:
            return self._create_circular_territories(managers)
        
        try:
            vor = Voronoi(points)
            
            territories = {}
            
            for i, manager_code in enumerate(manager_codes):
                region_index = vor.point_region[i]
                vertex_indices = vor.regions[region_index]
                
                if -1 not in vertex_indices and len(vertex_indices) > 0:
                    vertices = vor.vertices[vertex_indices]
                    if len(vertices) >= 3:
                        territories[manager_code] = Polygon(vertices)
                else:
                    territories[manager_code] = self._create_bounded_region(points[i], vor, i)
            
            return territories
            
        except Exception as e:
            print(f"Voronoi creation failed: {e}")
            return self._create_circular_territories(managers)
    
    def _create_circular_territories(self, managers: pd.DataFrame, radius: float = 0.5) -> Dict[str, Polygon]:
        """Create circular territories as fallback."""
        territories = {}
        
        for _, manager in managers.iterrows():
            center = Point(manager['Longitude'], manager['Latitude'])
            territory = center.buffer(radius)
            territories[manager['Code_secteur']] = territory
        
        return territories
    
    def _create_bounded_region(self, point: np.ndarray, vor: Voronoi, point_index: int) -> Polygon:
        """Create a bounded region for infinite Voronoi cells."""
        bbox = Polygon([
            (-5, 41),   # Southwest
            (10, 41),   # Southeast  
            (10, 52),   # Northeast
            (-5, 52)    # Northwest
        ])
        
        center = Point(point[0], point[1])
        circle = center.buffer(1.0)  # 1 degree radius
        
        return circle.intersection(bbox)
    
    def detect_overlaps(self, territories: Dict[str, Polygon]) -> List[Tuple[str, str]]:
        """Detect overlapping territories."""
        overlaps = []
        territory_codes = list(territories.keys())
        
        for i, code1 in enumerate(territory_codes):
            for code2 in territory_codes[i+1:]:
                if territories[code1].intersects(territories[code2]):
                    intersection = territories[code1].intersection(territories[code2])
                    if intersection.area > 0.001:  # Significant overlap threshold
                        overlaps.append((code1, code2))
        
        return overlaps
    
    def resolve_overlaps(self, territories: Dict[str, Polygon], stores: pd.DataFrame) -> Dict[str, Polygon]:
        """Resolve territory overlaps by adjusting boundaries."""
        overlaps = self.detect_overlaps(territories)
        
        if not overlaps:
            return territories
        
        resolved_territories = territories.copy()
        
        for code1, code2 in overlaps:
            territory1_stores = stores[stores['Code_secteur'] == code1]
            territory2_stores = stores[stores['Code_secteur'] == code2]
            
            if not territory1_stores.empty and not territory2_stores.empty:
                centroid1 = (territory1_stores['long'].mean(), territory1_stores['lat'].mean())
                centroid2 = (territory2_stores['long'].mean(), territory2_stores['lat'].mean())
                
                mid_x = (centroid1[0] + centroid2[0]) / 2
                mid_y = (centroid1[1] + centroid2[1]) / 2
                
                buffer_distance = 0.01  # Small buffer to prevent touching
                
                if centroid1[0] < centroid2[0]:  # code1 is west of code2
                    resolved_territories[code1] = territories[code1].intersection(
                        Polygon([(-180, -90), (mid_x - buffer_distance, -90), 
                                (mid_x - buffer_distance, 90), (-180, 90)])
                    )
                    resolved_territories[code2] = territories[code2].intersection(
                        Polygon([(mid_x + buffer_distance, -90), (180, -90), 
                                (180, 90), (mid_x + buffer_distance, 90)])
                    )
        
        return resolved_territories
    
    def add_territories_to_map(self, folium_map: folium.Map, territories: Dict[str, Polygon], 
                              sector_colors: Dict[str, str] = None) -> folium.Map:
        """Add territory boundaries to a Folium map."""
        if not territories:
            return folium_map
        
        for sector_code, territory in territories.items():
            if territory and not territory.is_empty:
                color = sector_colors.get(sector_code, '#FF0000') if sector_colors else '#FF0000'
                
                try:
                    if hasattr(territory, 'exterior'):
                        coords = list(territory.exterior.coords)
                        folium_coords = [(lat, lon) for lon, lat in coords]
                        
                        folium.Polygon(
                            locations=folium_coords,
                            color=color,
                            weight=2,
                            opacity=0.8,
                            fill=True,
                            fillColor=color,
                            fillOpacity=0.1,
                            popup=f"Territory: {sector_code}"
                        ).add_to(folium_map)
                except Exception as e:
                    print(f"Error adding territory {sector_code} to map: {e}")
        
        return folium_map

territory_manager = TerritoryBoundaryManager()
