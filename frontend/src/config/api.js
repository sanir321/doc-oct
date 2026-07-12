export const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ponytail: one fetch helper instead of repeating the ok-check everywhere
async function req(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error((await res.json()).detail);
  return res.json();
}

export const apiService = {
  uploadFile(file) {
    const form = new FormData();
    form.append('file', file);
    return req(`${BASE}/api/upload`, { method: 'POST', body: form });
  },

  askQuestion(sessionId) {
    return req(`${BASE}/api/ask/${sessionId}`, { method: 'POST' });
  },

  submitAnswer(sessionId, question, answer) {
    return req(`${BASE}/api/answer/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, answer }),
    });
  },

  getDownloadUrl(sessionId, fmt="html") {
    return `${BASE}/api/download/${sessionId}/${fmt}`;
  },

  savePaper(sessionId, paperJson) {
    return req(`${BASE}/api/save/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paper_json: paperJson }),
    });
  },

  editPaper(sessionId, instruction) {
    return req(`${BASE}/api/edit/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction }),
    });
  },

};
