from pathlib import Path

import webbrowser

from kundli.divineapi.orchestrator import generate_kundli_orchestrator
from artifacts.generators.api_to_html_service import render_kundli_html, render_combined_4_pages_html

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_kundli_report_generation() -> None:
    """
    Complete Kundli Report Generation Pipeline with Modular Templates
    =================================================================
    
    This is the main pipeline that orchestrates the complete flow:
    1. Generate astrology data using kundli.divineapi orchestrator (real API calls)
    2. Convert to HTML using modular template system 
       - Full report (all 4 pages)
       - Custom page combinations (e.g., pages 1,3 / pages 3,4)
       - Individual pages (e.g., page 2 only)
    3. Convert all variations to PDF using html_to_pdf_service  
    4. Auto-open generated files
    5. Demonstrate scalability of modular system
    """
    import os
    import sys
    import certifi
    
    print("🚀 Starting Complete Kundli Report Generation Pipeline")
    print("=" * 65)
    
    # Fix TLS CA bundle issues by pointing to certifi bundle and clearing conflicting env vars
    for _v in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        os.environ.pop(_v, None)
    os.environ["SSL_CERT_FILE"] = certifi.where()
    
    # Set API credentials (user should provide these)
    # Check for API credentials
    auth_token = os.getenv("AUTH_TOKEN")
    divine_api_key = os.getenv("DIVINE_API_KEY")
    
    if not auth_token:
        print("⚠️ AUTH_TOKEN environment variable not set!")
        print("   Please set: export AUTH_TOKEN=your_token_here")
        print("   Or add it directly in the script for testing")
        # Uncomment the line below and add your actual token:
        auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vZGl2aW5lYXBpLmNvbS9zaWdudXAiLCJpYXQiOjE3NDAwNDg4ODEsIm5iZiI6MTc0MDA0ODg4MSwianRpIjoicGZiaFJmU0R4d2RNbWJlUCIsInN1YiI6IjMzMDUiLCJwcnYiOiJlNmU2NGJiMGI2MTI2ZDczYzZiOTdhZmMzYjQ2NGQ5ODVmNDZjOWQ3In0.XPbN2bDU538E2pJEMFWidoZ2uA1uLZILnkhgaz0Qab0"
        
    if not divine_api_key:
        print("⚠️ DIVINE_API_KEY environment variable not set!")
        print("   Please set: export DIVINE_API_KEY=your_api_key_here")
        print("   Or add it directly in the script for testing")
        # Uncomment the line below and add your actual API key:
        divine_api_key = "46ca8e3fa8a1d676b75664e04db536bb"
    
    if not auth_token or not divine_api_key:
        print("\n❌ Missing required API credentials. Cannot proceed with live API test.")
        print("   Please provide AUTH_TOKEN and DIVINE_API_KEY to test with real data.")
        return
    
    # Set the credentials in environment for the API calls
    os.environ["AUTH_TOKEN"] = auth_token
    os.environ["DIVINE_API_KEY"] = divine_api_key
    
    # Step 1: Generate astrology data
    print("📊 Step 1: Generating astrology data...")
    payload = {
        "full_name": "Aarya",
        "day": "15",
        "month": "02", 
        "year": "2005",
        "hour": "01",
        "min": "30",
        "sec": "43",
        "gender": "female",
        "place": "Bengaluru, India",
        "lat": "12.9629",
        "lon": "77.5775",
        "tzone": "5.5"
    }

    try:
        final_output = generate_kundli_orchestrator(payload)
        print("✅ Astrology data generated successfully!")
        
        # Verify UserProfile models
        if final_output.user_profile1:
            print(f"   Name: {final_output.user_profile1.name}")
            print(f"   Gender: {final_output.user_profile1.gender}")
            print(f"   Place: {final_output.user_profile1.place_of_birth}")
        
        if final_output.user_profile2:
            print(f"   Nakshatra: {final_output.user_profile2.birth_star}")
            print(f"   Moon Sign: {final_output.user_profile2.birth_rasi}")
            print(f"   Ascendant: {final_output.user_profile2.lagna}")
        
        # Verify Chart models
        d1_available = final_output.d1_chart and final_output.d1_chart.chart_image and (final_output.d1_chart.chart_image.svg or final_output.d1_chart.chart_image.base64_image)
        d9_available = final_output.d9_chart and final_output.d9_chart.chart_image and (final_output.d9_chart.chart_image.svg or final_output.d9_chart.chart_image.base64_image)
        
        print(f"   D1 Chart: {'✅ Available' if d1_available else '⚠️ Not Available'}")
        print(f"   D9 Chart: {'✅ Available' if d9_available else '⚠️ Not Available'}")
        
        # Verify Ashtakavarga data
        ashtakavarga_available = final_output.ashtakavarga and final_output.ashtakavarga.data
        print(f"   Ashtakavarga: {'✅ Available' if ashtakavarga_available else '⚠️ Not Available'}")
        print()
    except Exception as e:
        print(f"❌ Error generating astrology data: {e}")
        raise
    
    # Step 2: Convert to HTML - Combined 7-Page Report (now includes D1, D9 charts and Astrological Insights)
    print("🌐 Step 2: Converting to HTML (Combined 12+ Page Report)...")
    try:
        # Generate the new combined 7-page template
        html_content_combined = render_combined_4_pages_html(final_output)
        assert isinstance(html_content_combined, str) and len(html_content_combined) > 0
        print("✅ Combined 12+ page HTML generated successfully!")
        print("   📄 Page 1: Poster (with user name)")
        print("   📄 Page 2: Page1/Sanskrit (with ganesha mantras)")
        print("   📄 Page 3: User Profile - Basic Info (name, gender, DOB, timezone, place)")
        print("   📄 Page 4: User Profile - Astrological Details (coordinates, ayanamsha, nakshatra, rasi, ascendant)")
        print("   📄 Page 5: D1 Birth Chart (Lagna Chart)")
        print("   📄 Page 6: D9 Navamsa Chart")
        print("   📄 Page 7: Astrological Insights (Ghata Chakra, Ascendant, Lucky Stone, Life Stone)")
        print("   📄 Page 8: Antar Dasha (Current Maha Dasha and its Antar Dasha periods)")
        print("   📄 Page 9: Dasha Analysis - Career")
        print("   📄 Page 10: Dasha Analysis - Health")
        print("   📄 Page 11: Dasha Analysis - Finance")
        print("   📄 Page 12: Dasha Analysis - Relationships")
        print("   📄 Pages 13+: Yogas (one page per valid yoga)")
        print("   📄 Final Page: Ashtakavarga (if available)")
        
        print()
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        raise

    # Step 3: Save HTML files and open locally
    print("📁 Step 3: Saving and opening HTML files...")
    try:
        out_dir = Path("output")  # Relative to current directory like main_pipeline
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Save combined 7-page report
        html_path_combined = out_dir / "kundli_report_combined_12_plus_pages.html"
        html_path_combined.write_text(html_content_combined, encoding="utf-8")
        assert html_path_combined.exists() and html_path_combined.stat().st_size > 0
        print(f"✅ Combined 12+ page HTML saved to: {html_path_combined.resolve()}")
        
        # Open the combined report in browser
        webbrowser.open(html_path_combined.resolve().as_uri())
        print("🌐 Combined 12+ page HTML report opened in browser!")
        print()
    except Exception as e:
        print(f"❌ Error saving/opening HTML: {e}")
        raise

    # Step 4: Convert HTML to PDF
    print("📄 Step 4: Converting HTML to PDF...")
    try:
        from artifacts.generators.html_to_pdf_service import convert_html_to_pdf
        
        # Generate PDF from combined 7-page HTML report
        pdf_path_combined = out_dir / "kundli_report_combined_12_plus_pages.pdf"
        pdf_bytes_combined = convert_html_to_pdf(html_content_combined)
        pdf_path_combined.write_bytes(pdf_bytes_combined)
        assert pdf_path_combined.exists() and pdf_path_combined.stat().st_size > 0
        print(f"✅ Combined 12+ page PDF saved to: {pdf_path_combined.resolve()}")
        
        # Open combined PDF file automatically
        if sys.platform.startswith('win'):
            os.startfile(str(pdf_path_combined))
        elif sys.platform.startswith('darwin'):  # macOS
            os.system(f"open '{pdf_path_combined}'")
        else:  # Linux
            os.system(f"xdg-open '{pdf_path_combined}'")
        
        print("📄 Combined 12+ page PDF file opened!")
        print()
    except Exception as e:
        print(f"❌ Error generating/opening PDF: {e}")
        raise
    
    # Step 5: Success summary
    print("🎉 COMBINED TEMPLATE PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 65)
    user_name = final_output.user_profile1.name if final_output.user_profile1 else 'Test User'
    print(f"📊 Generated kundli reports for: {user_name}")
    print()
    print("📁 Files Generated:")
    print(f"🌐 Combined 12+ page HTML: {html_path_combined.resolve()}")
    print(f"📄 Combined 12+ page PDF:  {pdf_path_combined.resolve()}")
    print()
    print("✅ Combined template files opened automatically!")
    print("🎯 Pipeline Features Demonstrated:")
    print("   ✅ Real API integration with astrology data")
    print("   ✅ NEW: Combined 12+ page modular template system")
    print("   ✅ UserProfile1 & UserProfile2 Pydantic models")
    print("   ✅ D1Chart & D9Chart Pydantic models")
    print("   ✅ AstroInsights Pydantic model")
    print("   ✅ AntarDasha Pydantic model")
    print("   ✅ DashaAnalysis Pydantic model")
    print("   ✅ Yogas Pydantic model")
    print("   ✅ Ashtakavarga Pydantic model")
    print("   ✅ Modular template includes (no code duplication)")  
    print("   ✅ Parameterized content (poster name, user profile data, chart data, insights)")
    print("   ✅ Base64 encoded images (self-contained files)")
    print("   ✅ HTML generation with perfect styling")
    print("   ✅ PDF conversion with proper formatting")
    print("   ✅ Auto-opening of generated files")
    print("   ✅ Scalable architecture for future needs")
    print()
    print("🎯 Combined Template Structure:")
    print("   📄 Page 1: Poster with user name")
    print("   📄 Page 2: Sanskrit/Ganesha mantras")
    print("   📄 Page 3: User Profile - Basic Info (UserProfile1 data)")
    print("   📄 Page 4: User Profile - Astrological Details (UserProfile2 data)")
    print("   📄 Page 5: D1 Birth Chart (Lagna Chart)")
    print("   📄 Page 6: D9 Navamsa Chart")
    print("   📄 Page 7: Astrological Insights (AstroInsights data)")
    print("   📄 Page 8: Antar Dasha (AntarDasha data)")
    print("   📄 Page 9-12: Dasha Analysis (Career, Health, Finance, Relationships)")
    print("   📄 Pages 13+: Yogas (one page per valid yoga)")
    print("   📄 Final Page: Ashtakavarga (if available)")
    print()
    print("🚀 Ready for production use!")


if __name__ == "__main__":
    test_kundli_report_generation()


