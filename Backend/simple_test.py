#!/usr/bin/env python3
"""
Simple test for cities API.
"""

import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dao.cities import CitiesDAO

def test_cities():
    """Test CitiesDAO directly."""
    print("Testing CitiesDAO...")
    
    try:
        dao = CitiesDAO()
        print("CitiesDAO initialized")
        
        # Test search
        print("Testing search_cities_optimized...")
        cities = dao.search_cities_optimized("mumbai", 5)
        print(f"Found {len(cities)} cities")
        
        if cities:
            city = cities[0]
            print(f"Sample city: {city.dict()}")
        
        return True
        
    except Exception as e:
        print(f"Error in CitiesDAO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cities()
