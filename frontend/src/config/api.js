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
    return req(`${BASE}/api/ask-paper/${sessionId}`, { method: 'POST' });
  },

  submitAnswer(sessionId, question, answer) {
    return req(`${BASE}/api/answer-paper/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, answer }),
    });
  },

  getDownloadUrl(sessionId, fmt="html", paperFormat="procomm") {
    return `${BASE}/api/download-paper/${sessionId}/${fmt}?format=${paperFormat}`;
  },

  savePaper(sessionId, paperJson) {
    return req(`${BASE}/api/save-paper/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paper_json: paperJson }),
    });
  },

  editPaper(sessionId, instruction) {
    return req(`${BASE}/api/edit-paper/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction }),
    });
  },

  setMode(sessionId, mode) {
    return req(`${BASE}/api/set-mode/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
  },

  askResumeQuestion(sessionId) {
    return req(`${BASE}/api/ask-resume/${sessionId}`, { method: 'POST' });
  },

  submitResumeAnswer(sessionId, question, answer) {
    return req(`${BASE}/api/answer-resume/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, answer }),
    });
  },

  getResumeDownloadUrl(sessionId, fmt) {
    return `${BASE}/api/download-resume/${sessionId}/${fmt}`;
  },

  saveResume(sessionId, resumeText) {
    return req(`${BASE}/api/save-resume/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_text: resumeText }),
    });
  },

  editResume(sessionId, instruction) {
    return req(`${BASE}/api/edit-resume/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction }),
    });
  },

};
