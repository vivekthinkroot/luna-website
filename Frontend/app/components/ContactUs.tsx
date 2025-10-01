import React from 'react';

const ContactUs = () => {
  return (
    <section id="contact" className="py-16 px-4 bg-gradient-to-r from-indigo-900 to-purple-900">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">Contact Us</h2>
          <p className="text-gray-300 text-lg">Ready to discover your cosmic destiny? Get in touch with us today.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Form Section */}
          <div className="bg-white bg-opacity-10 glass rounded-2xl p-8 border border-purple-600 border-opacity-30">
            <h3 className="text-2xl font-semibold text-white mb-6">Get Your Reading</h3>
            <form>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Full Name"
                  className="w-full bg-white bg-opacity-10 border border-purple-600 rounded-lg px-4 py-3 text-black placeholder-gray-300 focus:outline-none focus:border-yellow-400 transition-colors"
                />
                <input
                  type="email"
                  placeholder="Email Address"
                  className="w-full bg-white bg-opacity-10 border border-purple-600 rounded-lg px-4 py-3 text-black placeholder-gray-300 focus:outline-none focus:border-yellow-400 transition-colors"
                />
                <textarea
                  rows={4}
                  placeholder="Your Message or Questions"
                  className="w-full bg-white bg-opacity-10 border border-purple-600 rounded-lg px-4 py-3 text-black placeholder-gray-300 resize-none focus:outline-none focus:border-yellow-400 transition-colors"
                />
                <button className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 text-black font-semibold py-3 rounded-lg transition-all transform hover:scale-105 cursor-pointer">
                  Send Messge
                </button>
              </div>
            </form>
          </div>

          {/* Contact Details Section */}
          <div className="text-white">
            <h3 className="text-2xl font-semibold mb-8">Reach Out to Us</h3>
            <div className="space-y-6">
              {/* Phone */}
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-black"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                    />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-yellow-400">Phone</h4>
                  <p className="text-gray-300">+91 98765 43210</p>
                  <p className="text-gray-300">+91 87654 32109</p>
                </div>
              </div>

              {/* Email */}
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-yellow-400">Email</h4>
                  <p className="text-gray-300">info@astrology.com</p>
                  <p className="text-gray-300">consultations@astrology.com</p>
                </div>
              </div>

              {/* Address */}
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-full flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-yellow-400">Address</h4>
                  <p className="text-gray-300">123 Cosmic Center</p>
                  <p className="text-gray-300">Hyderabad, Telangana 500001</p>
                </div>
              </div>

              {/* Working Hours */}
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12,6 12,12 16,14" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-yellow-400">Working Hours</h4>
                  <p className="text-gray-300">Mon - Fri: 9:00 AM - 8:00 PM</p>
                  <p className="text-gray-300">Sat - Sun: 10:00 AM - 6:00 PM</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ContactUs;
