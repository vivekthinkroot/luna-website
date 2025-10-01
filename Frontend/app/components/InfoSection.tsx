import React from "react";

interface Stat {
  value: string;
  label: string;
}

interface InfoSectionProps {
  image: string;
  heading: string;
  text: string | string[]; // can be multiple paragraphs
  stats?: Stat[]; // optional stats like clients, years experience
  buttonText?: string;
  reverse?: boolean; // if true, image goes right, text left
}

const InfoSection: React.FC<InfoSectionProps> = ({
  image,
  heading,
  text,
  stats,
  buttonText,
  reverse = false,
}) => {
  const paragraphs = Array.isArray(text) ? text : [text];

  return (
    <section
      className={`py-16 px-4 ${
        reverse ? "bg-black bg-opacity-20" : "bg-gradient-to-r from-purple-700 to-blue-800"
      }`}
    >
      <div className="max-w-7xl mx-auto">
        <div
          className={`grid grid-cols-1 md:grid-cols-2 gap-12 items-center ${
            reverse ? "md:grid-cols-2-reverse" : ""
          }`}
        >
          {/* Image Section */}
          <div className={`relative ${reverse ? "order-1" : "order-2"}`}>
            <img
              src={image}
              alt={heading}
              className="w-full h-auto rounded-2xl shadow-2xl"
            />
            <div className="absolute -top-6 -right-6 w-24 h-24 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-black" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
          </div>

          {/* Text Section */}
          <div className={`text-white ${reverse ? "order-2" : "order-1"}`}>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-yellow-400">
              {heading}
            </h2>

            {paragraphs.map((p, idx) => (
              <p key={idx} className="text-gray-300 text-lg mb-6 leading-relaxed">
                {p}
              </p>
            ))}

            {/* Stats */}
            {stats && stats.length > 0 && (
              <div className="flex items-center space-x-6 mb-8">
                {stats.map((stat, idx) => (
                  <div key={idx} className="text-center">
                    <div className="text-3xl font-bold text-yellow-400">{stat.value}</div>
                    <div className="text-sm text-gray-400">{stat.label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Button */}
            {buttonText && (
              <button className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-8 py-3 rounded-full font-semibold transition-all transform hover:scale-105 cursor-pointer">
                {buttonText}
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default InfoSection;
