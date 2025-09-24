import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy.spatial.distance import cdist
from .osrm_client import osrm_client

class MultiCriteriaOptimizer:
    def __init__(self, weights: Dict[str, float] = None):
        """Initialize multi-criteria optimizer with configurable weights.
        
        Args:
            weights: Dictionary with criteria weights. Default:
                    {'distance': 0.4, 'workload': 0.3, 'ca_potential': 0.2, 'capacity': 0.1}
        """
        self.weights = weights or {
            'distance': 0.4,
            'workload': 0.3, 
            'ca_potential': 0.2,
            'capacity': 0.1
        }
        
        total_weight = sum(self.weights.values())
        self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def calculate_distance_score(self, store_coords: Tuple[float, float], manager_coords: Tuple[float, float]) -> float:
        """Calculate normalized distance score (lower distance = higher score)."""
        try:
            travel_time = osrm_client.get_travel_time_minutes(
                (store_coords[1], store_coords[0]),  # lon, lat for OSRM
                (manager_coords[1], manager_coords[0])
            )
            normalized_score = max(0, 1 - (travel_time / 180))
            return normalized_score
        except:
            distance = np.sqrt((store_coords[0] - manager_coords[0])**2 + 
                             (store_coords[1] - manager_coords[1])**2)
            normalized_score = max(0, 1 - (distance / 5))
            return normalized_score
    
    def calculate_workload_score(self, manager_current_workload: float, manager_capacity: float) -> float:
        """Calculate workload balance score (closer to optimal = higher score)."""
        if manager_capacity <= 0:
            return 0
        
        utilization = manager_current_workload / manager_capacity
        optimal_range = (0.8, 0.9)
        
        if optimal_range[0] <= utilization <= optimal_range[1]:
            return 1.0
        elif utilization < optimal_range[0]:
            return utilization / optimal_range[0]
        else:
            return max(0, 1 - (utilization - optimal_range[1]) * 2)
    
    def calculate_ca_potential_score(self, store_potential: float, max_potential: float) -> float:
        """Calculate CA potential score (higher potential = higher priority)."""
        if max_potential <= 0:
            return 0.5
        return min(1.0, store_potential / max_potential)
    
    def calculate_capacity_score(self, manager_available_capacity: float, max_capacity: float) -> float:
        """Calculate capacity availability score."""
        if max_capacity <= 0:
            return 0
        return min(1.0, manager_available_capacity / max_capacity)
    
    def find_best_manager(self, store: pd.Series, managers: pd.DataFrame, stores: pd.DataFrame) -> str:
        """Find the best manager for a store using multi-criteria optimization."""
        best_score = -1
        best_manager = None
        
        max_potential = stores['Potentiel'].max() if 'Potentiel' in stores.columns else 1
        max_capacity = managers['Nb_visite_max_par_an'].max() if 'Nb_visite_max_par_an' in managers.columns else 1
        
        store_coords = (store['lat'], store['long'])
        store_potential = store.get('Potentiel', 0)
        
        for _, manager in managers.iterrows():
            manager_coords = (manager['Latitude'], manager['Longitude'])
            
            manager_stores = stores[stores['Code_secteur'] == manager['Code_secteur']]
            current_workload = 0
            if not manager_stores.empty and 'Temps' in stores.columns and 'Frequence' in stores.columns:
                current_workload = (manager_stores['Temps'] * manager_stores['Frequence']).sum()
            
            manager_capacity = manager.get('Nb_jour_terrain_par_an', 183) * manager.get('Nb_heure_par_jour', 7) * 60
            available_capacity = max(0, manager_capacity - current_workload)
            
            distance_score = self.calculate_distance_score(store_coords, manager_coords)
            workload_score = self.calculate_workload_score(current_workload, manager_capacity)
            ca_score = self.calculate_ca_potential_score(store_potential, max_potential)
            capacity_score = self.calculate_capacity_score(available_capacity, max_capacity)
            
            total_score = (
                self.weights['distance'] * distance_score +
                self.weights['workload'] * workload_score +
                self.weights['ca_potential'] * ca_score +
                self.weights['capacity'] * capacity_score
            )
            
            if total_score > best_score:
                best_score = total_score
                best_manager = manager['Code_secteur']
        
        return best_manager or managers.iloc[0]['Code_secteur']
    
    def optimize_allocation(self, stores: pd.DataFrame, managers: pd.DataFrame) -> pd.DataFrame:
        """Optimize store allocation using multi-criteria approach."""
        optimized_stores = stores.copy()
        
        for idx, store in stores.iterrows():
            best_manager = self.find_best_manager(store, managers, stores)
            optimized_stores.at[idx, 'Code_secteur'] = best_manager
        
        return optimized_stores

multi_criteria_optimizer = MultiCriteriaOptimizer()
