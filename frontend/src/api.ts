export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchWithGroqKey<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const apiKey = localStorage.getItem('groq_api_key');

  if (!apiKey) {
    throw new Error('API_KEY_MISSING');
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Groq-Api-Key': apiKey,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = '';
    try {
      const err = await response.json();
      detail = err?.detail || JSON.stringify(err);
    } catch {
      detail = await response.text();
    }

    if (detail === 'API_KEY_MISSING') {
      throw new Error('API_KEY_MISSING');
    }

    throw new Error(`API request failed: ${response.status} ${response.statusText}${detail ? ` - ${detail}` : ''}`);
  }

  return response.json() as Promise<T>;
}
