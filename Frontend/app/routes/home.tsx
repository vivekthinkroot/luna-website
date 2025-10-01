// app/routes/index.tsx
import React from 'react';
import HoroscopeForm from '~/components/HoroscopeForm';
import Navbar from '../components/Navbar';
import HeroSection from '../components/HeroSection';
import AstroCard from '../components/AstroCard';
import InfoSection from '../components/InfoSection';
import ContactUs from '../components/ContactUs';
import Footer from '../components/Footer'; // Import the Footer Component

const astrologers = [
  {
    id: 1,
    image: 'https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=200&h=200&fit=crop&crop=face',
    name: 'Dr. Maya Sharma',
    experience: '15 Years of Experience',
  },
  {
    id: 2,
    image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face',
    name: 'Pandit Rajesh Kumar',
    experience: '22 Years of Experience',
  },
  {
    id: 3,
    image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&crop=face',
    name: 'Smt. Priya Devi',
    experience: '18 Years of Experience',
  },
  {
    id: 4,
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face',
    name: 'Guru Arjun Singh',
    experience: '25 Years of Experience',
  },
  {
    id: 5,
    image: 'https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=200&h=200&fit=crop&crop=face',
    name: 'Dr. Kavitha Rao',
    experience: '12 Years of Experience',
  },
];

const Home = () => {
  return (
    <div>
      {/* Navbar */}
      <Navbar />
       <HoroscopeForm />
      {/* Hero Section */}
      <HeroSection />

      {/* Astrologers Section */}
      <section className="py-16 px-4 bg-gradient-to-r from-purple-700 to-yellow-600">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-white mb-4">Meet Our Expert Astrologers</h2>
            <p className="text-gray-300 text-lg">Consult with experienced professionals who can guide your path</p>
          </div>

          {/* Scrollable AstroCard Container */}
          <div className="overflow-x-auto pb-4 bg-transparent scroll-container">
            <div className="flex space-x-6 w-max">
              {astrologers.map(astro => (
                <AstroCard
                  key={astro.id}
                  image={astro.image}
                  name={astro.name}
                  experience={astro.experience}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Left Aligned Section */}
      <InfoSection
        image="/img1.jpg"
        heading="Ancient Wisdom, Modern Insights"
        text={[
          "Our astrology practice combines thousands of years of ancient wisdom with modern psychological insights.",
          "We believe that understanding the cosmic influences can help you make better decisions, improve relationships, and find your true purpose in life."
        ]}
        stats={[
          { value: "1000+", label: "Happy Clients" },
          { value: "25+", label: "Years Experience" },
          { value: "5★", label: "Average Rating" }
        ]}
      />

      {/* Right Aligned Section */}
      <InfoSection
        image="/img2.jpg"
        heading="Comprehensive Astrological Services"
        text={[
          "Understand relationship dynamics and compatibility through synastry and composite chart analysis.",
          "Forecast future trends and important life events using advanced astrological techniques."
        ]}
        buttonText="Explore All Services"
        reverse={true}
      />

      {/* Contact Us Section */}
      <ContactUs />

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default Home;
