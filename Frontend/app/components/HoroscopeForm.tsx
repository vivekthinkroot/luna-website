import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import PhoneInput from "react-phone-number-input";
import "react-phone-number-input/style.css"; // Import the required styles
import { createProfile, getLocations, searchCities } from "../api";

const HoroscopeForm: React.FC = () => {
  const navigate = useNavigate();
  // Custom styles for PhoneInput dropdown
  const phoneInputCustomStyles = `
    .PhoneInputCountrySelect {
      background-color: #230735 !important;
      color: #fff !important;
    }
    .PhoneInputCountrySelect option {
      background-color: #230735 !important;
      color: #fff !important;
    }
  `;
  const [form, setForm] = useState({
    fullName: "",
    gender: "",
    dob: "",
    pob: "",
    pobId: "",
    tob: "",
    phone: "",
    mobile: "",
    email: "",
    tobPeriod: "AM" // AM/PM period
  });
  // Location state
  const [locations, setLocations] = useState<Array<any>>([]);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState("");
  const [locationSearch, setLocationSearch] = useState("");
  const [locationDisplay, setLocationDisplay] = useState("");
  const [selectedCity, setSelectedCity] = useState<any>(null); // Store selected city object

  // Search cities when user types
  useEffect(() => {
    if (locationSearch.trim().length >= 2) {
      setLocationLoading(true);
      searchCities(locationSearch)
        .then((cities) => {
          setLocations(cities);
          setLocationError("");
        })
        .catch(() => {
          setLocationError("Failed to search cities");
        })
        .finally(() => setLocationLoading(false));
    } else {
      setLocations([]);
    }
  }, [locationSearch]);

  const [errors, setErrors] = useState({
    fullName: "",
    gender: "",
    dob: "",
    pob: "",
    tob: "",
    phone: "",
    mobile: "",
    email: "",
  });
    const [apiStatus, setApiStatus] = useState<{ success?: string; error?: string }>({});
    const [loading, setLoading] = useState(false);
    const [isMounted, setIsMounted] = useState(false);

  // Fix hydration mismatch by only rendering animations after mount
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
    // Clear the error for this field when user starts typing
    if (errors[name as keyof typeof errors]) {
      setErrors({ ...errors, [name]: "" });
    }
  };

  // Handle location select
  const handleLocationSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedId = e.target.value;
    setForm({ ...form, pobId: selectedId });
    // Clear error
    if (errors.pob) {
      setErrors({ ...errors, pob: "" });
    }
  };

  const handlePhoneChange = (value?: string) => {
    setForm({ ...form, mobile: value || "" });
    
    // Clear mobile error when user starts typing
    if (errors.mobile) {
      setErrors({ ...errors, mobile: "" });
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    let newErrors = {
      fullName: "",
      gender: "",
      dob: "",
      pob: "",
      tob: "",
      phone: "",
      mobile: "",
      email: "",
    };

    // Validation
    if (!form.fullName) newErrors.fullName = "Full Name is required.";
    if (!form.gender) newErrors.gender = "Gender is required.";
    if (!form.dob) newErrors.dob = "Date of Birth is required.";
    if (!form.pobId || !selectedCity) newErrors.pob = "Please select a city from the dropdown.";
    if (!form.tob) newErrors.tob = "Time of Birth is required.";
    if (!form.mobile) newErrors.mobile = "Mobile number is required.";
    if (!form.email) newErrors.email = "Email is required.";
    else if (!/\S+@\S+\.\S+/.test(form.email)) newErrors.email = "Invalid email format.";

    setErrors(newErrors);
    
    // Debug validation
    console.log("=== FORM VALIDATION ===");
    console.log("Form pobId:", form.pobId);
    console.log("Selected City:", selectedCity);
    console.log("Validation Errors:", newErrors);
    console.log("======================");

    // If no errors, submit the form
    if (Object.values(newErrors).every((error) => error === "")) {
      try {
        // Compose birth_datetime as ISO string from dob and tob
        let birth_datetime = "";
        if (form.dob && form.tob) {
          birth_datetime = `${form.dob}T${form.tob}:00`;
        }
        // Gender must be MALE/FEMALE/OTHER
        let gender = form.gender.toUpperCase() as "MALE" | "FEMALE" | "OTHER";
        if (!["MALE", "FEMALE", "OTHER"].includes(gender)) {
          gender = "OTHER";
        }
        // Use stored selected city (not from locations array which may be cleared)
        let birth_place = "";
        let birth_location_id = null;
        
        if (selectedCity) {
          birth_place = `${selectedCity.city}, ${selectedCity.country}`;
          // Ensure birth_location_id is an integer, not string
          birth_location_id = typeof selectedCity.id === 'number' 
            ? selectedCity.id 
            : parseInt(selectedCity.id, 10);
          
          console.log("Selected City:", selectedCity);
          console.log("Birth Place:", birth_place);
          console.log("Birth Location ID:", birth_location_id, typeof birth_location_id);
        } else {
          console.error("No city selected! selectedCity is null");
        }
        
        // Create profile via API
        const profileData = {
          name: form.fullName,
          gender,
          birth_datetime,
          birth_place,
          birth_location_id,
          mobile_no: form.mobile,
          email: form.email
        };
        
        // Debug: Log the data being sent
        console.log("=== SUBMITTING PROFILE ===");
        console.log("Profile Data:", JSON.stringify(profileData, null, 2));
        console.log("birth_location_id type:", typeof profileData.birth_location_id);
        console.log("mobile_no length:", profileData.mobile_no?.length);
        
        const response = await createProfile(profileData);
        
        // Store form data AND profile_id in localStorage
        const formData = {
          profile_id: response.profile_id,
          fullName: form.fullName,
          gender,
          birth_datetime,
          birth_place,
          birth_location_id,
          mobile_no: form.mobile,
          email: form.email,
          dob: form.dob,
          tob: form.tob,
          tobPeriod: form.tobPeriod,
          timestamp: new Date().toISOString()
        };
        
        // Store in localStorage
        localStorage.setItem('horoscopeFormData', JSON.stringify(formData));
        localStorage.setItem('profile_id', response.profile_id);
        
        // Show success message
        setApiStatus({ success: "Profile created successfully!" });
        
        // Clear form
        setForm({
          fullName: "",
          gender: "",
          dob: "",
          pob: "",
          pobId: "",
          tob: "",
          phone: "",
          mobile: "",
          email: "",
          tobPeriod: "AM",
        });
        
        // Redirect to kundali page after a short delay
        setTimeout(() => {
          navigate('/kundli');
        }, 1500);
      } catch (error: any) {
        console.error("Profile creation error:", error);
        const errorMessage = error?.message || error?.toString() || "Failed to create profile";
        console.error("Error message:", errorMessage);
        setApiStatus({ error: errorMessage });
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  };

  // Zodiac PNGs with Sanskrit names
  const zodiacImages = [
    { src: "Karka.png", name: "Karka (Cancer)" },
    { src: "Kumbha.png", name: "Kumbha (Aquarius)" },
    { src: "Makar.png", name: "Makar (Capricorn)" },
    { src: "Sinh.png", name: "Sinh (Leo)" },
    { src: "Tula1.png", name: "Tula (Libra)" },
    { src: "Vrishabha.png", name: "Vrishabha (Taurus)" },
    { src: "Vrishchika.png", name: "Vrishchika (Scorpio)" },
    { src: "Dhan.png", name: "Dhanus (Sagittarius)" },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Inject custom styles for PhoneInput dropdown */}
      <style>{phoneInputCustomStyles}</style>
      {/* Animated Background */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(135deg, #230735 0%, #11001C 100%)",
        }}
      />

      {/* White Stars Animation - Only render on client to avoid hydration mismatch */}
      {isMounted && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(30)].map((_, i) => (
            <div
              key={i}
              className="absolute animate-pulse"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${3 + Math.random() * 2}s`,
              }}
            >
              <div className="w-1 h-1 bg-white rounded-full shadow-lg shadow-white/30"></div>
            </div>
          ))}
          {/* Larger stars */}
          {[...Array(10)].map((_, i) => (
            <div
              key={`large-${i}`}
              className="absolute animate-pulse"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 4}s`,
                animationDuration: `${4 + Math.random() * 3}s`,
              }}
            >
              <div className="w-2 h-2 bg-white rounded-full shadow-lg shadow-white/40"></div>
            </div>
          ))}
        </div>
      )}

      {/* Main Content Container */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <p className="text-lg text-gray-300 font-light tracking-wide">
              Discover the cosmic wisdom written in the stars
            </p>
            <div className="w-24 h-0.5 bg-gradient-to-r from-white to-gray-300 mx-auto mt-3 rounded-full"></div>
          </div>
          {/* Main Content Grid */}
          <div className="grid lg:grid-cols-2 md:grid-cols-1 gap-8 items-center">
            {/* Left Side - Zodiac Gallery */}
            <div className="space-y-6">
              <div className="text-center lg:text-left">
                <h2 className="text-2xl font-bold text-yellow-400 mb-4">
                  Sacred Zodiac Signs
                </h2>
                <p className="text-gray-300 text-base leading-relaxed">
                  Each zodiac sign carries ancient wisdom and celestial energy
                  that influences your life's journey.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4 gap-3">
                {zodiacImages.map((zodiac, idx) => (
                  <div
                    key={zodiac.src}
                    className="group relative transform hover:scale-105 transition-all duration-300 cursor-pointer"
                    style={{ animationDelay: `${idx * 0.1}s` }}
                  >
                    <div
                      className="relative overflow-hidden rounded-xl backdrop-blur-sm border border-white/20 shadow-xl hover:shadow-white/10"
                      style={{
                        background:
                          "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
                      }}
                    >
                      <div className="aspect-square p-2">
                        <img
                          src={`/${zodiac.src}`}
                          alt={zodiac.name}
                          className="w-full h-full object-contain filter drop-shadow-lg group-hover:drop-shadow-2xl transition-all duration-300"
                        />
                      </div>
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-end p-2">
                        <span className="text-white text-xs font-semibold">
                          {zodiac.name}
                        </span>
                      </div>
                    </div>

                    {/* Glow Effect */}
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/20 to-white/10 opacity-0 group-hover:opacity-100 transition-all duration-300 -z-10 blur-lg"></div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Side - Compact Premium Form */}
            <div className="lg:pl-6">
              <div className="relative max-w-md mx-auto">
                {/* Form Container - Made Smaller */}
                <div
                  className="relative backdrop-blur-xl rounded-2xl border border-white/20 shadow-xl overflow-hidden"
                  style={{
                    background:
                      "linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%)",
                  }}
                >
                  {/* Decorative Elements - Reduced */}
                  <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-white/10 to-transparent rounded-full blur-xl"></div>
                  <div className="absolute bottom-0 left-0 w-16 h-16 bg-gradient-to-tr from-white/10 to-transparent rounded-full blur-lg"></div>

                  <div className="relative z-10 p-6">
                    <div className="text-center mb-6">
                      <h3 className="text-2xl font-bold text-yellow-400 mb-1">
                        In Depth Horoscope
                      </h3>
                      <p className="text-gray-300 text-sm">
                        Enter your birth details for cosmic insights
                      </p>
                    </div>

                    <div className="space-y-4">
                      {/* Full Name */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Full Name</span>
                        </label>
                        <input
                          type="text"
                          name="fullName"
                          value={form.fullName}
                          onChange={handleChange}
                          placeholder="Enter your full name"
                          className="w-full px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent placeholder-gray-400 transition-all duration-300 hover:border-white/50"
                        />
                        {errors.fullName && (
                          <span className="text-red-400 text-xs font-medium">{errors.fullName}</span>
                        )}
                      </div>

                      {/* Gender */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Gender</span>
                        </label>
                        <select
                          name="gender"
                          value={form.gender}
                          onChange={handleChange}
                          className="w-full px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent transition-all duration-300 hover:border-white/50"
                        >
                          <option value="" className="bg-gray-800">Select Gender</option>
                          <option value="Male" className="bg-gray-800">Male</option>
                          <option value="Female" className="bg-gray-800">Female</option>
                          <option value="Other" className="bg-gray-800">Other</option>
                        </select>
                        {errors.gender && (
                          <span className="text-red-400 text-xs font-medium">{errors.gender}</span>
                        )}
                      </div>

                      {/* Date of Birth */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Date of Birth</span>
                        </label>
                        <input
                          type="date"
                          name="dob"
                          value={form.dob}
                          onChange={handleChange}
                          className="w-full px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent transition-all duration-300 hover:border-white/50"
                        />
                        {errors.dob && (
                          <span className="text-red-400 text-xs font-medium">{errors.dob}</span>
                        )}
                      </div>

                      {/* Place of Birth - Autocomplete Dropdown */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Place of Birth</span>
                        </label>
                        <div className="relative">
                          <input
                            type="text"
                            value={locationDisplay || locationSearch}
                            onChange={e => {
                              setLocationSearch(e.target.value);
                              setLocationDisplay("");
                              setForm({ ...form, pobId: "" });
                              setSelectedCity(null); // Clear selected city when typing
                            }}
                            placeholder="City, Country (e.g., Kabul, Afghanistan)"
                            className="w-full px-3 py-2 rounded-lg bg-black/40 text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white placeholder-gray-400"
                          />
                          {/* Dropdown list below input */}
                          {locationSearch.trim() !== "" && !locationDisplay && (
                            <ul className="absolute w-full max-h-48 overflow-y-auto bg-black/80 border border-white/30 rounded-lg mt-1 z-20">
                              {locationLoading && (
                                <li className="px-3 py-2 text-gray-400">Loading...</li>
                              )}
                              {locationError && (
                                <li className="px-3 py-2 text-red-400">{locationError}</li>
                              )}
                              {!locationLoading && !locationError && locations
                                .slice(0, 20)
                                .map((loc) => (
                                  <li
                                    key={loc.id}
                                    className={`px-3 py-2 cursor-pointer hover:bg-yellow-900/40 text-white`}
                                    onClick={() => {
                                      // Store selected city data
                                      const cityDisplay = `${loc.city}, ${loc.country}`;
                                      setForm({ ...form, pobId: loc.id.toString() });
                                      setLocationDisplay(cityDisplay);
                                      setLocationSearch("");
                                      setSelectedCity(loc); // Store complete city object
                                      
                                      // Store latitude and longitude in localStorage
                                      if (loc.lat && loc.lng) {
                                        localStorage.setItem('birthplace_lat', loc.lat.toString());
                                        localStorage.setItem('birthplace_lng', loc.lng.toString());
                                        localStorage.setItem('birthplace_city', loc.city);
                                        localStorage.setItem('birthplace_country', loc.country);
                                      }
                                    }}
                                  >
                                    {loc.city}, {loc.country}
                                  </li>
                                ))}
                              {/* No results */}
                              {!locationLoading && !locationError && locations.length === 0 && (
                                <li className="px-3 py-2 text-gray-400">No results found</li>
                              )}
                            </ul>
                          )}
                        </div>
                        {/* Show selected city below input */}
                        {form.pobId && locationDisplay && (
                          <div className="mt-1 text-xs text-gray-300">Selected: {locationDisplay}</div>
                        )}
                        {errors.pob && (
                          <span className="text-red-400 text-xs font-medium">{errors.pob}</span>
                        )}
                      </div>

                      {/* Time of Birth */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Time of Birth</span>
                        </label>
                        <div className="flex items-center space-x-3">
                          <input
                            type="time"
                            name="tob"
                            value={form.tob}
                            onChange={handleChange}
                            className="flex-1 px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent transition-all duration-300 hover:border-white/50"
                          />
                          <select
                            name="tobPeriod"
                            value={form.tobPeriod}
                            onChange={handleChange}
                            className="px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent transition-all duration-300 hover:border-white/50"
                          >
                            <option value="AM">AM</option>
                            <option value="PM">PM</option>
                          </select>
                        </div>
                        {errors.tob && (
                          <span className="text-red-400 text-xs font-medium">{errors.tob}</span>
                        )}
                      </div>

                      {/* Mobile Number with PhoneInput */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Mobile Number</span>
                        </label>
                        <PhoneInput
                          international
                          defaultCountry="IN"
                          value={form.mobile}
                          onChange={handlePhoneChange}
                          className="w-full px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent placeholder-gray-400 transition-all duration-300 hover:border-white/50"
                        />
                        {errors.mobile && (
                          <span className="text-red-400 text-xs font-medium">{errors.mobile}</span>
                        )}
                      </div>

                      {/* Email */}
                      <div className="space-y-1">
                        <label className="block text-white font-medium text-xs tracking-wide">
                          <span className="text-yellow-400">Email</span>
                        </label>
                        <input
                          type="email"
                          name="email"
                          value={form.email}
                          onChange={handleChange}
                          placeholder="Enter your email"
                          className="w-full px-3 py-2.5 rounded-lg bg-black/40 backdrop-blur-sm text-white text-sm border border-white/30 focus:outline-none focus:ring-1 focus:ring-white focus:border-transparent placeholder-gray-400 transition-all duration-300 hover:border-white/50"
                        />
                        {errors.email && (
                          <span className="text-red-400 text-xs font-medium">{errors.email}</span>
                        )}
                      </div>

                      {/* Submit Button */}
                      <button
                        onClick={handleSubmit}
                        type="button"
                        className="group relative w-full py-3 mt-6 text-white font-bold rounded-lg text-base shadow-xl hover:shadow-white/10 transform hover:scale-[1.02] transition-all duration-300 overflow-hidden"
                        style={{
                          background:
                            "linear-gradient(135deg, #230735 0%, #11001C 100%)",
                        }}
                      >
                        <span className="relative z-10 flex items-center justify-center space-x-2">
                          <span>Get Horoscope</span>
                        </span>
                        {/* Button Shine Effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 group-hover:animate-pulse"></div>
                      </button>
                      {/* API feedback below button */}
                      {apiStatus.success && (
                        <div className="mt-3 text-green-400 text-sm font-semibold text-center">{apiStatus.success}</div>
                      )}
                      {apiStatus.error && (
                        <div className="mt-3 text-red-400 text-sm font-semibold text-center">{apiStatus.error}</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-12"></div>
        </div>
      </div>
    </div>
  );
};

export default HoroscopeForm;