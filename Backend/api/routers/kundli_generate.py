"""
Direct Kundli Generation Endpoint
Generates kundali from user data without requiring a saved profile
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from io import BytesIO
import os

from kundli.divineapi.orchestrator import generate_kundli_orchestrator
from kundli.divineapi.output_model import FinalAstroOutput
from artifacts.generators.api_to_html_service import render_combined_4_pages_html
from artifacts.generators.html_to_pdf_service import convert_html_to_pdf

router = APIRouter(prefix="/kundli", tags=["Kundli Generation"])


class DirectKundliRequest(BaseModel):
    """Request model for direct kundali generation from localStorage data."""
    name: str
    gender: str  # "MALE", "FEMALE", "OTHER"
    birth_datetime: str  # ISO format: "2000-01-15T14:30:00"
    birth_place: str  # "Kanpur, India"
    latitude: float  # From cities table
    longitude: float  # From cities table


@router.post("/generate-direct", response_model=dict)
async def generate_kundli_direct(request: DirectKundliRequest):
    """
    Generate kundali directly from user data without requiring a saved profile.
    Uses data from localStorage (frontend) and calls Divine API to generate kundali HTML.
    
    This endpoint is designed to be called from the /kundli/redirect page after payment.
    """
    try:
        # Parse birth datetime
        birth_dt = datetime.fromisoformat(request.birth_datetime)
        
        # Get Divine API credentials from environment
        # Note: The orchestrator uses DIVINE_API_KEY internally via client
        # But we need to set AUTH_TOKEN for the client's authorization header
        divine_api_key = os.getenv("DIVINE_API_KEY", "")
        divine_access_token = os.getenv("DIVINE_ACCESS_TOKEN", "")
        
        if not divine_api_key:
            raise HTTPException(
                status_code=500,
                detail="Divine API key not configured. Please set DIVINE_API_KEY in .env file."
            )
        
        if not divine_access_token:
            raise HTTPException(
                status_code=500,
                detail="Divine access token not configured. Please set DIVINE_ACCESS_TOKEN in .env file."
            )
        
        # Set AUTH_TOKEN for the DivineAPIClient (it reads from environment)
        os.environ["AUTH_TOKEN"] = divine_access_token
        
        # Prepare Divine API input
        divine_api_input = {
            "api_key": divine_api_key,
            "full_name": request.name,
            "day": birth_dt.day,
            "month": birth_dt.month,
            "year": birth_dt.year,
            "hour": birth_dt.hour,
            "min": birth_dt.minute,
            "sec": birth_dt.second,  # Divine API requires seconds field
            "lat": request.latitude,
            "lon": request.longitude,
            "tzone": 5.5,  # Default to IST, can be calculated based on location
            "gender": request.gender.lower(),  # Divine API expects lowercase
            "place": request.birth_place,
            "chart_style": "south",  # Default to south Indian style
            "lan": "en",  # Language for gemstone API
        }
        
        print(f"Calling Divine API with input: {divine_api_input}")
        
        # Call Divine API orchestrator to get complete astrological data
        astro_output: FinalAstroOutput = generate_kundli_orchestrator(divine_api_input)
        
        print(f"Divine API call successful, generating HTML...")
        
        # Generate HTML from astrological data
        kundli_html = render_combined_4_pages_html(astro_output)
        
        print(f"Kundli HTML generated successfully ({len(kundli_html)} chars)")
        
        return {
            "success": True,
            "kundli_html": kundli_html,
            "birth_info": {
                "name": request.name,
                "birth_place": request.birth_place,
                "birth_datetime": request.birth_datetime
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input data: {str(e)}"
        )
    except Exception as e:
        print(f"Error generating kundli: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate kundli: {str(e)}"
        )


@router.post("/convert-to-pdf")
async def convert_kundli_to_pdf(request: dict):
    """
    Convert kundali HTML to PDF for download.
    Accepts HTML content and returns PDF file.
    """
    try:
        html_content = request.get('html_content')
        if not html_content:
            raise HTTPException(
                status_code=400,
                detail="HTML content is required"
            )
        
        print(f"Converting HTML to PDF (length: {len(html_content)} chars)...")
        
        # Convert HTML to PDF
        try:
            pdf_bytes = convert_html_to_pdf(html_content)
        except Exception as conv_error:
            print(f"WeasyPrint conversion error: {conv_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"PDF conversion failed: {str(conv_error)}. Please check if WeasyPrint is installed: pip install weasyprint"
            )
        
        if not pdf_bytes:
            raise HTTPException(
                status_code=500,
                detail="PDF generation returned empty result"
            )
        
        pdf_size = len(pdf_bytes)
        print(f"PDF generated successfully! Size: {pdf_size:,} bytes")
        
        # Return PDF as downloadable file
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=kundali_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in PDF conversion: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert to PDF: {str(e)}"
        )
