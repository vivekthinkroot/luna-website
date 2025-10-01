import React, { useEffect, useState } from "react";
import { useLocation } from "react-router";
import { generateKundli, downloadKundliPdf, createPaymentLink } from "../api";

// Extend window type for Razorpay callback
declare global {
  interface Window {
    handleRazorpayPayment?: (response: any) => void;
  }
}

// Accept profile_id via props or location state
const KundliPage: React.FC<{ profile_id?: string }> = ({ profile_id }) => {
	const [kundliHtml, setKundliHtml] = useState<string>("");
	const [error, setError] = useState<string>("");
	const [loading, setLoading] = useState<boolean>(false);
	const [generated, setGenerated] = useState<boolean>(false);
	
	// Payment-related state
	const [user_id] = useState<string>("user-123"); // In real app, get from auth context
	
	// Pay Now button state
	const [payNowLoading, setPayNowLoading] = useState<boolean>(false);
	const [redirecting, setRedirecting] = useState<boolean>(false);
	
	// Form data from localStorage
	const [formData, setFormData] = useState<any>(null);

	// Get autoGenerate flag and profile_id from location state using React Router
	const location = useLocation();
	const autoGenerate = location.state?.autoGenerate;
	const effectiveProfileId = profile_id || location.state?.profile_id;

	// Load form data from localStorage on component mount
	useEffect(() => {
		const storedData = localStorage.getItem('horoscopeFormData');
		if (storedData) {
			try {
				const parsedData = JSON.parse(storedData);
				setFormData(parsedData);
				console.log('Loaded form data from localStorage:', parsedData);
			} catch (err) {
				console.error('Error parsing stored form data:', err);
			}
		}
	}, []);

	// Payment button is now a simple "Pay Now" button that calls handlePayNow

	const handleGenerate = async () => {
		const pid = effectiveProfileId;
		if (!pid) {
			setError("No profile ID provided.");
			return;
		}
		
		setLoading(true);
		setError("");
		setKundliHtml("");
		try {
			const data = await generateKundli(pid, user_id);
			setKundliHtml(data.kundli_html);
			setGenerated(true);
		} catch (err: any) {
			setError(err.message || "Failed to generate Kundli");
		} finally {
			setLoading(false);
		}
	};

	const handleDownload = async () => {
		if (!kundliHtml) {
			setError("No Kundli to download");
			return;
		}
		try {
			await downloadKundliPdf(kundliHtml);
		} catch (err: any) {
			setError(err.message || "Failed to download Kundli");
		}
	};

	// SKU ID 1 (basic plan) is hardcoded for the website

	const handlePayNow = async () => {
		try {
		  console.log("Pay Now button clicked");
		  setPayNowLoading(true);
		  setError("");
	  
		  console.log("Calling backend API…");
		  const result = await createPaymentLink(user_id, "1");
	  
		  console.log("Raw backend response:", result);
	  
		  if (!result.payment_url) {
			throw new Error("Payment URL not found in response");
		  }
	  
		  const paymentLink = result.payment_url;
	  
		  setRedirecting(true);
	  
		  setTimeout(() => {
			console.log("Redirecting to:", paymentLink);
			window.location.href = paymentLink;
		  }, 3000);
		} catch (err: any) {
		  console.error("Error creating payment link:", err);
		  setError(err.message || "Failed to create payment link");
		  setPayNowLoading(false);
		  setRedirecting(false);
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] p-4">
			<div className="max-w-4xl mx-auto">
				<div className="text-center mb-8">
					<h1 className="text-4xl font-bold text-white mb-4">Your Kundli</h1>
					<p className="text-gray-300">Generate your personalized Kundli</p>
				</div>

				{/* Form Data Display */}
				{formData && (
					<div className="bg-white/5 rounded-lg p-4 mb-6">
						<h3 className="text-lg text-white mb-3">Your Details</h3>
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
							<div>
								<span className="text-gray-400">Name:</span>
								<span className="text-white ml-2">{formData.name}</span>
							</div>
							<div>
								<span className="text-gray-400">Birth Date:</span>
								<span className="text-white ml-2">{formData.birthDate}</span>
							</div>
							<div>
								<span className="text-gray-400">Birth Time:</span>
								<span className="text-white ml-2">{formData.birthTime}</span>
							</div>
							<div>
								<span className="text-gray-400">Birth Place:</span>
								<span className="text-white ml-2">{formData.birthPlace}</span>
							</div>
							<div>
								<span className="text-gray-400">Gender:</span>
								<span className="text-white ml-2">{formData.gender}</span>
							</div>
						</div>
					</div>
				)}
				
				{/* Payment Section - Show when payment is required */}
				{!loading && (
					<div className="text-center mb-6">
						<div className="bg-white/5 rounded-lg p-6 mb-4">
							<h3 className="text-xl text-white mb-4">Complete Payment to Generate Kundli</h3>
							<div className="mb-4">
								<p className="text-gray-300 mb-4">Click the button below to complete your payment:</p>
								
								{/* Loading State */}
								{payNowLoading && (
									<button
										disabled
										className="px-6 py-3 bg-blue-400 text-white font-bold rounded-lg shadow-lg transition-all duration-300 opacity-75 cursor-not-allowed"
									>
										<div className="inline-flex items-center space-x-2">
											<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
											<span>Creating Payment Link...</span>
										</div>
									</button>
								)}
								
								{/* Redirecting State */}
								{redirecting && (
									<button
										disabled
										className="px-6 py-3 bg-green-500 text-white font-bold rounded-lg shadow-lg transition-all duration-300 opacity-75 cursor-not-allowed"
									>
										<div className="inline-flex items-center space-x-2">
											<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
											<span>Redirecting to Payment...</span>
										</div>
									</button>
								)}
								
								{/* Normal State */}
								{!payNowLoading && !redirecting && (
									<button
										onClick={handlePayNow}
										className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-lg shadow-lg transition-all duration-300"
									>
										Pay Now
									</button>
								)}
							</div>
							<div className="text-gray-300 text-sm mt-2">Secure payment powered by Razorpay</div>
						</div>
					</div>
				)}


				{/* Loading State */}
				{loading && (
					<div className="text-center">
						<div className="inline-flex items-center space-x-2 text-white">
							<div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-400"></div>
							<span>Generating your Kundli...</span>
						</div>
					</div>
				)}

				{/* Error Display */}
				{error && (
					<div className="text-center mb-4">
						<div className="bg-red-500/20 border border-red-500 rounded-lg p-4">
							<div className="text-red-400 font-semibold">{error}</div>
						</div>
					</div>
				)}


				{/* Kundli Display */}
				{kundliHtml && (
					<>
						<div className="bg-white rounded-lg p-4">
							<div className="kundli-html" dangerouslySetInnerHTML={{ __html: kundliHtml }} />
						</div>
						<div className="text-center mt-4">
							<button
								onClick={handleGenerate}
								disabled={loading || !effectiveProfileId}
								className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-lg transition-all duration-300"
							>
								Regenerate Kundli
							</button>
							<button
								onClick={handleDownload}
								className="ml-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-lg transition-all duration-300"
							>
								Download PDF
							</button>
						</div>
					</>
				)}

				{/* No Data Message */}
				{!loading && !error && generated && !kundliHtml && (
					<div className="text-center">
						<div className="bg-yellow-500/20 border border-yellow-500 rounded-lg p-4">
							<div className="text-yellow-400 font-semibold">No Kundli Data Available</div>
							<div className="text-gray-300 text-sm mt-2">
								Unable to generate Kundli. Please try again.
							</div>
						</div>
					</div>
				)}
			</div>
		</div>
	);
};

export default KundliPage;