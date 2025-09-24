import re
from typing import Tuple, Optional
from geopy.geocoders import Nominatim

class MonacoGeocoder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="sectorisation_monaco_v1.0")
        self.monaco_postal_codes = set(range(98000, 99000))  # Monaco postal codes
        
    def is_monaco_postal_code(self, postal_code: str) -> bool:
        """Check if postal code belongs to Monaco."""
        try:
            code = int(postal_code)
            return code in self.monaco_postal_codes
        except (ValueError, TypeError):
            return False
    
    def is_monaco_address(self, address: str) -> bool:
        """Check if address contains Monaco indicators."""
        address_lower = address.lower()
        monaco_indicators = ['monaco', 'monte-carlo', 'monte carlo', 'principauté']
        return any(indicator in address_lower for indicator in monaco_indicators)
    
    def normalize_monaco_address(self, address: str, postal_code: str = None) -> str:
        """Normalize Monaco address for better geocoding."""
        if postal_code and self.is_monaco_postal_code(postal_code):
            if not self.is_monaco_address(address):
                address = f"{address}, Monaco"
        
        return address
    
    def geocode_with_monaco_support(self, address: str, postal_code: str = None) -> Tuple[Optional[float], Optional[float], str]:
        """Geocode address with Monaco support, returning department code."""
        try:
            normalized_address = self.normalize_monaco_address(address, postal_code)
            
            location = self.geolocator.geocode(normalized_address)
            
            if location:
                department_code = self.get_department_code(location, postal_code)
                return location.latitude, location.longitude, department_code
            else:
                return None, None, "Unknown"
                
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None, None, "Unknown"
    
    def get_department_code(self, location, postal_code: str = None) -> str:
        """Get department code, treating Monaco as department 06."""
        if postal_code and self.is_monaco_postal_code(postal_code):
            return "06"
        
        if hasattr(location, 'address') and self.is_monaco_address(location.address):
            return "06"
        
        if (location.latitude and location.longitude and
            43.7 <= location.latitude <= 43.8 and
            7.4 <= location.longitude <= 7.5):
            return "06"
        
        if postal_code:
            try:
                code = postal_code.strip()
                if len(code) >= 2:
                    dept = code[:2]
                    if code.startswith('97') or code.startswith('98'):
                        return code[:3] if len(code) >= 3 else dept
                    return dept
            except:
                pass
        
        return "Unknown"

monaco_geocoder = MonacoGeocoder()
