# Simple stub for location_extractor to prevent import errors
# This returns None for all location extraction methods

class LocationExtractor:
    def extract_location(self, query: str):
        """Always return None - no hardcoded location extraction"""
        return None
    
    def get_scenic_places(self, location: str):
        """Always return None - no hardcoded scenic places"""
        return None
    
    def get_forests(self, location: str):
        """Always return None - no hardcoded forests"""
        return None
    
    def get_water_bodies(self, location: str):
        """Always return None - no hardcoded water bodies"""  
        return None
    
    def get_location_info(self, location: str):
        """Always return None - no hardcoded location info"""
        return None

# Global instance
location_extractor = LocationExtractor()
