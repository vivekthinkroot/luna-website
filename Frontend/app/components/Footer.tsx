import React from "react";

const Footer = () => {
  return (
    <footer className="bg-black bg-opacity-40 text-gray-200 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Footer Top Section */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-4">
          {/* Left Section */}
          <div className="text-white text-center md:text-left mb-4 md:mb-0">
            <h2 className="text-3xl font-bold text-yellow-400">AstroVision</h2>
            <p className="text-sm">
              Discover your cosmic journey with our astrology experts.
            </p>
          </div>

          {/* Social Media Icons */}
          <div className="flex justify-center md:justify-end space-x-6">
            {/* Social Media Icons */}
            <a href="#" className="text-yellow-400 hover:text-white">
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M7 2C4.24 2 2 4.24 2 7v10c0 2.76 2.24 5 5 5h10c2.76 0 5-2.24 5-5V7c0-2.76-2.24-5-5-5H7zm10 2c1.65 0 3 1.35 3 3v10c0 1.65-1.35 3-3 3H7c-1.65 0-3-1.35-3-3V7c0-1.65 1.35-3 3-3h10zm-5 3a5 5 0 100 10 5 5 0 000-10zm0 2a3 3 0 110 6 3 3 0 010-6zm4.5-2a1.5 1.5 0 100 3 1.5 1.5 0 000-3z" />
              </svg>
            </a>
            <a href="#" className="text-yellow-400 hover:text-white">
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M22 12a10 10 0 10-11.62 9.87v-7h-2.3v-2.87h2.3V9.41c0-2.27 1.35-3.53 3.43-3.53.99 0 2.02.18 2.02.18v2.23h-1.14c-1.12 0-1.47.7-1.47 1.42v1.7h2.5l-.4 2.87h-2.1v7A10 10 0 0022 12z" />
              </svg>
            </a>
            <a href="#" className="text-yellow-400 hover:text-white">
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2a10 10 0 00-8.94 14.39L2 22l5.8-1.94A10 10 0 1012 2zm0 18a8 8 0 01-4.23-1.2l-.3-.18-3.44 1.15 1.13-3.35-.2-.34A8 8 0 1112 20zm4.35-5.65c-.24-.12-1.42-.7-1.64-.77-.22-.08-.38-.12-.53.12-.16.24-.61.77-.75.93-.14.16-.28.18-.52.06-.24-.12-1.01-.37-1.92-1.18-.71-.63-1.19-1.4-1.33-1.64-.14-.24-.01-.38.11-.5.12-.12.24-.28.36-.42.12-.14.16-.24.24-.4.08-.16.04-.3-.02-.42-.06-.12-.53-1.28-.73-1.76-.2-.48-.4-.42-.53-.43-.14-.01-.3-.01-.46-.01-.16 0-.42.06-.64.3-.22.24-.85.82-.85 2 0 1.18.86 2.31.98 2.47.12.16 1.7 2.59 4.1 3.63.57.25 1.01.4 1.36.51.57.18 1.09.15 1.5.09.46-.07 1.42-.58 1.63-1.13.2-.55.2-1.03.14-1.13-.06-.1-.22-.16-.46-.28z" />
              </svg>
            </a>
          </div>
        </div>

        {/* Footer Bottom Section */}
        <div className="text-center">
          <p className="text-sm">&copy; 2025 Astrology. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
