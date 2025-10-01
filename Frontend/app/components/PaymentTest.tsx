import React, { useEffect, useState } from "react";
import { verifyTestPayment } from "../api";

// Extend window type for Razorpay callback
declare global {
  interface Window {
    handleRazorpayPayment?: (response: any) => void;
  }
}

const PaymentTest: React.FC = () => {
  const [paymentStatus, setPaymentStatus] = useState<string>("idle");
  const [paymentResponse, setPaymentResponse] = useState<any>(null);
  const [user_id] = useState<string>("test-user-123"); // Test user ID

  useEffect(() => {
    // Remove previous script if any
    const prevScript = document.getElementById("razorpay-script");
    if (prevScript) prevScript.remove();

    // Create the Razorpay payment button script
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/payment-button.js";
    script.setAttribute("data-payment_button_id", "pl_RMzdCG79e62qAb"); // Your test button ID
    script.setAttribute("data-callback", "handleRazorpayPayment");
    script.async = true;
    script.id = "razorpay-script";

    // Find the payment form container
    const form = document.getElementById("razorpay-form");
    if (form) {
      form.appendChild(script);
    }

    // Set up global callback function
    window.handleRazorpayPayment = async (response: any) => {
      console.log("Payment response:", response);
      setPaymentResponse(response);
      
      if (response?.razorpay_payment_id) {
        setPaymentStatus("success");
        console.log("Payment successful:", response.razorpay_payment_id);
        
        // Verify payment with backend
        try {
          await verifyTestPayment(user_id);
          console.log("Payment verified with backend");
        } catch (error) {
          console.error("Failed to verify payment with backend:", error);
        }
      } else {
        setPaymentStatus("failed");
        console.log("Payment failed");
      }
    };

    // Cleanup on unmount
    return () => {
      if (form && form.contains(script)) {
        form.removeChild(script);
      }
      delete window.handleRazorpayPayment;
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#230735] to-[#11001C] p-4">
      <div className="max-w-2xl mx-auto bg-white/10 rounded-xl shadow-xl p-6 mt-8">
        <h2 className="text-2xl font-bold text-yellow-400 mb-4 text-center">
          Razorpay Payment Test
        </h2>
        
        <div className="bg-white/5 rounded-lg p-6 mb-4">
          <h3 className="text-xl text-white mb-4">Test Payment with Button ID: pl_RMzdCG79e62qAb</h3>
          <p className="text-gray-300 mb-4">
            Click the button below to test the payment flow:
          </p>
          
          <form id="razorpay-form" className="mb-4">
            {/* Razorpay payment button will be loaded here */}
          </form>
          
          <div className="text-gray-300 text-sm mt-2">
            Secure payment powered by Razorpay
          </div>
        </div>

        {/* Payment Status */}
        {paymentStatus !== "idle" && (
          <div className={`rounded-lg p-4 mb-4 ${
            paymentStatus === "success" 
              ? "bg-green-500/20 border border-green-500" 
              : "bg-red-500/20 border border-red-500"
          }`}>
            <h4 className={`font-semibold ${
              paymentStatus === "success" ? "text-green-400" : "text-red-400"
            }`}>
              Payment {paymentStatus === "success" ? "Successful!" : "Failed"}
            </h4>
            {paymentResponse && (
              <div className="mt-2">
                <p className="text-gray-300 text-sm">
                  Payment ID: {paymentResponse.razorpay_payment_id}
                </p>
                <p className="text-gray-300 text-sm">
                  Order ID: {paymentResponse.razorpay_order_id}
                </p>
                <p className="text-gray-300 text-sm">
                  Signature: {paymentResponse.razorpay_signature}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="bg-blue-500/20 border border-blue-500 rounded-lg p-4">
          <h4 className="text-blue-400 font-semibold mb-2">Test Instructions:</h4>
          <ul className="text-gray-300 text-sm space-y-1">
            <li>• Use test card: 4111 1111 1111 1111</li>
            <li>• Use any future expiry date</li>
            <li>• Use any CVV</li>
            <li>• Use any name</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PaymentTest;
