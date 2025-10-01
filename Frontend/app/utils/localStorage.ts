/**
 * Utility functions for managing location data in browser localStorage
 */

export interface BirthplaceData {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
}

/**
 * Get birthplace data from localStorage
 * @returns BirthplaceData object or null if not found
 */
export function getBirthplaceFromLocalStorage(): BirthplaceData | null {
  try {
    const city = localStorage.getItem('birthplace_city');
    const country = localStorage.getItem('birthplace_country');
    const lat = localStorage.getItem('birthplace_lat');
    const lng = localStorage.getItem('birthplace_lng');

    if (!city || !country || !lat || !lng) {
      return null;
    }

    return {
      city,
      country,
      latitude: parseFloat(lat),
      longitude: parseFloat(lng),
    };
  } catch (error) {
    console.error('Error reading birthplace from localStorage:', error);
    return null;
  }
}

/**
 * Save birthplace data to localStorage
 * @param data BirthplaceData to store
 */
export function saveBirthplaceToLocalStorage(data: BirthplaceData): void {
  try {
    localStorage.setItem('birthplace_city', data.city);
    localStorage.setItem('birthplace_country', data.country);
    localStorage.setItem('birthplace_lat', data.latitude.toString());
    localStorage.setItem('birthplace_lng', data.longitude.toString());
  } catch (error) {
    console.error('Error saving birthplace to localStorage:', error);
  }
}

/**
 * Clear birthplace data from localStorage
 */
export function clearBirthplaceFromLocalStorage(): void {
  try {
    localStorage.removeItem('birthplace_city');
    localStorage.removeItem('birthplace_country');
    localStorage.removeItem('birthplace_lat');
    localStorage.removeItem('birthplace_lng');
  } catch (error) {
    console.error('Error clearing birthplace from localStorage:', error);
  }
}

/**
 * Get formatted birthplace string (City, Country)
 * @returns Formatted string or null if not found
 */
export function getFormattedBirthplace(): string | null {
  const data = getBirthplaceFromLocalStorage();
  if (!data) return null;
  return `${data.city}, ${data.country}`;
}

/**
 * Get coordinates as a tuple [latitude, longitude]
 * @returns Coordinates array or null if not found
 */
export function getBirthplaceCoordinates(): [number, number] | null {
  const data = getBirthplaceFromLocalStorage();
  if (!data) return null;
  return [data.latitude, data.longitude];
}

