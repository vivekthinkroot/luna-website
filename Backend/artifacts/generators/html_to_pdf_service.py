from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from typing import Union
from pathlib import Path
import os
import re

def convert_html_to_pdf(html_content_or_data, output_path: Union[Path, None] = None) -> Union[bytes, None]:
    """
    Converts HTML string to PDF bytes using WeasyPrint with optimizations for design accuracy.
    
    Args:
        html_content_or_data: Either HTML string or data object (for compatibility with main_pipeline)
        output_path: Optional path to save PDF file directly (for compatibility with main_pipeline)
    
    Returns:
        PDF bytes if output_path is None, otherwise saves to file and returns None
    """
    # Handle both patterns: direct HTML string or data object
    if isinstance(html_content_or_data, str):
        html_content = html_content_or_data
    else:
        # If it's a data object, we need to generate HTML first
        from .api_to_html_service import render_kundli_html
        html_content = render_kundli_html(html_content_or_data)
    
    # Apply WeasyPrint-specific optimizations
    html_content = _optimize_html_for_weasyprint(html_content)
    
    # Configure font handling for better font support
    font_config = FontConfiguration()
    
    # Create CSS for WeasyPrint-specific optimizations
    weasyprint_css = CSS(string="""
        /* Page configuration for proper PDF generation - FORCE FULL PAGE */
        @page {
            size: A4;
            margin: 0;
            background: #000;
        }
        
        /* Override page sizing to use full A4 dimensions */
        body {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .page {
            width: 210mm !important;
            height: 297mm !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
            page-break-after: always !important;
            break-after: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            overflow: hidden !important;
            position: relative !important;
            background-size: 210mm 297mm !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-clip: border-box !important;
        }
        
        .page:last-child {
            page-break-after: auto !important;
            break-after: auto !important;
        }
        
        /* Prevent content overflow and data overlap - REDUCED SIDE PADDING, NO TOP PADDING */
        .page-content {
            width: 100% !important;
            height: 100% !important;
            overflow: hidden !important;
            position: relative !important;
            z-index: 1 !important;
            padding: 0 5mm 15mm 5mm !important;
            box-sizing: border-box !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-center !important;
            align-items: center !important;
        }
        
        /* Fix for backdrop-filter not supported - use opacity instead */
        .remedy-box, .tab-content, .table-container, .ashtakavarga-container {
            backdrop-filter: none !important;
            background: rgba(255, 255, 255, 0.15) !important;
        }
        
        /* Fix for webkit-specific text gradient - use solid color fallback */
        .in-depth, .horoscope {
            -webkit-background-clip: unset !important;
            -webkit-text-fill-color: unset !important;
            color: #ffd769 !important;
            background: none !important;
        }
        
        /* Improve font rendering */
        body, * {
            font-family: 'Arial', 'Helvetica', sans-serif !important;
        }
        
        /* Ensure images are properly sized */
        img {
            max-width: 100%;
            height: auto;
        }
        
        
        /* Specific styling for remedies page image */
        .remedies-page img {
            width: 40% !important;
            height: auto !important;
            max-width: 40% !important;
            margin-top: 0 !important;
        }
        
        /* Remedies page title and image spacing */
        .remedies-page .timeline-title {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        .remedies-page div[style*="text-align: center"] {
            margin-bottom: 0 !important;
        }
        
        /* Birth chart styling for PDF - More aggressive rules */
        .chart-page svg text, .chart-page svg tspan { 
            fill: #ffffff !important;
            stroke: none !important; 
        }
        .chart-page svg path, .chart-page svg line, .chart-page svg rect, .chart-page svg circle, .chart-page svg polygon { 
            stroke: #ad80fe !important; 
            fill: transparent !important; 
        }
        .chart-page svg * { 
            fill: #ad80fe !important; 
            stroke: #ad80fe !important; 
        }
        
        /* Universal SVG styling for PDF - override all SVG colors */
        svg text, svg tspan { 
            fill: #ad80fe !important; 
        }
        svg path, svg line, svg rect, svg circle, svg polygon { 
            stroke: #ad80fe !important; 
            fill: transparent !important; 
        }
        svg * { 
            fill: #ad80fe !important; 
            stroke: #ad80fe !important; 
        }
        
        /* Override specific color attributes */
        svg [fill="black"], svg [fill="#000000"], svg [fill="#000"] { 
            fill: #ad80fe !important; 
        }
        svg [stroke="black"], svg [stroke="#000000"], svg [stroke="#000"] { 
            stroke: #ad80fe !important; 
        }
        
        /* Specifically target text inside SVG charts */
        svg text { 
            fill: #ad80fe !important; 
            color: #ad80fe !important; 
        }
        svg tspan { 
            fill: #ad80fe !important; 
            color: #ad80fe !important; 
        }
        
        /* Override any text color attributes in SVG */
        svg text[fill], svg tspan[fill] { 
            fill: #ad80fe !important; 
        }
        svg text[color], svg tspan[color] { 
            color: #ad80fe !important; 
        }
        
        /* Ensure tables don't break across pages */
        table {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }
        
        /* Prevent orphaned content */
        .antar-dasha-container, .ashtakavarga-container {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }
        
        /* Force content to stay within page bounds and fix overlaps */
        * {
            max-width: 100% !important;
        }
        
        /* FIXED BACKGROUND SIZE - Each page background exactly A4 size */
        .page {
            background-size: 210mm 297mm !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-clip: border-box !important;
            contain: layout style paint !important;
        }
        
        /* Ensure page content doesn't affect background */
        .page-content {
            contain: layout style paint !important;
            z-index: 1 !important;
        }
        
        /* Prevent any content from extending beyond page boundaries */
        .page * {
            max-height: 297mm !important;
            max-width: 210mm !important;
        }
        
        /* Ensure full page utilization for all content */
        .page > div {
            width: 100% !important;
            height: 100% !important;
        }
        
        /* Remove top margin/padding from content containers */
        .ashtakavarga-container, .antar-dasha-container, .table-container, .gemstone-container {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Ensure headers start from top */
        .ashtakavarga-header, .antar-dasha-header, .gemstone-header {
            margin-top: 0 !important;
            padding-top: 10px !important;
        }
        
        /* Ensure proper spacing between elements */
        .favourable-page .page-content > div,
        .saturn-page .page-content > div,
        .mercury-page .page-content > div {
            margin-bottom: 5px !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Expand content boxes for specific pages */
        .favourable-page div[style*="width: 90%"],
        .favourable-page div[style*="max-width: 600px"] {
            width: 95% !important;
            max-width: none !important;
        }
        
        .saturn-page div[style*="width: 600px"],
        .mercury-page div[style*="width: 600px"] {
            width: 95% !important;
            max-width: 100% !important;
            padding: 15px !important;
        }
        
        /* Remedies page optimization - CONTENT WRAPPING BOXES */
        .remedies-page .page-content {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            padding: 20px !important;
        }
        
        .remedies-page .remedies-grid {
            width: 90% !important;
            max-width: 90% !important;
            padding: 10px !important;
            margin: 20px auto 0 !important;
            height: auto !important;
            grid-template-rows: auto auto !important;
            align-items: start !important;
        }
        
        .remedies-page .remedy-box {
            width: 100% !important;
            max-width: 100% !important;
            padding: 15px !important;
            margin: 5px 0 !important;
            height: auto !important;
            min-height: fit-content !important;
            overflow: visible !important;
        }
        
        /* Yogas page optimization - start from top */
        .tab-view-page .yoga-container {
            justify-content: flex-start !important;
            padding: 10px !important;
            margin-top: 100px !important;
        }
        
        .tab-view-page .yoga-header-box {
            margin-top: 20px !important;
            margin-bottom: 20px !important;
        }
        
        /* Ensure proper text scaling in expanded boxes */
        .favourable-page p, .saturn-page p, .mercury-page p {
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        
        /* Prevent text overflow */
        p, h1, h2, h3, h4, h5, h6 {
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
    """)
    
    # Get the base path for resolving relative URLs
    base_path = Path(__file__).parent.parent / "template"
    base_url = f"file://{base_path.absolute()}/"
    
    if output_path:
        # Save directly to file (main_pipeline pattern)
        HTML(string=html_content, base_url=base_url).write_pdf(
            str(output_path), 
            stylesheets=[weasyprint_css],
            font_config=font_config,
            optimize_images=True
        )
        return None
    else:
        # Return bytes (current test pattern)  
        pdf_io = BytesIO()
        HTML(string=html_content, base_url=base_url).write_pdf(
            pdf_io, 
            stylesheets=[weasyprint_css],
            font_config=font_config,
            optimize_images=True
        )
        pdf_io.seek(0)
        return pdf_io.read()

def _optimize_html_for_weasyprint(html_content: str) -> str:
    """
    Optimize HTML content for better WeasyPrint compatibility and prevent data overlap.
    """
    # Fix relative image paths to be absolute
    html_content = re.sub(
        r"url\(['\"]?\./reference_images/([^'\"]*)['\"]?\)",
        r"url('./reference_images/\1')",
        html_content
    )
    
    # Fix inline background-image styles with proper sizing
    html_content = re.sub(
        r"background-image:\s*url\(['\"]?\./reference_images/([^'\"]*)['\"]?\)",
        r"background-image: url('./reference_images/\1'); background-size: 210mm 297mm; background-repeat: no-repeat; background-position: center center; background-clip: border-box;",
        html_content
    )
    
    # Remove or replace unsupported CSS properties
    # Replace backdrop-filter with transparency
    html_content = re.sub(
        r"backdrop-filter:\s*blur\([^;]*\);?",
        "background: rgba(255, 255, 255, 0.15);",
        html_content
    )
    
    # Fix webkit-specific gradient text
    html_content = re.sub(
        r"-webkit-background-clip:\s*text;\s*-webkit-text-fill-color:\s*transparent;",
        "color: #ffd769;",
        html_content
    )
    
    # Fix margin issues that can cause data overlap - preserve centering
    html_content = re.sub(
        r'margin:\s*20px\s+auto;?',
        'margin: 0 auto;',
        html_content
    )
    
    # Ensure all page elements have proper containment with fixed background size
    html_content = re.sub(
        r'(<div[^>]*class="page"[^>]*>)',
        r'\1<div style="position: relative; overflow: hidden; width: 100%; height: 100%; background-size: 210mm 297mm; background-repeat: no-repeat; background-position: center center; background-clip: border-box;">',
        html_content
    )
    
    # Close the containment div before each page ends
    html_content = re.sub(
        r'(</div>\s*<!-- [^>]*page[^>]*-->)',
        r'</div>\1',
        html_content
    )
    
    # Replace black colors in SVG with purple for birth charts
    html_content = re.sub(
        r'stroke="black"',
        'stroke="#ad80fe"',
        html_content
    )
    html_content = re.sub(
        r'fill="black"',
        'fill="#ad80fe"',
        html_content
    )
    html_content = re.sub(
        r'stroke="#000000"',
        'stroke="#ad80fe"',
        html_content
    )
    html_content = re.sub(
        r'fill="#000000"',
        'fill="#ad80fe"',
        html_content
    )
    html_content = re.sub(
        r'stroke="#000"',
        'stroke="#ad80fe"',
        html_content
    )
    html_content = re.sub(
        r'fill="#000"',
        'fill="#ad80fe"',
        html_content
    )
    
    # Also replace RGB black colors
    html_content = re.sub(
        r'stroke="rgb\(0,0,0\)"',
        'stroke="#ad80fe"',
        html_content
    )
    html_content = re.sub(
        r'fill="rgb\(0,0,0\)"',
        'fill="#ad80fe"',
        html_content
    )
    
    
    
    return html_content
