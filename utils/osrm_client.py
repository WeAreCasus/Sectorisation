import requests
import time
import json
from typing import Tuple, Optional, Dict, Any
import streamlit as st

class OSRMClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.cache = {}
        
    def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Get route information between two coordinates using OSRM API.
        
        Args:
            start_coords: (longitude, latitude) of start point
            end_coords: (longitude, latitude) of end point
            
        Returns:
            Dictionary with route information including duration and distance
        """
        cache_key = f"{start_coords[0]:.6f},{start_coords[1]:.6f}-{end_coords[0]:.6f},{end_coords[1]:.6f}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            url = f"{self.base_url}/route/v1/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
            params = {
                'overview': 'false',
                'alternatives': 'false',
                'steps': 'false',
                'geometries': 'geojson'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok' and data.get('routes'):
                    route_info = {
                        'duration': data['routes'][0]['duration'],  # seconds
                        'distance': data['routes'][0]['distance'],  # meters
                        'duration_minutes': data['routes'][0]['duration'] / 60
                    }
                    self.cache[cache_key] = route_info
                    return route_info
            
            return None
            
        except Exception as e:
            st.warning(f"OSRM API error: {e}. Using fallback calculation.")
            return self._fallback_calculation(start_coords, end_coords)
    
    def _fallback_calculation(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict[str, Any]:
        """Fallback calculation when OSRM is not available."""
        from geopy.distance import geodesic
        
        distance_km = geodesic((start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])).kilometers
        
        avg_speed_kmh = 50
        duration_minutes = (distance_km / avg_speed_kmh) * 60
        
        return {
            'duration': duration_minutes * 60,
            'distance': distance_km * 1000,
            'duration_minutes': duration_minutes
        }
    
    def get_travel_time_minutes(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> float:
        """Get travel time in minutes between two coordinates."""
        route_info = self.get_route(start_coords, end_coords)
        if route_info:
            return route_info['duration_minutes']
        return 25000 / 60  # fallback to old fixed value in minutes
    
    def is_available(self) -> bool:
        """Check if OSRM service is available."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

osrm_client = OSRMClient()
