import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer"; // Your Navbar and Footer

const About = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />

      <main className="flex-1 bg-gray-100 py-16 px-4">
        <div className="max-w-3xl mx-auto flex flex-col items-center gap-8">
          
          {/* Animated Image */}
          <div>
            <img
              src='/think_img.jpg'
              alt="Thinking Person"
              className="w-full max-w-sm mx-auto animate-bounce-slow rounded-lg shadow-lg"
            />
          </div>

          {/* Text Section */}
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-800 mb-6">
              About AstroVision
            </h1>
            <p className="text-lg text-gray-700 mb-4">
              At <span className="font-semibold text-yellow-500">AstroVision</span>, 
              we believe that the stars hold the key to understanding your life's journey. Our expert astrologers provide personalized insights to help you navigate challenges, uncover opportunities, and align with your true potential.
            </p>
            <p className="text-lg text-gray-700 mb-4">
              Whether you are seeking guidance in love, career, health, or personal growth, our astrology consultations are tailored to bring clarity, wisdom, and actionable advice into your life.
            </p>
            <p className="text-lg text-gray-700">
              Explore the cosmic patterns that shape your destiny and take the first step towards a brighter, more enlightened future.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default About;
