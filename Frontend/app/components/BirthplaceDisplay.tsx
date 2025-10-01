/**
 * Example component showing how to retrieve and display birthplace data from localStorage
 * This component can be used anywhere in your app to display the selected birthplace
 */

import React, { useEffect, useState } from 'react';
import { getBirthplaceFromLocalStorage, BirthplaceData } from '../utils/localStorage';

const BirthplaceDisplay: React.FC = () => {
  const [birthplace, setBirthplace] = useState<BirthplaceData | null>(null);

  useEffect(() => {
    // Retrieve birthplace data from localStorage
    const data = getBirthplaceFromLocalStorage();
    setBirthplace(data);

    // Optional: Set up an event listener to update when localStorage changes
    const handleStorageChange = () => {
      const updatedData = getBirthplaceFromLocalStorage();
      setBirthplace(updatedData);
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  if (!birthplace) {
    return (
      <div className="bg-white/5 rounded-lg p-4">
        <p className="text-gray-400 text-sm">No birthplace selected</p>
      </div>
    );
  }

  return (
    <div className="bg-white/5 rounded-lg p-4 space-y-2">
      <h3 className="text-white font-semibold text-lg">Selected Birthplace</h3>
      
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Location:</span>
          <span className="text-white font-medium">
            {birthplace.city}, {birthplace.country}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Latitude:</span>
          <span className="text-white">{birthplace.latitude.toFixed(4)}°</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Longitude:</span>
          <span className="text-white">{birthplace.longitude.toFixed(4)}°</span>
        </div>
      </div>

      {/* Optional: Display coordinates in a more readable format */}
      <div className="mt-3 p-2 bg-black/30 rounded text-xs text-gray-300 font-mono">
        Coordinates: {birthplace.latitude.toFixed(6)}, {birthplace.longitude.toFixed(6)}
      </div>
    </div>
  );
};

export default BirthplaceDisplay;

