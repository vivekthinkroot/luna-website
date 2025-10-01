
// api.ts - API utility for profile creation
const LOCAL_API_URL = "http://localhost:8000";

export async function createProfile(profile: {
  name: string;
  gender: "MALE" | "FEMALE" | "OTHER";
  birth_datetime: string;
  birth_place: string;
  birth_location_id?: number | null;
  mobile_no: string;
  email: string;
}) {
  const API_URL = `${LOCAL_API_URL}/profiles/`;
  
  // Debug: Log the data being sent
  console.log("Creating profile with data:", JSON.stringify(profile, null, 2));
  
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });
  const data = await res.json();
  
  console.log("API Response:", { status: res.status, data });
  
  if (!res.ok) {
    // Handle validation errors (422)
    if (res.status === 422 && data.detail) {
      // Format validation errors nicely
      if (Array.isArray(data.detail)) {
        const errors = data.detail.map((err: any) => 
          `${err.loc?.join(' → ') || 'Field'}: ${err.msg}`
        ).join('; ');
        throw new Error(`Validation Error: ${errors}`);
      }
      throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
    }
    throw new Error(data.detail || data.message || "Failed to create profile");
  }
  return data;
}

// Request OTP for login
export async function requestOtp(mobile: string) {
  const API_URL = `${LOCAL_API_URL}/authentication/request-otp`;
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ mobile }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to request OTP");
  }
  return data;
}

// Verify OTP for login
export async function verifyOtp(mobile: string, otp: string) {
  const API_URL = `${LOCAL_API_URL}/authentication/verify-otp`;
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ mobile, otp }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to verify OTP");
  }
  return data;
}
// Generate kundli for a profile
export async function generateKundli(profile_id: string, user_id: string) {
  const API_URL = `${LOCAL_API_URL}/kundli/generate/${profile_id}?user_id=${user_id}`;
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to generate kundli");
  }
  return data;
}

// Generate kundli directly from localStorage data (no profile required)
export async function generateKundliDirect(data: {
  name: string;
  gender: string;
  birth_datetime: string;
  birth_place: string;
  latitude: number;
  longitude: number;
}) {
  const API_URL = `${LOCAL_API_URL}/kundli/generate-direct`;
  
  console.log("Calling Direct Kundli Generation:", data);
  
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  
  const responseData = await res.json();
  
  if (!res.ok) {
    throw new Error(responseData.detail || "Failed to generate kundli");
  }
  
  return responseData;
}
// Fetch cities for Place of Birth
export async function getLocations() {
  const API_URL = `${LOCAL_API_URL}/profiles/cities`;
  const res = await fetch(API_URL);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to fetch cities");
  }
  return data.cities || [];
}

// Search cities with query
export async function searchCities(query: string) {
  const API_URL = `${LOCAL_API_URL}/profiles/cities/search?search_term=${encodeURIComponent(query)}`;
  const res = await fetch(API_URL);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to search cities");
  }
  return data.cities || [];
}

// Download kundli PDF for a profile
export async function downloadKundliPdf(profile_id: string): Promise<void> {
  const response = await fetch(`http://localhost:8000/kundli/generate-pdf/${profile_id}`, {
    method: 'POST',
    headers: {},
  });
  if (!response.ok) {
    throw new Error('Failed to download PDF');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `kundli_${profile_id}.pdf`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, 100);
}

// Check if user can generate kundli (payment verification)
export async function canGenerateKundli(user_id: string) {
  const API_URL = `${LOCAL_API_URL}/kundli/can-generate/${user_id}`;
  const res = await fetch(API_URL);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to check payment status");
  }
  return data;
}

// Check payment status for a user
export async function checkPaymentStatus(user_id: string) {
  const API_URL = `${LOCAL_API_URL}/payments/status/${user_id}`;
  const res = await fetch(API_URL);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to check payment status");
  }
  return data;
}

// Create payment link
export async function createPaymentLink(user_id: string, sku_id: string) {
  const API_URL = `${LOCAL_API_URL}/payments/create-link`;
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, sku_id }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to create payment link");
  }
  return data;
}

// Get available SKUs
export async function getAvailableSkus() {
  const API_URL = `${LOCAL_API_URL}/payments/skus`;
  const res = await fetch(API_URL);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to fetch SKUs");
  }
  return data.skus || [];
}

// Verify test payment (for development/testing)
export async function verifyTestPayment(user_id: string) {
  const API_URL = `${LOCAL_API_URL}/payments/verify-test-payment/${user_id}`;
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to verify test payment");
  }
  return data;
}

// Check payment success status
export async function checkPaymentSuccess(user_id: string) {
  const API_URL = `${LOCAL_API_URL}/payments/check-success/${user_id}`;
  const res = await fetch(API_URL);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Failed to check payment success");
  }
  return data;
}

export async function verifyPayment(payment_id: string): Promise<{ status: string }> {
  // Call your backend API (FastAPI) instead of Razorpay directly
  const res = await fetch(`http://localhost:8000/kundli/payments/${payment_id}`);

  if (!res.ok) {
    throw new Error(`Verify payment failed: ${res.status}`);
  }

  const data = await res.json();
  return { status: data.payment_status }; // "captured" | "failed" | ...
}