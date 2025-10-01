import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { generateKundliDirect } from '../api';

// Dynamic import for html2pdf.js to avoid SSR issues
let html2pdf: any = null;

interface PaymentStatusResponse {
  status: 'paid' | 'pending';
  kundli_url?: string;
  message: string;
}

const KundliRedirect: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Kundali generation state
  const [generating, setGenerating] = useState(false);
  const [kundliHtml, setKundliHtml] = useState<string>('');
  const [kundliGenerated, setKundliGenerated] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [generatedHtmlForPdf, setGeneratedHtmlForPdf] = useState<string>(''); // Store HTML for PDF download

  // Extract user_id from URL parameters
  // Handle both formats: ?user_id=xxx and ?razorpay_payment_link_reference_id=user123_1_timestamp
  let user_id = searchParams.get('user_id');
  
  // If user_id is not in the URL, try to extract from reference_id
  if (!user_id) {
    const reference_id = searchParams.get('razorpay_payment_link_reference_id');
    if (reference_id) {
      // Extract user_id from reference_id format: "user123_1_timestamp"
      const parts = reference_id.split('_');
      if (parts.length >= 1) {
        user_id = parts[0];
      }
    }
  }

  useEffect(() => {
    if (!user_id) {
      setError('User ID not found in URL parameters');
      setLoading(false);
      return;
    }

    const checkPaymentStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/payments/check-status?user_id=${user_id}`);
        const data = await response.json();
        
        if (response.ok) {
          setPaymentStatus(data);
        } else {
          setError(data.detail || 'Failed to check payment status');
        }
      } catch (err: any) {
        setError(err.message || 'Network error');
      } finally {
        setLoading(false);
      }
    };

    // Check status immediately (no polling needed since user is redirected after payment)
    checkPaymentStatus();
  }, [user_id]);

  const handleDownloadPdf = async () => {
    if (!generatedHtmlForPdf) {
      alert('⚠️ Please generate kundali first before downloading PDF');
      setError('Please generate kundali first before downloading PDF');
      return;
    }

    setDownloadingPdf(true);
    setError(null);
    
    try {
      console.log('Starting PDF conversion with html2pdf.js...');
      console.log('HTML content length:', generatedHtmlForPdf.length);
      
      // Dynamically import html2pdf.js only on client side
      if (!html2pdf) {
        // @ts-ignore - html2pdf.js doesn't have TypeScript definitions
        const html2pdfModule = await import('html2pdf.js');
        html2pdf = html2pdfModule.default;
      }
      
      // Create a temporary container for the HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = generatedHtmlForPdf;
      tempDiv.style.position = 'absolute';
      tempDiv.style.left = '-9999px';
      document.body.appendChild(tempDiv);
      
      // Configure html2pdf options
      const opt = {
        margin: 0,
        filename: `kundali_${new Date().getTime()}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
          scale: 2,
          useCORS: true,
          letterRendering: true,
          logging: false
        },
        jsPDF: { 
          unit: 'mm', 
          format: 'a4', 
          orientation: 'portrait' as const
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      };
      
      // Generate and download PDF
      await html2pdf().set(opt).from(tempDiv).save();
      
      // Clean up
      document.body.removeChild(tempDiv);
      
      console.log('PDF downloaded successfully with html2pdf.js!');
      alert('✅ Kundali PDF downloaded successfully!');
      
    } catch (err: any) {
      console.error('PDF download error:', err);
      const errorMessage = err.message || 'Failed to download PDF. Please try again.';
      setError(errorMessage);
      alert(`❌ PDF Download Failed\n\n${errorMessage}\n\nPlease try generating the kundali again.`);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleGenerateKundli = async () => {
    setGenerating(true);
    setError(null);

    try {
      // Get profile data from localStorage
      const horoscopeData = localStorage.getItem('horoscopeFormData');
      if (!horoscopeData) {
        setError('Profile data not found. Please fill the form first.');
        setGenerating(false);
        return;
      }

      const formData = JSON.parse(horoscopeData);
      
      // Get birthplace coordinates from localStorage
      const birthplace_lat = localStorage.getItem('birthplace_lat');
      const birthplace_lng = localStorage.getItem('birthplace_lng');
      
      if (!birthplace_lat || !birthplace_lng) {
        setError('Location coordinates not found. Please select a city from the dropdown.');
        setGenerating(false);
        return;
      }

      console.log("Form Data from localStorage:", formData);
      console.log("Birthplace Coordinates:", { lat: birthplace_lat, lng: birthplace_lng });

      // Prepare data for Divine API
      const kundliRequest = {
        name: formData.fullName || formData.name,
        gender: formData.gender,
        birth_datetime: formData.birth_datetime,
        birth_place: formData.birth_place,
        latitude: parseFloat(birthplace_lat),
        longitude: parseFloat(birthplace_lng)
      };

      console.log("Sending to Divine API:", kundliRequest);

      // Call the new direct generation endpoint
      const result = await generateKundliDirect(kundliRequest);
      
      console.log("Kundli generated successfully!");

      // Store HTML for PDF download
      setGeneratedHtmlForPdf(result.kundli_html);

      // Open kundli HTML in a new tab
      const newWindow = window.open('', '_blank');
      if (newWindow) {
        newWindow.document.write(result.kundli_html);
        newWindow.document.close();
        
        // Show success message
        setKundliGenerated(true);
        setError(null);
      } else {
        // Fallback: Display inline if popup was blocked
        setKundliHtml(result.kundli_html);
        setGeneratedHtmlForPdf(result.kundli_html); // Also store for PDF download
        setKundliGenerated(true);
      }

    } catch (err: any) {
      console.error('Kundali generation error:', err);
      setError(err.message || 'Failed to generate Kundali');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-white text-lg">Checking payment status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-6xl mb-4">⚠️</div>
          <h1 className="text-white text-2xl font-bold mb-4">Error</h1>
          <p className="text-gray-300 mb-6">{error}</p>
          <button
            onClick={() => window.location.href = '/kundli'}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Back to Kundli Page
          </button>
        </div>
      </div>
    );
  }

  if (paymentStatus?.status === 'paid') {
    // If kundali was generated and opened in new tab, show success
    if (kundliGenerated && !kundliHtml) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] flex items-center justify-center p-4">
          {/* Download PDF button at top right */}
          {generatedHtmlForPdf && (
            <div className="fixed top-4 right-4 z-50">
              <button
                onClick={handleDownloadPdf}
                disabled={downloadingPdf}
                className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {downloadingPdf ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Generating PDF...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>Download Your Kundali (PDF)</span>
                  </>
                )}
              </button>
            </div>
          )}
          
          <div className="text-center max-w-md mx-auto p-6">
            <div className="text-green-400 text-6xl mb-4">✨</div>
            <h1 className="text-white text-2xl font-bold mb-4">Kundali Generated!</h1>
            <p className="text-gray-300 mb-6">Your kundali has been generated and opened in a new tab.</p>
            
            <div className="bg-yellow-500/20 border border-yellow-500 rounded-lg p-4 mb-6">
              <p className="text-yellow-300 text-sm">
                📌 If the new tab didn't open, please allow popups for this site and try again.
              </p>
            </div>
            
            {/* Show download hint */}
            {generatedHtmlForPdf && (
              <div className="bg-blue-500/20 border border-blue-500 rounded-lg p-4 mb-6">
                <p className="text-blue-300 text-sm">
                  💡 Click "Download Your Kundali (PDF)" at the top right to save your kundali!
                </p>
              </div>
            )}
            
            <button
              onClick={handleGenerateKundli}
              disabled={generating}
              className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors mb-4 disabled:opacity-50"
            >
              Generate Again
            </button>
            
            <button
              onClick={() => window.location.href = '/'}
              className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              Go to Home
            </button>
          </div>
        </div>
      );
    }
    
    // If kundali HTML is available (popup was blocked), show it inline
    if (kundliGenerated && kundliHtml) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] p-4">
          <div className="max-w-6xl mx-auto">
            {/* Header with Download Button */}
            <div className="flex justify-between items-start mb-6">
              <div className="flex-1 text-center">
                <h1 className="text-4xl font-bold text-white mb-2">Your Kundali</h1>
                <p className="text-gray-300">Generated successfully! ✨</p>
                <p className="text-yellow-300 text-sm mt-2">(Popup was blocked - showing here instead)</p>
              </div>
              
              {/* Download PDF Button - Top Right */}
              <div className="ml-4">
                <button
                  onClick={handleDownloadPdf}
                  disabled={downloadingPdf}
                  className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                >
                  {downloadingPdf ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Generating PDF...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>Download PDF</span>
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* Kundali HTML Display */}
            <div className="bg-white rounded-lg p-6 mb-6 shadow-2xl">
              <div 
                className="kundli-html" 
                dangerouslySetInnerHTML={{ __html: kundliHtml }} 
              />
            </div>
            
            {/* Action Buttons */}
            <div className="flex justify-center gap-4 mb-6">
              <button
                onClick={() => {
                  setKundliGenerated(false);
                  setKundliHtml('');
                }}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                Generate New
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Show payment success and generate button
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] flex items-center justify-center p-4">
        {/* Download PDF button at top right - shown after kundali generated */}
        {generatedHtmlForPdf && (
          <div className="fixed top-4 right-4 z-50">
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloadingPdf ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Generating PDF...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Download Your Kundali (PDF)</span>
                </>
              )}
            </button>
          </div>
        )}
        
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-green-400 text-6xl mb-4">✅</div>
          <h1 className="text-white text-2xl font-bold mb-4">Payment Successful!</h1>
          <p className="text-gray-300 mb-6">{paymentStatus.message}</p>
          
          {/* Error message if any */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}
          
          {/* Generating state */}
          {generating ? (
            <div className="mb-4">
              <div className="inline-flex items-center space-x-2 text-white">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-400"></div>
                <span>Generating your Kundali...</span>
              </div>
              <p className="text-gray-400 text-sm mt-2">This may take a few moments</p>
            </div>
          ) : (
            <button
              onClick={handleGenerateKundli}
              disabled={generating}
              className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors mb-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Generate Kundali Now
            </button>
          )}
          
          <button
            onClick={() => window.location.href = '/kundli'}
            className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Back to Kundli Page
          </button>
        </div>
      </div>
    );
  }

  if (paymentStatus?.status === 'pending') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-yellow-400 text-6xl mb-4">⏳</div>
          <h1 className="text-white text-2xl font-bold mb-4">Payment Verification</h1>
          <p className="text-gray-300 mb-6">{paymentStatus.message}</p>
          <p className="text-sm text-gray-400">Please wait while we verify your payment.</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded-lg transition-colors"
          >
            Refresh Status
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] flex items-center justify-center">
      <div className="text-center">
        <div className="text-gray-400 text-6xl mb-4">❓</div>
        <h1 className="text-white text-2xl font-bold mb-4">Unknown Status</h1>
        <p className="text-gray-300 mb-6">Unable to determine payment status.</p>
        <button
          onClick={() => window.location.href = '/kundli'}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          Back to Kundli Page
        </button>
      </div>
    </div>
  );
};

export default KundliRedirect;
