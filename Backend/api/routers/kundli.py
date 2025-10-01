import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from io import BytesIO
import uuid
import traceback
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.responses import StreamingResponse
from weasyprint import HTML
from io import BytesIO
def render_kundli_html_template(kundli_basic_info, astro_data):
    env = Environment(
        loader=FileSystemLoader('api/template'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('combined_kundli_template.html')
    return template.render(kundli_basic_info=kundli_basic_info, astro_data=astro_data)

# In-memory HTML to PDF conversion
def convert_html_to_pdf(html_content):
    pdf_io = BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)
    return pdf_io.read()

from api.routers.profile import SessionLocal, Profile
from kundli.astro_profile import build_and_store_astro_profile_data
import datetime

# Utility to ensure datetime is always timezone-aware (UTC if naive)
def ensure_aware(dt):
    if dt is None:
        return None
    # If dt is a string, try to parse it
    if isinstance(dt, str):
        try:
            # Try parsing ISO format first
            dt_obj = datetime.datetime.fromisoformat(dt)
        except Exception:
            # Fallback: try common datetime formats (add more if needed)
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    dt_obj = datetime.datetime.strptime(dt, fmt)
                    break
                except Exception:
                    continue
            else:
                raise ValueError(f"Could not parse datetime string: {dt}")
        dt = dt_obj
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt
from kundli.artifact_builder import get_kundli_artifacts, ProfileDAO
from kundli.divineapi.output_model import FinalAstroOutput
from kundli.divineapi_v2.output_model import RawAstroAPIData
from artifacts.generators.api_to_html_service import render_combined_4_pages_html
from fastapi.responses import HTMLResponse
from services.payments import PaymentsService

from artifacts.generators.html_to_pdf_service import convert_html_to_pdf

router = APIRouter(prefix="/kundli", tags=["Kundli"])

# Initialize payments service
payments_service = PaymentsService()

# Utility: Convert RawAstroAPIData to FinalAstroOutput
def raw_to_final_astro_output(raw: RawAstroAPIData) -> FinalAstroOutput:
    user_profile1_dict = raw.basic_astro_details.model_dump() if raw.basic_astro_details else None
    if user_profile1_dict and "timezone" in user_profile1_dict:
        user_profile1_dict["timezone"] = str(user_profile1_dict["timezone"])
    return FinalAstroOutput(
        user_profile1=user_profile1_dict,
        user_profile2=None,
        d1_chart=raw.horoscope_charts["D1"].model_dump() if raw.horoscope_charts and "D1" in raw.horoscope_charts else None,
        d9_chart=raw.horoscope_charts["D9"].model_dump() if raw.horoscope_charts and "D9" in raw.horoscope_charts else None,
        astro_insights=None,
        antar_dasha=raw.vimshottari_dasha.model_dump() if raw.vimshottari_dasha else None,
        dasha_analysis=raw.dasha_analysis.model_dump() if raw.dasha_analysis else None,
        yogas=raw.yogas.model_dump() if raw.yogas else None,
        ashtakavarga=getattr(raw, "ashtakavarga", None).model_dump() if getattr(raw, "ashtakavarga", None) else None
    )

# Endpoint to generate kundli
@router.post("/generate/{profile_id}")
async def generate_kundli_endpoint(profile_id: uuid.UUID, user_id: str = Query(..., description="User ID for payment verification")):
    db: Session = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.profile_id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_id_str = str(profile.profile_id)
        
        # Check payment status before allowing kundli generation
        payment_status = payments_service.check_user_payment_status(user_id)
        if not payment_status.get("has_verified_payment", False):
            raise HTTPException(
                status_code=402, 
                detail="Payment required. Please complete payment to generate kundli."
            )


        # Debug: Print profile and location details before kundli generation
        print(f"[DEBUG] Profile: {profile_id_str}, birth_location_id: {profile.birth_location_id}, birth_place: {profile.birth_place}, birth_datetime: {profile.birth_datetime}, gender: {profile.gender}")

        # Ensure profile.birth_datetime is always timezone-aware before passing to downstream logic
        if hasattr(profile, 'birth_datetime') and profile.birth_datetime:
            profile.birth_datetime = ensure_aware(profile.birth_datetime)
            print(f"[DEBUG] Normalized birth_datetime: {profile.birth_datetime} (type: {type(profile.birth_datetime)})")

        # Generate kundli basic info
        basic_kundli_info = await build_and_store_astro_profile_data(profile_id_str)

        # Generate kundli artifacts (HTML, PDF, astro data)
        try:
            artifacts = await get_kundli_artifacts(profile_id_str)
        except TypeError as te:
            if "offset-naive and offset-aware" in str(te):
                raise HTTPException(status_code=500, detail="Kundli generation failed: Datetime comparison error (offset-naive vs offset-aware). Please check input data timezones.")
            else:
                raise
        if not artifacts.is_success:
            raise HTTPException(status_code=500, detail=f"Kundli artifact generation failed: {artifacts.error_message}")

        kundli_html = render_kundli_html_template(
            basic_kundli_info.model_dump() if hasattr(basic_kundli_info, 'model_dump') else dict(basic_kundli_info),
            artifacts.astro_data.model_dump() if artifacts.astro_data and hasattr(artifacts.astro_data, 'model_dump') else None
        )
        return {
            "profile_id": profile_id_str,
            "kundli_basic_info": basic_kundli_info.model_dump() if hasattr(basic_kundli_info, 'model_dump') else dict(basic_kundli_info),
            "kundli_html": kundli_html,
            "kundli_pdf": bool(artifacts.pdf),
            "astro_data": artifacts.astro_data.model_dump() if artifacts.astro_data and hasattr(artifacts.astro_data, 'model_dump') else None
        }
    finally:
        db.close()
        
@router.post("/generate-pdf/{profile_id}")
async def generate_kundli_pdf(profile_id: uuid.UUID):
    db: Session = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.profile_id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_id_str = str(profile.profile_id)
        # Ensure profile.birth_datetime is always timezone-aware before passing to downstream logic
        if hasattr(profile, 'birth_datetime') and profile.birth_datetime:
            profile.birth_datetime = ensure_aware(profile.birth_datetime)
            print(f"[DEBUG] Normalized birth_datetime: {profile.birth_datetime} (type: {type(profile.birth_datetime)})")
        basic_kundli_info = await build_and_store_astro_profile_data(profile_id_str)
        artifacts = await get_kundli_artifacts(profile_id_str)
        if not artifacts.is_success:
            raise HTTPException(status_code=500, detail=f"Kundli artifact generation failed: {artifacts.error_message}")

        kundli_html = render_kundli_html_template(
            basic_kundli_info.model_dump() if hasattr(basic_kundli_info, 'model_dump') else dict(basic_kundli_info),
            artifacts.astro_data.model_dump() if artifacts.astro_data and hasattr(artifacts.astro_data, 'model_dump') else None
        )
        pdf_bytes = convert_html_to_pdf(kundli_html)
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=kundli_{profile_id_str}.pdf"})
    except Exception as e:
        print("Error generating kundli PDF:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Kundli PDF generation failed: {str(e)}")
    finally:
        db.close()

@router.get("/generated/{profile_id}")
async def get_generated_kundli(profile_id: str):
    profiles_dao = ProfileDAO()
    profile_data = profiles_dao.get_profile_data(profile_id)
    if not profile_data:
        raise HTTPException(status_code=404, detail="No profile data found for this profile")
    return profile_data

@router.get("/can-generate/{user_id}")
async def can_generate_kundli(user_id: str):
    """
    Check if user can generate kundli (payment verification).
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict containing whether user can generate kundli
    """
    try:
        payment_status = payments_service.check_user_payment_status(user_id)
        can_generate = payment_status.get("has_verified_payment", False)
        
        return {
            "can_generate": can_generate,
            "payment_status": payment_status,
            "message": "Payment verified" if can_generate else "Payment required"
        }
        
    except Exception as e:
        logger.error(f"Error checking kundli generation eligibility: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

RAZORPAY_KEY_ID = "rzp_live_RM7mcIelFY6w84"       # set in your env
RAZORPAY_KEY_SECRET = "ppTFAaVUDMGYt0xVtDsYwfbT"  # set in your env


def _get_auth():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Razorpay credentials not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET).",
        )
    return (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)


@router.get("/payments/{payment_id}")
def get_payment(payment_id: str):
    """
    Proxy to Razorpay Payments API.
    Example: GET /payments/pay_XXXXXXXXXXXXXXXX
    """
    url = f"https://api.razorpay.com/v1/payments/{payment_id}"
    try:
        resp = requests.get(url, auth=_get_auth(), timeout=10)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Payment not found.")
        resp.raise_for_status()
        payment_details = resp.json()
        return JSONResponse(
            {
                "payment": payment_details,
                "payment_status": payment_details.get("status"),
            }
        )
    except requests.exceptions.RequestException as e:
        # Bubble up as a 502 since the upstream call failed
        raise HTTPException(status_code=502, detail=f"Error fetching payment details: {e}")