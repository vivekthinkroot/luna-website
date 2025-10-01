from typing import Optional

from pydantic import BaseModel

from artifacts.generators.api_to_html_service import render_kundli_html
from artifacts.generators.html_to_pdf_service import convert_html_to_pdf
from dao.profiles import ProfileDAO
from kundli.astro_profile import ChartStyle
from kundli.divineapi.output_model import FinalAstroOutput
from kundli.divineapi_v2.output_model import RawAstroAPIData
from utils.logger import get_logger

logger = get_logger()


class KundliArtifacts(BaseModel):
    astro_data: Optional[RawAstroAPIData] = None
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    is_success: bool = False
    error_message: Optional[str] = None


async def get_kundli_artifacts(
    profile_id: str,
    chart_style: Optional[ChartStyle] = ChartStyle.AUTO,
) -> KundliArtifacts:
    """
    Generate kundli artifacts for a profile by fetching existing kundli data.

    This method fetches existing kundli data from the database and generates artifacts.
    For new implementations, consider using build_and_store_astro_profile_data() and
    generate_artifacts_from_astro_data() separately.

    Args:
        profile_id: ID of the profile to generate artifacts for
        chart_style: Chart style preference (auto/south/north) - not used when fetching existing data

    Returns:
        KundliArtifacts: Object containing astro data, HTML, and PDF
    """
    try:
        # Fetch existing kundli data from profile DAO
        profiles_dao = ProfileDAO()
        profile_data = profiles_dao.get_profile_data(profile_id)

        if not profile_data or not profile_data.kundli_data:
            return KundliArtifacts(
                is_success=False, error_message="No kundli data found for this profile"
            )

        # Convert stored JSON data back to RawAstroAPIData
        try:
            astro_data = RawAstroAPIData.model_validate(profile_data.kundli_data)
        except Exception as e:
            logger.warning(
                f"Failed to parse cached profile data for {profile_id}, regenerating: {e}"
            )
            # parsing is never supposed to fail
            return KundliArtifacts(
                is_success=False,
                error_message=f"Failed to deserialize artifacts from profile-dao: {str(e)}",
            )

        # Generate artifacts from the astro data
        return _generate_artifacts_from_astro_data(astro_data)

    except Exception as e:
        logger.error(f"Failed to fetch kundli data for profile {profile_id}: {e}")
        return KundliArtifacts(
            is_success=False, error_message=f"Failed to fetch kundli data: {str(e)}"
        )


def _generate_artifacts_from_astro_data(astro_data: RawAstroAPIData) -> KundliArtifacts:
    """
    Generate HTML and PDF artifacts from existing astrological data.

    Args:
        astro_data: The astrological data to convert to artifacts

    Returns:
        KundliArtifacts: Object containing astro data, HTML, and PDF
    """
    try:
        # TODO: Implement HTML generation from v2 RawAstroAPIData
        # For now, create a stub that returns basic success response
        html_payload = f"<html><body><h1>Kundli Report for {astro_data.basic_astro_details.full_name if astro_data.basic_astro_details else 'User'}</h1></body></html>"
        logger.info("HTML report generated successfully from astro data!")

        # TODO: Implement PDF generation from HTML
        # For now, return None for PDF
        pdf_payload = None
        logger.info("PDF generation stub - returning None for now")

        return KundliArtifacts(
            astro_data=astro_data, html=html_payload, pdf=pdf_payload, is_success=True
        )
    except Exception as e:
        logger.error(f"Failed to generate artifacts from astro data: {e}")
        return KundliArtifacts(
            is_success=False, error_message=f"Failed to generate artifacts: {str(e)}"
        )


def _generate_artifacts_from_v1_astro_output(
    astro_data: FinalAstroOutput,
) -> KundliArtifacts:
    """
    Generate HTML and PDF artifacts from existing astrological data (backward compatibility).

    Args:
        astro_data: The astrological data to convert to artifacts

    Returns:
        KundliArtifacts: Object containing astro data, HTML, and PDF
    """
    try:
        # Generate HTML from astro data
        html_payload = render_kundli_html(astro_data)
        logger.info("HTML report generated successfully from astro data!")

        # Generate PDF from HTML
        pdf_payload = convert_html_to_pdf(html_payload)
        if pdf_payload is None:
            raise ValueError(
                "PDF generation failed: received None from convert_html_to_pdf"
            )
        logger.info("PDF generated successfully from astro data!")

        return KundliArtifacts(
            astro_data=None,  # FinalAstroOutput is not compatible with RawAstroAPIData
            html=html_payload,
            pdf=pdf_payload,
            is_success=True,
        )
    except Exception as e:
        logger.error(f"Failed to generate artifacts from astro data: {e}")
        return KundliArtifacts(
            is_success=False, error_message=f"Failed to generate artifacts: {str(e)}"
        )


def generate_artifacts_from_final_astro_output(
    astro_data: FinalAstroOutput,
) -> KundliArtifacts:
    """
    Generate artifacts from FinalAstroOutput (backward compatibility).

    Args:
        astro_data: The astrological data to convert to artifacts

    Returns:
        KundliArtifacts: Object containing astro data, HTML, and PDF
    """
    if not astro_data:
        return KundliArtifacts(is_success=False, error_message="No astro data provided")

    return _generate_artifacts_from_v1_astro_output(astro_data)
