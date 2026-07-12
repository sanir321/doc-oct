export const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiService = {
  async uploadFile(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json()).detail);
    return res.json();
  },

  async askQuestion(sessionId) {
    const res = await fetch(`${BASE}/api/ask/${sessionId}`, { method: 'POST' });
    if (!res.ok) throw new Error((await res.json()).detail);
    return res.json();
  },

  async submitAnswer(sessionId, question, answer) {
    const res = await fetch(`${BASE}/api/answer/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, answer }),
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    return res.json();
  },

  getDownloadUrl(sessionId, fmt="html") {
    return `${BASE}/api/download/${sessionId}/${fmt}`;
  }
};
