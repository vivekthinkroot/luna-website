import React, { useState } from "react";
import { useNavigate } from "react-router";
const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  // Toggle the mobile menu
  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };
  const navigate = useNavigate(); 
  const handleBookSlot = () => {
    return navigate('/login'); 
  }

  return (
  <nav className="sticky top-0 z-50 border-b border-purple-800 border-opacity-30" style={{ background: '#230735' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <img
              src="/logo.png"
              alt="AstroVision Logo"
              className="h-23 w-23 object-contain"
            />
          </div>

          {/* Centered Desktop Navigation Links */}
          <div className="hidden md:flex flex-1 justify-center items-center space-x-6">
            <a
              href="/"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              Home
            </a>
            <a
              href="/about"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              About Us
            </a>
            <a
              href="/pricing"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              Pricing
            </a>
            <a
              href="#contact"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              Contact Us
            </a>
          </div>

          {/* Login Button (Right Aligned) */}
          <div className="hidden md:flex">
            <button className="px-4 py-2 bg-gradient-to-r from-yellow-500 to-yellow-600 text-black font-semibold rounded-md transition-all hover:scale-105 cursor-pointer" onClick={handleBookSlot}>
              Login
            </button>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={toggleMenu}
              className="text-white focus:outline-none"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-black bg-opacity-50 absolute w-full left-0 top-16 py-4">
          <div className="flex flex-col items-center space-y-4">
            <a
              href="/"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              Home
            </a>
            <a
              href="/about"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              About Us
            </a>
            <a
              href="/pricing"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              Pricing
            </a>
            <a
              href="#contact"
              className="text-white hover:text-yellow-400 transition-colors"
            >
              Contact Us
            </a>

            {/* Book Slot Button (Mobile Menu) */}
            <button className="mt-2 px-4 py-2 bg-gradient-to-r from-yellow-500 to-yellow-600 text-black font-semibold rounded-md transition-all hover:scale-105 cursor-pointer" onClick={handleBookSlot}>
              Login
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
