const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchDashboard() {
  const res = await fetch(`${API_BASE_URL}/api/dashboard`);
  if (!res.ok) {
    throw new Error(`Dashboard fetch failed: ${res.statusText}`);
  }
  return await res.json();
}

export async function sendChatMessage(message, history = []) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      history: history.map(h => ({
        role: h.role,
        content: h.content,
      })),
    }),
  });

  if (!res.ok) {
    let errorDetail = 'Failed to get response from server';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // Use fallback
    }
    throw new Error(errorDetail);
  }

  return await res.json();
}
