import React, { useState } from "react";
import Navbar from "../components/Navbar"; // Import Navbar component
import Footer from "../components/Footer"; // Import Footer component
import { useNavigate } from "react-router"; // Import useNavigate for navigation

const Pricing = () => {
  // State to track the selected pricing option (monthly or yearly)
  const [isYearly, setIsYearly] = useState(false);
  const navigate = useNavigate(); // Initialize useNavigate

  // Toggle function to switch between Monthly and Yearly
  const togglePricing = () => setIsYearly(!isYearly);

  // Pricing plans with both monthly and yearly options
  const plans = [
    {
      name: "Basic Plan",
      monthlyPrice: 29.99,
      yearlyPrice: 299.99,
      features: [
        "1 Personal Birth Chart Reading",
        "1 Relationship Compatibility Analysis",
        "Email Consultation",
        "Weekly Astrology Updates",
      ],
    },
    {
      name: "Plus Plan",
      monthlyPrice: 59.99,
      yearlyPrice: 599.99,
      features: [
        "Everything in Basic Plan",
        "2 Personal Birth Chart Readings",
        "1 Career Guidance Analysis",
        "Monthly Relationship Compatibility Analysis",
        "Priority Email Consultation",
      ],
    },
    {
      name: "Premium Plan",
      monthlyPrice: 99.99,
      yearlyPrice: 999.99,
      features: [
        "Everything in Plus Plan",
        "Unlimited Personal Birth Chart Readings",
        "Weekly Relationship Compatibility Analysis",
        "Full Yearly Astrology Forecast",
        "VIP 1-on-1 Phone Consultation",
      ],
    },
  ];

  // Function to handle clicking on the "Book Slot" button
 const handleBookSlot = (amount: number) => {
  navigate('/', { state: { amount } });
};

  return (
    <div>
      {/* Navbar component */}
      <Navbar />

      {/* Pricing Section */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-800 mb-6">
            Choose Your Plan
          </h2>
          <p className="text-lg text-gray-600 mb-12">
            Select the perfect plan to unlock the secrets of the stars and get
            personalized astrological guidance.
          </p>

          {/* Pricing Toggle (Monthly / Yearly) */}
          <div className="mb-8">
            <button
              onClick={togglePricing}
              className="text-white bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 px-6 py-2 rounded-full cursor-pointer"
            >
              {isYearly ? "Switch to Monthly" : "Switch to Yearly"}
            </button>
          </div>

          {/* Pricing Plans */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <div
                key={index}
                className="bg-white shadow-xl rounded-xl p-8 border border-gray-300 hover:border-yellow-400 transition-all transform hover:scale-105 flex flex-col"
              >
                <h3 className="text-3xl font-semibold text-yellow-400 mb-4">
                  {plan.name}
                </h3>
                <p className="text-4xl font-bold text-gray-800 mb-4">
                  ₹
                  {isYearly
                    ? plan.yearlyPrice.toFixed(2)
                    : plan.monthlyPrice.toFixed(2)}{" "}
                  <span className="text-sm text-gray-500">
                    {isYearly ? "/ year" : "/ month"}
                  </span>
                </p>

                <ul className="text-gray-600 mb-6 flex-grow">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="mb-2">
                      <svg
                        className="inline-block h-5 w-5 text-yellow-400 mr-2"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          d="M9 11l3 3L22 4"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>

                {/* Book Slot Button */}
                <div className="mt-auto">
                  <button
                    onClick={() =>
                      handleBookSlot(
                        isYearly ? plan.yearlyPrice : plan.monthlyPrice
                      )
                    }
                    className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 text-black font-semibold py-3 rounded-lg transition-all hover:scale-105 cursor-pointer"
                  >
                    Book Slot
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer component */}
      <Footer />
    </div>
  );
};

export default Pricing;
