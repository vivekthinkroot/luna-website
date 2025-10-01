# Cities Integration Documentation

This document describes the integration of the pgAdmin cities table with the Luna backend for place of birth functionality.

## Overview

The cities integration replaces the existing locations table with a more efficient cities table from the pgAdmin database (`looooona`). This provides better performance and more accurate city data for the place of birth field in user profiles.

## Database Configuration

### Environment Variables

The following environment variables are configured in `.env`:

```env
# Database Configuration
DB_URL=postgresql://postgres:tiger@localhost:5432/looooona
```

### Database Schema

The cities table has the following structure:

```sql
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    state VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    population BIGINT,
    timezone VARCHAR(50)
);

CREATE INDEX idx_cities_name ON cities(name);
```

## Implementation Details

### 1. Data Models

**File**: `Backend/data/models.py`

Added `TCities` model to represent the cities table:

```python
class TCities(SQLModel, table=True):
    """Cities table model from pgAdmin database."""
    
    __tablename__ = "cities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # City name with index for fast searching
    country: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    timezone: Optional[str] = None
```

### 2. Data Access Object (DAO)

**File**: `Backend/dao/cities.py`

Created `CitiesDAO` class with optimized methods:

- `get_exact_matches()` - Exact city name matches
- `get_contains_matches()` - Partial matches
- `search_cities_optimized()` - Multi-strategy search algorithm
- `get_cities_by_country()` - Filter by country
- `get_popular_cities()` - Most populated cities
- `get_all_city_names()` - All city names for fuzzy matching

### 3. Service Layer

**File**: `Backend/services/cities.py`

Created `CitiesService` class with business logic:

- Fuzzy matching with similarity algorithms
- Optimized search strategies
- Location resolution
- Coordinate retrieval

### 4. Geolocation Service Update

**File**: `Backend/services/geolocation.py`

Updated to use cities instead of locations:

- Changed imports to use `CitiesDAO` and `CityCandidate`
- Updated all methods to work with cities data
- Maintained backward compatibility

### 5. API Endpoints

**File**: `Backend/api/routers/profile.py`

Added new endpoints:

- `GET /profiles/cities` - Get all cities
- `GET /profiles/cities/search` - Optimized city search
- `GET /profiles/cities/popular` - Popular cities
- `GET /profiles/cities/country/{country}` - Cities by country
- `POST /profiles/resolve-location` - Resolve birth place to city ID

## Optimized Search Algorithm

The cities integration uses a multi-strategy search algorithm for optimal performance:

### 1. Exact Match (Highest Priority)
- Direct string comparison
- Case-insensitive fallback

### 2. Starts With Search (High Priority)
- Prefix matching for partial inputs
- Useful for autocomplete functionality

### 3. Contains Search (Medium Priority)
- Substring matching
- Handles typos and variations

### 4. Fuzzy Matching (Low Priority)
- Similarity scoring using SequenceMatcher
- Configurable threshold (default: 0.6)
- Limited to top candidates

## Performance Features

### Database Indexing
- Primary key on `id`
- Index on `name` for fast searching
- Optimized queries for different search patterns

### Caching Strategy
- Session-based caching for repeated searches
- Configurable cache size and timeout
- Automatic cache invalidation

### Query Optimization
- Limit results to prevent large datasets
- Efficient SQL queries with proper WHERE clauses
- Pagination support for large result sets

## Usage Examples

### 1. Basic City Search

```python
from services.cities import CitiesService

service = CitiesService()

# Search for a city
result = service.search_city("Mumbai")
print(f"Found {result.total_results} results")

# Get best match
best_match = service.resolve_best_match("Mumbai")
if best_match:
    print(f"Best match: {best_match.name}, {best_match.country}")
```

### 2. Optimized Search

```python
# Use optimized search for better performance
cities = service.search_cities_optimized("Delhi", limit=10)
for city in cities:
    print(f"{city.name}, {city.country}")
```

### 3. API Usage

```bash
# Search for cities
curl "http://localhost:8000/profiles/cities/search?search_term=Mumbai&limit=5"

# Get popular cities
curl "http://localhost:8000/profiles/cities/popular?limit=10"

# Get cities by country
curl "http://localhost:8000/profiles/cities/country/India?limit=20"
```

## Configuration

### Environment Variables

```env
# Database
DB_URL=postgresql://postgres:tiger@localhost:5432/looooona

# Geolocation Settings
GEOLOC_ENABLED=true
GEOLOC_FUZZY_MATCHING_ENABLED=true
GEOLOC_FUZZY_MATCH_THRESHOLD=0.6
GEOLOC_MAX_CANDIDATES=5
```

### Settings Classes

The integration uses the existing `GeolocationSettings` class for configuration:

```python
class GeolocationSettings(BaseSettings):
    enabled: bool = True
    fuzzy_matching_enabled: bool = True
    fuzzy_match_threshold: float = 0.6
    max_candidates: int = 5
```

## Testing

### Test Script

Run the integration test:

```bash
cd Backend
python test_cities_integration.py
```

### Test Coverage

The test script covers:

1. Database connection
2. Cities DAO functionality
3. Cities service operations
4. Geolocation integration
5. API endpoint testing

## Migration Notes

### From Locations to Cities

The integration maintains backward compatibility:

- Same API endpoints
- Same response format
- Same business logic
- Only internal implementation changed

### Database Changes

- Old `locations` table remains unchanged
- New `cities` table added
- No data migration required
- Both tables can coexist

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection string in `.env`
   - Ensure database `looooona` exists

2. **No Cities Found**
   - Verify cities table has data
   - Check table permissions
   - Run test script for diagnostics

3. **Slow Search Performance**
   - Check database indexes
   - Verify query optimization
   - Monitor database performance

### Debug Mode

Enable debug logging:

```env
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=DEBUG
```

## Future Enhancements

### Planned Features

1. **Geospatial Search**
   - Distance-based city search
   - Radius-based filtering
   - Map integration

2. **Advanced Caching**
   - Redis integration
   - Distributed caching
   - Cache warming strategies

3. **Machine Learning**
   - Smart city suggestions
   - User preference learning
   - Search result ranking

### Performance Optimizations

1. **Database Optimization**
   - Additional indexes
   - Query optimization
   - Connection pooling

2. **Caching Improvements**
   - Multi-level caching
   - Cache preloading
   - Intelligent invalidation

## Support

For issues or questions regarding the cities integration:

1. Check the test script output
2. Review database logs
3. Verify configuration settings
4. Check API endpoint responses

The integration is designed to be robust and maintainable, with comprehensive error handling and logging throughout the system.
