import React from 'react';

interface AstroCardProps {
  image: string;
  name: string;
  experience: string;
}

const AstroCard: React.FC<AstroCardProps> = ({ image, name, experience }) => {
  return (
    <div className="bg-gradient-to-br from-purple-600 via-purple-500 to-yellow-500 bg-opacity-30 glass rounded-2xl p-6 min-w-[280px] sm:w-full md:w-[320px] lg:w-[350px] border border-purple-600 border-opacity-30 hover:border-yellow-400 hover:border-opacity-50 transition-all hover:scale-105 transform">
      <div className="text-center">
        <img
          src={image}
          alt={name}
          className="w-20 h-20 rounded-full mx-auto mb-4 border-4 border-yellow-400"
        />
        <h3 className="text-white font-semibold text-lg sm:text-base md:text-lg mb-2">
          {name}
        </h3>
        <p className="text-yellow-400 text-sm sm:text-xs md:text-sm mb-2">
          {experience}
        </p>
        <button className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-6 py-2 rounded-full font-medium transition-all w-full cursor-pointer">
          Consult Now
        </button>
      </div>
    </div>
  );
};

export default AstroCard;
