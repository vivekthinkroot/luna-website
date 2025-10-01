from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Any, Dict, List
import base64
from kundli.divineapi.output_model import FinalAstroOutput

# Setup Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent.parent / "template"
MODULAR_TEMPLATE_DIR = Path(__file__).parent.parent / "modular_template"
env = Environment(
    loader=FileSystemLoader([TEMPLATE_DIR, MODULAR_TEMPLATE_DIR]),
    autoescape=select_autoescape(["html", "xml"])
)

def _encode_image_as_base64(image_path: str) -> str:
    """Encode an image file as base64 data URL."""
    try:
        full_path = Path(__file__).parent.parent / image_path
        if full_path.exists():
            with open(full_path, "rb") as img_file:
                img_data = img_file.read()
                
                # Determine MIME type based on file extension
                ext = full_path.suffix.lower()
                
                # For SVG, use base64 encoding for consistency
                if ext == '.svg':
                    encoded = base64.b64encode(img_data).decode('utf-8')
                    return f"data:image/svg+xml;base64,{encoded}"
                else:
                    # For other images, use base64 encoding
                    encoded = base64.b64encode(img_data).decode('utf-8')
                mime_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                }.get(ext, 'image/png')
                return f"data:{mime_type};base64,{encoded}"
        else:
            print(f"Warning: Image file not found: {full_path}")
            return ""
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return ""

def _get_css_content(css_file: str) -> str:
    """Read CSS file content"""
    try:
        css_path = Path(__file__).parent.parent / "modular_template" / css_file
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            print(f"Warning: CSS file not found: {css_path}")
            return ""
    except Exception as e:
        print(f"Error reading CSS {css_file}: {e}")
        return ""

def _get_images_context() -> Dict[str, str]:
    """Get base64 encoded images for HTML context."""
    image_paths = {
        # Poster images - Fixed missing file
        "bg_blur": "static_images/poster-images/80_554.png",
        "bg_pattern": "static_images/poster-images/bc5069bdaa910433abc621dcdeb2f62ba3a55820.png",  # Fixed: replaced missing file
        "bg_ellipse_1": "static_images/poster-images/80_559.png",
        "bg_ellipse_2": "static_images/poster-images/80_560.png",
        "zodiac_wheel": "static_images/poster-images/e89f95dc7e3825ad8c3ff48833f0d37fe3ec2edb.png",
        
        # Page1 images - Fixed missing file
        "bg_texture": "static_images/page-1-images/6_677.png",
        "cosmic_bg": "static_images/page-1-images/bc5069bdaa910433abc621dcdeb2f62ba3a55820.png",  # Fixed: replaced missing file
        "glow_1": "static_images/page-1-images/6_678.png",
        "glow_2": "static_images/page-1-images/6_679.png",
        "glow_3": "static_images/page-1-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "ganesha": "static_images/page-1-images/28b0f4bca21ce96aa55a97d27fac0fcee17a0e69.png",
        "divider": "static_images/page-1-images/217b852c9f1c5430180d7a6dd5977dd345fd9b46.png",
        
        # User profile images - Fixed missing file
        "bg_main": "static_images/user-profiles-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "bg_deco": "static_images/user-profiles-images/bc5069bdaa910433abc621dcdeb2f62ba3a55820.png",  # Fixed: replaced missing file
        "blur_1": "static_images/user-profiles-images/6_753.png",
        "blur_2": "static_images/user-profiles-images/6_754.png",
        "blur_3": "static_images/user-profiles-images/6_755.png",
        "icon_bg_1": "static_images/user-profiles-images/6_789.png",
        "icon_bg_2": "static_images/user-profiles-images/6_790.png",
        "icon_main": "static_images/user-profiles-images/3ec5556ae00764c443fce7d7355e6e94b1a971ff.png",
        
        # Logo - Use one logo across all pages
        "logo": "static_images/poster-images/logo.png",
        
        # Page 5 (Charts) background
        "charts_bg": "static_images/user-profiles-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        
        # Remedies page images
        "remedies_bg_main": "static_images/remedies-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "remedies_bg_blur": "static_images/remedies-images/155_96.png",
        "remedies_title_decoration": "static_images/remedies-images/04ad95a7104eced41b61df6c7a41329fc61a1b7d.png",
        "remedy_1_image": "static_images/remedies-images/f0feaacffc00b215ffd8990bf4ff56c0251da1a8.png",
        "remedy_2_image": "static_images/remedies-images/b319bec82602e54b673f6440c3928f03e9c46a40.png", 
        "remedy_3_image": "static_images/remedies-images/053d2aa05df8f7cb5aa20cbd7d5e7cf796f288ff.png",
        "remedy_4_bg_image": "static_images/remedies-images/70_537.png",
        "remedy_4_fg_image": "static_images/remedies-images/1b81299fcd641f8ec18a863514d7d081298216c5.png",
        
        # Antar Dasha page images
        "antar_dasha_title_decoration": "static_images/antar-dasha-dates-images/2de6a49da0fd28e69412b17db723faf0ca840baa.png",
        "antar_dasha_bg_main": "static_images/antar-dasha-dates-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "antar_dasha_bg_blur": "static_images/antar-dasha-dates-images/156_236.svg",
        
        # Dasha Analysis page images
        "dasha_analysis_bg_stars": "static_images/dasha-analysis-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "dasha_analysis_bg_blur": "static_images/dasha-analysis-images/156_110.svg",
        "dasha_analysis_dot_387": "static_images/dasha-analysis-images/33_387.svg",
        "dasha_analysis_dot_388": "static_images/dasha-analysis-images/33_388.svg",
        "dasha_analysis_dot_351": "static_images/dasha-analysis-images/70_351.svg",
        "dasha_analysis_dot_390": "static_images/dasha-analysis-images/33_390.svg",
        "dasha_analysis_dot_394": "static_images/dasha-analysis-images/33_394.svg",
        "dasha_analysis_dot_397": "static_images/dasha-analysis-images/33_397.svg",
        "dasha_analysis_dot_400": "static_images/dasha-analysis-images/33_400.svg",
        "dasha_analysis_dot_403": "static_images/dasha-analysis-images/33_403.svg",
        "dasha_analysis_dot_406": "static_images/dasha-analysis-images/33_406.svg",
        "dasha_analysis_dot_409": "static_images/dasha-analysis-images/33_409.svg",
        "dasha_analysis_dot_415": "static_images/dasha-analysis-images/33_415.svg",
        
        # Yogas page images
        "yogas_bg_stars": "static_images/yogas-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "yogas_bg_blur": "static_images/yogas-images/156_257.png",
        "yogas_bg_deco": "static_images/yogas-images/f9329cf484a60fae70cce569fa7808d5b53f7f49.png",
        
        # Ashtakavarga page images
        "ashtakavarga_bg_stars": "static_images/ashtakavarga-images/efa57b83a1733119b6a1ac464c2b102b30abd334.png",
        "ashtakavarga_bg_blur": "static_images/ashtakavarga-images/f9329cf484a60fae70cce569fa7808d5b53f7f49.png",
        "ashtakavarga_title_divider": "static_images/ashtakavarga-images/79836a5dc22827f585e204f11bf02379ad88f02b.png",
        "ashtakavarga_mesha_illustration": "static_images/ashtakavarga-images/4657e95378c964dcf5cda980bf06f63343b47115.png",
        "ashtakavarga_moon_icon": "static_images/ashtakavarga-images/67_150.svg",
        "ashtakavarga_sun_icon": "static_images/ashtakavarga-images/68_24.svg",
        "ashtakavarga_mercury_icon": "static_images/ashtakavarga-images/68_33.svg",
        "ashtakavarga_venus_icon": "static_images/ashtakavarga-images/68_41.svg",
        "ashtakavarga_mars_icon": "static_images/ashtakavarga-images/68_15.svg",
        "ashtakavarga_jupiter_icon": "static_images/ashtakavarga-images/68_24.svg",
        "ashtakavarga_saturn_icon": "static_images/ashtakavarga-images/68_33.svg",
        
        # Rashi illustrations for Ashtakavarga table (using actual available images)
        "mesha_illustration": "static_images/ashtakavarga-images/67_150.svg",
        "vrishabha_illustration": "static_images/ashtakavarga-images/68_15.svg", 
        "mithuna_illustration": "static_images/ashtakavarga-images/68_24.svg",
        "karka_illustration": "static_images/ashtakavarga-images/68_33.svg",
        "simha_illustration": "static_images/ashtakavarga-images/68_41.svg",
        "kanya_illustration": "static_images/ashtakavarga-images/67_150.svg",  # Using same as Mesha
        "tula_illustration": "static_images/ashtakavarga-images/68_15.svg",   # Using same as Vrishabha
        "vrishchika_illustration": "static_images/ashtakavarga-images/68_24.svg", # Using same as Mithuna
        "dhanu_illustration": "static_images/ashtakavarga-images/68_33.svg",  # Using same as Karka
        "makara_illustration": "static_images/ashtakavarga-images/68_41.svg", # Using same as Simha
        "kumbha_illustration": "static_images/ashtakavarga-images/67_150.svg", # Using same as Mesha
        "meena_illustration": "static_images/ashtakavarga-images/68_15.svg",  # Using same as Vrishabha
        
        # Planet icons for Ashtakavarga (using actual planet images)
        "moon_icon": "static_images/ashtakavarga-images/moon.png",
        "sun_icon": "static_images/ashtakavarga-images/sun.png",
        "mercury_icon": "static_images/ashtakavarga-images/mercury.png",
        "venus_icon": "static_images/ashtakavarga-images/venus.png",
        "mars_icon": "static_images/ashtakavarga-images/mars.png",
        "jupiter_icon": "static_images/ashtakavarga-images/jupiter.png",
        "saturn_icon": "static_images/ashtakavarga-images/saturn.png"
    }
    
    return {
        key: _encode_image_as_base64(path) 
        for key, path in image_paths.items()
    }

def _build_template_data(final_output: FinalAstroOutput) -> Dict[str, Any]:
    """
    Build template data from clean UserProfile models and chart models.
    This function extracts data exclusively from UserProfile1, UserProfile2, D1Chart, and D9Chart.
    """
    template_data = {}
    
    # Extract data from UserProfile1 (basic personal info)
    if final_output.user_profile1:
        profile1 = final_output.user_profile1
        template_data.update({
            "full_name": profile1.name,
            "gender": profile1.gender,
            "date_of_birth": profile1.date_of_birth.isoformat() if profile1.date_of_birth else None,
            "timezone": profile1.timezone,
            "place_of_birth": profile1.place_of_birth,
        })
    
    # Extract data from UserProfile2 (astrological info)
    if final_output.user_profile2:
        profile2 = final_output.user_profile2
        template_data.update({
            "longitude": profile2.longitude,
            "latitude": profile2.latitude,
            "ayanamsha": profile2.ayanamsa,
            "nakshatra": profile2.birth_star,
            "moon_sign": profile2.birth_rasi,
            "ascendant": profile2.lagna,
            "planetary_lord": profile2.lagna_lord,
        })
    
    # Add chart data for templates
    if final_output.d1_chart:
        template_data["d1_chart"] = final_output.d1_chart
    
    if final_output.d9_chart:
        template_data["d9_chart"] = final_output.d9_chart
    
    # Add astro insights data for templates
    if final_output.astro_insights:
        template_data["astro_insights"] = final_output.astro_insights
    
    # Add antar dasha data for templates
    if final_output.antar_dasha:
        template_data["antar_dasha"] = final_output.antar_dasha
    
    # Add dasha analysis data for templates
    if final_output.dasha_analysis:
        template_data["dasha_analysis"] = final_output.dasha_analysis
    
    # Add yogas data for templates
    if final_output.yogas:
        template_data["yogas"] = final_output.yogas
    
    # Add ashtakavarga data for templates
    if final_output.ashtakavarga:
        template_data["ashtakavarga"] = final_output.ashtakavarga
    
    return template_data

def render_kundli_html(final_output: FinalAstroOutput) -> str:
    """Render kundli HTML mapping FinalAstroOutput to template-friendly context."""
    template = env.get_template("combined_kundli_template.html")
    
    # Build template data
    template_data = _build_template_data(final_output)

    context = {
        "data": template_data,
        "report_date": None,
        "images": _get_images_context()
    }
    return template.render(context)

def render_combined_4_pages_html(final_output: FinalAstroOutput) -> str:
    """Render the new combined 4-page template with poster, page1, and user profiles."""
    template = env.get_template("combined_4_pages_v2.html")
    
    # Build template data from UserProfile models
    template_data = _build_template_data(final_output)
    
    # Convert None values to "N/A" for display
    data_dict = {
        k: (v if v is not None else "N/A")
        for k, v in template_data.items()
    }
    
    # Add all base64 encoded images to the context
    images = _get_images_context()
    
    # Map image keys to template placeholders
    image_placeholders = {}
    
    # Poster images
    image_placeholders["BG_BLUR_BASE64"] = images.get("bg_blur", "")
    image_placeholders["BG_PATTERN_BASE64"] = images.get("bg_pattern", "")
    image_placeholders["BG_ELLIPSE_1_BASE64"] = images.get("bg_ellipse_1", "")
    image_placeholders["BG_ELLIPSE_2_BASE64"] = images.get("bg_ellipse_2", "")
    image_placeholders["ZODIAC_WHEEL_BASE64"] = images.get("zodiac_wheel", "")
    
    # Page1 images
    image_placeholders["BG_TEXTURE_BASE64"] = images.get("bg_texture", "")
    image_placeholders["COSMIC_BG_BASE64"] = images.get("cosmic_bg", "")
    image_placeholders["GLOW_1_BASE64"] = images.get("glow_1", "")
    image_placeholders["GLOW_2_BASE64"] = images.get("glow_2", "")
    image_placeholders["GLOW_3_BASE64"] = images.get("glow_3", "")
    image_placeholders["GANESHA_BASE64"] = images.get("ganesha", "")
    image_placeholders["DIVIDER_BASE64"] = images.get("divider", "")
    
    # User profile images
    image_placeholders["BG_MAIN_BASE64"] = images.get("bg_main", "")
    image_placeholders["BG_DECO_BASE64"] = images.get("bg_deco", "")
    image_placeholders["BLUR_1_BASE64"] = images.get("blur_1", "")
    image_placeholders["BLUR_2_BASE64"] = images.get("blur_2", "")
    image_placeholders["BLUR_3_BASE64"] = images.get("blur_3", "")
    image_placeholders["ICON_BG_1_BASE64"] = images.get("icon_bg_1", "")
    image_placeholders["ICON_BG_2_BASE64"] = images.get("icon_bg_2", "")
    image_placeholders["ICON_MAIN_BASE64"] = images.get("icon_main", "")
    
    # Common logo (appears on all pages)
    image_placeholders["LOGO_BASE64"] = images.get("logo", "")
    
    context = {
        "data": data_dict,
        "report_date": None,
        # Add image placeholders directly to Jinja2 context
        "BG_BLUR_BASE64": images.get("bg_blur", ""),
        "BG_PATTERN_BASE64": images.get("bg_pattern", ""),
        "BG_ELLIPSE_1_BASE64": images.get("bg_ellipse_1", ""),
        "BG_ELLIPSE_2_BASE64": images.get("bg_ellipse_2", ""),
        "ZODIAC_WHEEL_BASE64": images.get("zodiac_wheel", ""),
        "BG_TEXTURE_BASE64": images.get("bg_texture", ""),
        "COSMIC_BG_BASE64": images.get("cosmic_bg", ""),
        "GLOW_1_BASE64": images.get("glow_1", ""),
        "GLOW_2_BASE64": images.get("glow_2", ""),
        "GLOW_3_BASE64": images.get("glow_3", ""),
        "GANESHA_BASE64": images.get("ganesha", ""),
        "DIVIDER_BASE64": images.get("divider", ""),
        # Antar Dasha page images
        "ANTAR_DASHA_TITLE_DECORATION_BASE64": images.get("antar_dasha_title_decoration", ""),
        "ANTAR_DASHA_BG_MAIN_BASE64": images.get("antar_dasha_bg_main", ""),
        "ANTAR_DASHA_BG_BLUR_BASE64": images.get("antar_dasha_bg_blur", ""),
        # Dasha Analysis page images
        "DASHA_ANALYSIS_BG_STARS_BASE64": images.get("dasha_analysis_bg_stars", ""),
        "DASHA_ANALYSIS_BG_BLUR_BASE64": images.get("dasha_analysis_bg_blur", ""),
        "DASHA_ANALYSIS_DOT_387_BASE64": images.get("dasha_analysis_dot_387", ""),
        "DASHA_ANALYSIS_DOT_388_BASE64": images.get("dasha_analysis_dot_388", ""),
        "DASHA_ANALYSIS_DOT_351_BASE64": images.get("dasha_analysis_dot_351", ""),
        "DASHA_ANALYSIS_DOT_390_BASE64": images.get("dasha_analysis_dot_390", ""),
        "DASHA_ANALYSIS_DOT_394_BASE64": images.get("dasha_analysis_dot_394", ""),
        "DASHA_ANALYSIS_DOT_397_BASE64": images.get("dasha_analysis_dot_397", ""),
        "DASHA_ANALYSIS_DOT_400_BASE64": images.get("dasha_analysis_dot_400", ""),
        "DASHA_ANALYSIS_DOT_403_BASE64": images.get("dasha_analysis_dot_403", ""),
        "DASHA_ANALYSIS_DOT_406_BASE64": images.get("dasha_analysis_dot_406", ""),
        "DASHA_ANALYSIS_DOT_409_BASE64": images.get("dasha_analysis_dot_409", ""),
        "DASHA_ANALYSIS_DOT_415_BASE64": images.get("dasha_analysis_dot_415", ""),
        # Yogas page images
        "YOGAS_BG_STARS_BASE64": images.get("yogas_bg_stars", ""),
        "YOGAS_BG_BLUR_BASE64": images.get("yogas_bg_blur", ""),
        "YOGAS_BG_DECO_BASE64": images.get("yogas_bg_deco", ""),
        "BG_MAIN_BASE64": images.get("bg_main", ""),
        "BG_DECO_BASE64": images.get("bg_deco", ""),
        "BLUR_1_BASE64": images.get("blur_1", ""),
        "BLUR_2_BASE64": images.get("blur_2", ""),
        "BLUR_3_BASE64": images.get("blur_3", ""),
        "ICON_BG_1_BASE64": images.get("icon_bg_1", ""),
        "ICON_BG_2_BASE64": images.get("icon_bg_2", ""),
        "ICON_MAIN_BASE64": images.get("icon_main", ""),
        "LOGO_BASE64": images.get("logo", ""),
        "CHARTS_BG_BASE64": images.get("charts_bg", ""),
        # Remedies page images
        "REMEDIES_BG_MAIN_BASE64": images.get("remedies_bg_main", ""),
        "REMEDIES_BG_BLUR_BASE64": images.get("remedies_bg_blur", ""),
        "TITLE_DECORATION_BASE64": images.get("remedies_title_decoration", ""),
        "REMEDY_1_IMAGE_BASE64": images.get("remedy_1_image", ""),
        "REMEDY_2_IMAGE_BASE64": images.get("remedy_2_image", ""),
        "REMEDY_3_IMAGE_BASE64": images.get("remedy_3_image", ""),
        "REMEDY_4_BG_IMAGE_BASE64": images.get("remedy_4_bg_image", ""),
        "REMEDY_4_FG_IMAGE_BASE64": images.get("remedy_4_fg_image", ""),
        # Ashtakavarga page images (using unique names to avoid conflicts)
        "ASHTAKAVARGA_BG_STARS_BASE64": images.get("ashtakavarga_bg_stars", ""),
        "ASHTAKAVARGA_BG_BLUR_BASE64": images.get("ashtakavarga_bg_blur", ""),
        "ASHTAKAVARGA_TITLE_DIVIDER_BASE64": images.get("ashtakavarga_title_divider", ""),
        "ASHTAKAVARGA_MESHA_ILLUSTRATION_BASE64": images.get("ashtakavarga_mesha_illustration", ""),
        "ASHTAKAVARGA_MOON_ICON_BASE64": images.get("ashtakavarga_moon_icon", ""),
        "ASHTAKAVARGA_SUN_ICON_BASE64": images.get("ashtakavarga_sun_icon", ""),
        "ASHTAKAVARGA_MERCURY_ICON_BASE64": images.get("ashtakavarga_mercury_icon", ""),
        "ASHTAKAVARGA_VENUS_ICON_BASE64": images.get("ashtakavarga_venus_icon", ""),
        "ASHTAKAVARGA_MARS_ICON_BASE64": images.get("ashtakavarga_mars_icon", ""),
        "ASHTAKAVARGA_JUPITER_ICON_BASE64": images.get("ashtakavarga_jupiter_icon", ""),
        "ASHTAKAVARGA_SATURN_ICON_BASE64": images.get("ashtakavarga_saturn_icon", ""),
        # Also add backward compatible names for templates that use BG_STARS_BASE64
        "BG_STARS_BASE64": images.get("ashtakavarga_bg_stars", ""),
        "TITLE_DIVIDER_BASE64": images.get("ashtakavarga_title_divider", ""),
        "MESHA_ILLUSTRATION_BASE64": images.get("ashtakavarga_mesha_illustration", ""),
        "MOON_ICON_BASE64": images.get("ashtakavarga_moon_icon", ""),
        "SUN_ICON_BASE64": images.get("ashtakavarga_sun_icon", ""),
        "MERCURY_ICON_BASE64": images.get("ashtakavarga_mercury_icon", ""),
        "VENUS_ICON_BASE64": images.get("ashtakavarga_venus_icon", ""),
        "MARS_ICON_BASE64": images.get("ashtakavarga_mars_icon", ""),
        "JUPITER_ICON_BASE64": images.get("ashtakavarga_jupiter_icon", ""),
        "SATURN_ICON_BASE64": images.get("ashtakavarga_saturn_icon", ""),
        
        # Rashi illustrations for Ashtakavarga table
        "MESHA_ILLUSTRATION_BASE64": images.get("mesha_illustration", ""),
        "VRISHABHA_ILLUSTRATION_BASE64": images.get("vrishabha_illustration", ""),
        "MITHUNA_ILLUSTRATION_BASE64": images.get("mithuna_illustration", ""),
        "KARKA_ILLUSTRATION_BASE64": images.get("karka_illustration", ""),
        "SIMHA_ILLUSTRATION_BASE64": images.get("simha_illustration", ""),
        "KANYA_ILLUSTRATION_BASE64": images.get("kanya_illustration", ""),
        "TULA_ILLUSTRATION_BASE64": images.get("tula_illustration", ""),
        "VRISHCHIKA_ILLUSTRATION_BASE64": images.get("vrishchika_illustration", ""),
        "DHANU_ILLUSTRATION_BASE64": images.get("dhanu_illustration", ""),
        "MAKARA_ILLUSTRATION_BASE64": images.get("makara_illustration", ""),
        "KUMBHA_ILLUSTRATION_BASE64": images.get("kumbha_illustration", ""),
        "MEENA_ILLUSTRATION_BASE64": images.get("meena_illustration", ""),
        
        # Planet icons for Ashtakavarga
        "MOON_ICON_BASE64": images.get("moon_icon", ""),
        "SUN_ICON_BASE64": images.get("sun_icon", ""),
        "MERCURY_ICON_BASE64": images.get("mercury_icon", ""),
        "VENUS_ICON_BASE64": images.get("venus_icon", ""),
        "MARS_ICON_BASE64": images.get("mars_icon", ""),
        "JUPITER_ICON_BASE64": images.get("jupiter_icon", ""),
        "SATURN_ICON_BASE64": images.get("saturn_icon", ""),
        
        # Ashtakavarga background elements (matching user-profile structure)
        "BG_MAIN_BASE64": images.get("ashtakavarga_bg_stars", ""),
        "BG_DECO_BASE64": images.get("ashtakavarga_bg_blur", ""),
        "LOGO_BASE64": images.get("ashtakavarga_bg_blur", ""),  # Using same as BG_DECO for now
        "BLUR_1_BASE64": images.get("ashtakavarga_bg_stars", ""),  # Using stars for blur effects
        "BLUR_2_BASE64": images.get("ashtakavarga_bg_blur", ""),
        "BLUR_3_BASE64": images.get("ashtakavarga_title_divider", ""),
    }
    
    # Add dynamic Ashtakavarga context variables
    # Get user's Moon sign (birth_rasi) dynamically
    rashi_name = "Mesha"  # Default fallback
    moon_sign_house = 1  # Default to House 1
    
    if final_output.user_profile2 and final_output.user_profile2.birth_rasi:
        rashi_name = final_output.user_profile2.birth_rasi
        # Map rashi name to house number (based on zodiac order)
        rashi_to_house = {
            "Mesha": 1, "Aries": 1,
            "Vrishabha": 2, "Taurus": 2,
            "Mithuna": 3, "Gemini": 3,
            "Karka": 4, "Cancer": 4,
            "Simha": 5, "Leo": 5,
            "Kanya": 6, "Virgo": 6,
            "Tula": 7, "Libra": 7,
            "Vrishchika": 8, "Scorpio": 8,
            "Dhanu": 9, "Sagittarius": 9,
            "Makara": 10, "Capricorn": 10,
            "Kumbha": 11, "Aquarius": 11,
            "Meena": 12, "Pisces": 12
        }
        moon_sign_house = rashi_to_house.get(rashi_name, 1)
    
    # Get user's Ascendant (Lagna) dynamically
    lagna_name = "Simha"  # Default fallback
    if final_output.user_profile2 and final_output.user_profile2.lagna:
        lagna_name = final_output.user_profile2.lagna
    
    # Filter Ashtakavarga data to show points for Moon sign house only
    filtered_ashtakavarga_data = None
    total_points = 0
    
    if final_output.ashtakavarga and final_output.ashtakavarga.data:
        # Create filtered data showing points for Moon sign house
        filtered_planets = []
        for planet_data in final_output.ashtakavarga.data:
            house_key = f"House{moon_sign_house}"
            moon_house_points = planet_data.house_wise_points.get(house_key, 0)
            
            # Create new planet data with moon house points as total
            filtered_planet = {
                "planet": planet_data.planet,
                "house_wise_points": planet_data.house_wise_points,
                "total_points": moon_house_points  # Use moon sign house points
            }
            filtered_planets.append(filtered_planet)
            total_points += moon_house_points
        
        # Create filtered ashtakavarga response
        from kundli.divineapi.intermediate_models import AshtakavargaResponse, PlanetAshtakavarga
        filtered_data_obj = []
        for fp in filtered_planets:
            filtered_data_obj.append(PlanetAshtakavarga(**fp))
        
        filtered_ashtakavarga_data = AshtakavargaResponse(
            success=1,
            data=filtered_data_obj,
            total_points=final_output.ashtakavarga.total_points
        )
    
    # Override ashtakavarga data with filtered version
    if filtered_ashtakavarga_data:
        data_dict["ashtakavarga"] = filtered_ashtakavarga_data
    
    # Add to context for ashtakavarga.html include
    context["rashi_name"] = rashi_name
    context["footnote"] = f"*Planetary Position in {rashi_name}.<br>Lagna in {lagna_name}."
    context["title"] = "AshtakaVarga Predictions"
    context["total_points"] = total_points
    
    # Render template with image data in context
    html_content = template.render(context)
    
    return html_content

def render_ashtakavarga_html(final_output: FinalAstroOutput) -> str:
    """Render ashtakavarga HTML with proper data mapping and filtering for Moon sign."""
    template = env.get_template("ashtakavarga.html")
    
    # Build template data
    template_data = _build_template_data(final_output)
    
    # Get user's Moon sign (birth_rasi) dynamically
    rashi_name = "Mesha"  # Default fallback
    moon_sign_house = 1  # Default to House 1
    
    if final_output.user_profile2 and final_output.user_profile2.birth_rasi:
        rashi_name = final_output.user_profile2.birth_rasi
        # Map rashi name to house number (based on zodiac order)
        rashi_to_house = {
            "Mesha": 1, "Aries": 1,
            "Vrishabha": 2, "Taurus": 2,
            "Mithuna": 3, "Gemini": 3,
            "Karka": 4, "Cancer": 4,
            "Simha": 5, "Leo": 5,
            "Kanya": 6, "Virgo": 6,
            "Tula": 7, "Libra": 7,
            "Vrishchika": 8, "Scorpio": 8,
            "Dhanu": 9, "Sagittarius": 9,
            "Makara": 10, "Capricorn": 10,
            "Kumbha": 11, "Aquarius": 11,
            "Meena": 12, "Pisces": 12
        }
        moon_sign_house = rashi_to_house.get(rashi_name, 1)
    
    # Get user's Ascendant (Lagna) dynamically
    lagna_name = "Simha"  # Default fallback
    if final_output.user_profile2 and final_output.user_profile2.lagna:
        lagna_name = final_output.user_profile2.lagna
    
    # Get user's name dynamically
    user_name = "H. Gurumurthy"  # Default fallback
    if final_output.user_profile1 and final_output.user_profile1.name:
        user_name = final_output.user_profile1.name

    # Filter Ashtakavarga data to show points for Moon sign house only
    total_points = 0
    if final_output.ashtakavarga and final_output.ashtakavarga.data:
        # Create filtered data showing points for Moon sign house
        filtered_planets = []
        for planet_data in final_output.ashtakavarga.data:
            house_key = f"House{moon_sign_house}"
            moon_house_points = planet_data.house_wise_points.get(house_key, 0)
            
            # Create new planet data with moon house points as total
            filtered_planet = {
                "planet": planet_data.planet,
                "house_wise_points": planet_data.house_wise_points,
                "total_points": moon_house_points  # Use moon sign house points
            }
            filtered_planets.append(filtered_planet)
            total_points += moon_house_points
        
        # Create filtered ashtakavarga response
        from kundli.divineapi.intermediate_models import AshtakavargaResponse, PlanetAshtakavarga
        filtered_data_obj = []
        for fp in filtered_planets:
            filtered_data_obj.append(PlanetAshtakavarga(**fp))
        
        # Override template data with filtered version
        template_data["ashtakavarga"] = AshtakavargaResponse(
            success=1,
            data=filtered_data_obj,
            total_points=final_output.ashtakavarga.total_points
        )

    context = {
        "data": template_data,
        "images": _get_images_context(),
        "total_points": total_points,
        "title": "AshtakaVarga Predictions",
        "rashi_name": rashi_name,  # Now dynamic based on user's Moon sign
        "footnote": f"*Planetary Position in {rashi_name}.<br>Lagna in {lagna_name}.",  # Dynamic
        "author_name": user_name,  # Dynamic user name
        "page_number": "1 / 20"
    }
    return template.render(context)

def render_yogas_html(final_output: FinalAstroOutput) -> str:
    """Render Yogas HTML with proper data mapping and logo positioning."""
    template = env.get_template("yogas.html")
    
    # Build template data
    template_data = _build_template_data(final_output)
    
    # Get user name for author
    user_name = "User"
    if final_output.user_profile1 and final_output.user_profile1.name:
        user_name = final_output.user_profile1.name
    
    # Get yoga data
    yoga_data = {
        "name": "Sample Yoga",
        "description": "This is a sample yoga description."
    }
    
    if final_output.yogas:
        yoga_data = {
            "name": final_output.yogas.title or "Sample Yoga",
            "description": final_output.yogas.description or "This is a sample yoga description."
        }
    
    context = {
        "data": template_data,
        "images": _get_images_context(),
        "yoga_data": yoga_data,
        "author_name": user_name,
        "page_data": {"page_number": "13 / 20"}
    }
    return template.render(context)
