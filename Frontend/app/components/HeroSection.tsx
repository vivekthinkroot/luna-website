import React from 'react';

const HeroSection = () => {
  return (
    <section
      className="h-screen flex items-center justify-center relative"
      style={{
        backgroundImage: `url('/astrology-hero.jpg')`, // Set the background image dynamically
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
      }}
    >
      <div className="text-center text-white px-4 z-10">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 text-gradient-gold">
          Unlock Your Destiny
        </h1>
        <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto text-gray-200">
          Discover the secrets of the stars and planets. Get personalized astrological insights
          from our expert astrologers and transform your life's journey.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-semibold px-8 py-3 rounded-full transition-all transform hover:scale-105 cursor-pointer">
            Get Slot Now
          </button>
          <button className="border-2 border-yellow-400 text-yellow-400 hover:bg-yellow-400 hover:text-black font-semibold px-8 py-3 rounded-full transition-all cursor-pointer">
            Learn More
          </button>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;