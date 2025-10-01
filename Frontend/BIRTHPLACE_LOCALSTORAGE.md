# Birthplace Data in localStorage

## Overview

When a user selects their place of birth in the horoscope form, the following data is automatically stored in the browser's localStorage:

- **City name** (city_ascii format)
- **Country name**
- **Latitude**
- **Longitude**

## Data Format

The data is stored as individual localStorage items:

```javascript
localStorage.getItem('birthplace_city')      // e.g., "Kabul"
localStorage.getItem('birthplace_country')   // e.g., "Afghanistan"
localStorage.getItem('birthplace_lat')       // e.g., "34.5333"
localStorage.getItem('birthplace_lng')       // e.g., "69.1667"
```

## Using the Utility Functions

We've created utility functions in `app/utils/localStorage.ts` to help you work with this data:

### Import the utilities

```typescript
import {
  getBirthplaceFromLocalStorage,
  saveBirthplaceToLocalStorage,
  clearBirthplaceFromLocalStorage,
  getFormattedBirthplace,
  getBirthplaceCoordinates
} from './utils/localStorage';
```

### Get complete birthplace data

```typescript
const birthplace = getBirthplaceFromLocalStorage();

if (birthplace) {
  console.log(birthplace.city);        // "Kabul"
  console.log(birthplace.country);     // "Afghanistan"
  console.log(birthplace.latitude);    // 34.5333
  console.log(birthplace.longitude);   // 69.1667
}
```

### Get formatted birthplace string

```typescript
const formattedLocation = getFormattedBirthplace();
console.log(formattedLocation); // "Kabul, Afghanistan"
```

### Get coordinates only

```typescript
const coords = getBirthplaceCoordinates();
if (coords) {
  const [lat, lng] = coords;
  console.log(`Latitude: ${lat}, Longitude: ${lng}`);
}
```

### Save birthplace data manually

```typescript
saveBirthplaceToLocalStorage({
  city: "Mumbai",
  country: "India",
  latitude: 19.076,
  longitude: 72.8777
});
```

### Clear birthplace data

```typescript
clearBirthplaceFromLocalStorage();
```

## Example Usage in a Component

```typescript
import React, { useEffect, useState } from 'react';
import { getBirthplaceFromLocalStorage } from '../utils/localStorage';

const MyComponent: React.FC = () => {
  const [birthplace, setBirthplace] = useState<string>('');

  useEffect(() => {
    const data = getBirthplaceFromLocalStorage();
    if (data) {
      setBirthplace(`${data.city}, ${data.country}`);
      console.log(`Coordinates: ${data.latitude}, ${data.longitude}`);
    }
  }, []);

  return (
    <div>
      <p>Your birthplace: {birthplace || 'Not selected'}</p>
    </div>
  );
};
```

## Using with Maps

If you're integrating with a mapping library like Leaflet or Google Maps:

```typescript
import { getBirthplaceCoordinates } from './utils/localStorage';

const coords = getBirthplaceCoordinates();
if (coords) {
  const [lat, lng] = coords;
  
  // Example with Leaflet
  const map = L.map('map').setView([lat, lng], 13);
  L.marker([lat, lng]).addTo(map);
  
  // Example with Google Maps
  const location = { lat, lng };
  const map = new google.maps.Map(document.getElementById('map'), {
    center: location,
    zoom: 13
  });
  new google.maps.Marker({ position: location, map });
}
```

## Notes

- Data persists across browser sessions until cleared
- Data is specific to the current browser/device
- Always check for null values when retrieving data
- The city field uses the city_ascii format (ASCII-only characters)

