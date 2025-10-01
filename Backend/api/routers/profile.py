from dao.cities import CitiesDAO
# Endpoint to get all cities data
from fastapi import Request
from services.geolocation import GeolocationService
# Endpoint to resolve birth_place to birth_location_id

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import create_engine, Column, String, Date, Time, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from api.schemas.profile import ProfileCreate

# Database setup
DATABASE_URL = "postgresql://postgres:tiger@localhost:5432/looooona"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=False)
    dob = Column(Date, nullable=False)
    pob = Column(String(100), nullable=False)
    tob = Column(Time, nullable=False)  # store as Time type instead of string
    mobile_no = Column(String(15), nullable=False)  # Removed unique constraint for testing
    email = Column(String(100), nullable=False)  # Removed unique constraint for testing

    birth_datetime = Column(String(30), nullable=True)
    birth_place = Column(String(100), nullable=True)
    birth_location_id = Column(Integer, nullable=True)  # FIX: Should be Integer type for location ID
    name = Column(String(100), nullable=True)
    sun_sign = Column(String(30), nullable=True)
    moon_sign = Column(String(30), nullable=True)

    # Make timestamps nullable and provide proper defaults
    created_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

# Ensure table is created before any DB operations
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.post("/", response_model=dict)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    try:
        # Allow duplicate emails and mobile numbers for testing/development
        # Removed uniqueness checks to allow multiple profiles with same email/mobile
        
        # Create new profile with explicit timestamp setting
        from datetime import datetime, timezone
        current_time = datetime.now(timezone.utc)

        # Validate gender
        gender_value = profile.gender.value if hasattr(profile.gender, 'value') else str(profile.gender)
        if gender_value not in ['MALE', 'FEMALE', 'OTHER']:
            raise HTTPException(status_code=400, detail="Invalid gender value. Must be MALE, FEMALE, or OTHER.")

        # Parse dob, pob, tob from birth_datetime and birth_place
        dob = profile.birth_datetime.date() if hasattr(profile.birth_datetime, 'date') else None
        tob = profile.birth_datetime.time() if hasattr(profile.birth_datetime, 'time') else None
        pob = profile.birth_place

        # Use birth_location_id directly from profile data, ensure it's an integer or None
        location_id = profile.birth_location_id if profile.birth_location_id is not None else None

        db_profile = Profile(
            name=profile.name,
            full_name=profile.name,
            gender=gender_value,
            dob=dob,
            pob=pob,
            tob=tob,
            birth_datetime=str(profile.birth_datetime),
            birth_place=profile.birth_place,
            birth_location_id=location_id,
            mobile_no=profile.mobile_no,
            email=profile.email,
            created_at=current_time,
            updated_at=current_time
        )

        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)

        return {
            "profile_id": str(db_profile.profile_id),
            "message": "Profile registered successfully"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate entry")
    except Exception as e:
        import traceback
        print("Error creating profile:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
    # Utility: Generate kundli HTML from kundli_data (dict or model)
def generate_kundli_html_from_data(kundli_data):
    from kundli.divineapi_v2.output_model import RawAstroAPIData
    from api.routers.kundli import raw_to_final_astro_output
    from artifacts.generators.api_to_html_service import render_combined_4_pages_html

    raw_astro = RawAstroAPIData.model_validate(kundli_data)
    final_astro = raw_to_final_astro_output(raw_astro)
    kundli_html = render_combined_4_pages_html(final_astro)
    return kundli_html

@router.post("/resolve-location", response_model=dict)
async def resolve_location_endpoint(request: Request):
    data = await request.json()
    birth_place = data.get("birth_place")
    if not birth_place:
        raise HTTPException(status_code=400, detail="birth_place is required")

    geo_service = GeolocationService()
    result = geo_service.search_location(birth_place)
    response = {}
    if result.total_results == 1:
        city = result.exact_matches[0]
        response = {
            "birth_location_id": city.id,
            "city": city.name,
            "state": city.state,
            "country": city.country
        }
    elif result.total_results > 1:
        # Multiple matches, return options for frontend to prompt user
        options = []
        for city in result.exact_matches:
            options.append({
                "id": city.id,
                "city": city.name,
                "state": city.state,
                "country": city.country
            })
        for city, _ in result.fuzzy_matches:
            options.append({
                "id": city.id,
                "city": city.name,
                "state": city.state,
                "country": city.country
            })
        response = {"options": options}
    else:
        response = {"error": f"No locations found for '{birth_place}'"}
    return response

@router.get("/cities", response_model=dict)
def get_all_cities():
    dao = CitiesDAO()
    # Fetch all cities, then filter for country == 'India'
    all_cities = dao.get_contains_matches("", limit=30000)
    india_cities = [city.dict() for city in all_cities if getattr(city, 'country', None) == 'India']
    return {"cities": india_cities}

@router.get("/cities/search", response_model=dict)
def search_cities_optimized(search_term: str, limit: int = 20):
    """
    Optimized city search endpoint using the best algorithms.
    
    Args:
        search_term: The search term to look for
        limit: Maximum number of results to return
        
    Returns:
        List of cities matching the search term
    """
    dao = CitiesDAO()
    cities = dao.search_cities_optimized(search_term, limit)
    return {"cities": [city.dict() for city in cities]}

@router.get("/cities/popular", response_model=dict)
def get_popular_cities(limit: int = 20):
    """
    Get most popular cities (by population).
    
    Args:
        limit: Maximum number of results to return
        
    Returns:
        List of popular cities
    """
    dao = CitiesDAO()
    cities = dao.get_popular_cities(limit)
    return {"cities": [city.dict() for city in cities]}

@router.get("/cities/country/{country}", response_model=dict)
def get_cities_by_country(country: str, limit: int = 50):
    """
    Get cities by country.
    
    Args:
        country: Country name to search for
        limit: Maximum number of results
        
    Returns:
        List of cities in the specified country
    """
    dao = CitiesDAO()
    cities = dao.get_cities_by_country(country, limit)
    return {"cities": [city.dict() for city in cities]}