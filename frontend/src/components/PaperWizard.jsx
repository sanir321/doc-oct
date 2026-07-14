import { useState, useRef, useEffect, useCallback } from 'react';
import { apiService, BASE } from '../config/api';
import LogoMark from './LogoMark';

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

const FORMAT_INFO = [
  { label: 'PDF', desc: 'Extracts text, diagrams & metadata' },
  { label: 'DOCX', desc: 'Reads formatted content & tables' },
  { label: 'Images', desc: 'OCR extracts text from screenshots & scans' },
  { label: 'Code', desc: 'Parses .py, .js, .tsx, .ipynb & more' },
  { label: 'Text', desc: 'TXT, Markdown, CSV, HTML, XML' },
  { label: 'LaTeX', desc: 'Reads .tex with equations & structure' },
];

const steps = ['Upload', 'Analysis', 'Interview', 'Generate'];

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 ml-1">
      {[0, 1, 2].map(i => (
        <span key={i} className="w-1.5 h-1.5 rounded-full animate-bounce bg-primary"
          style={{ animationDelay: `${i * 0.15}s`, animationDuration: '0.8s' }} />
      ))}
    </span>
  );
}

function DocIcon({ color }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color || '#6c6a64'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function Sidebar({ current, history, onSelectDoc, onReset }) {
  let profile = null;
  try { const p = localStorage.getItem('userProfile'); if (p) profile = JSON.parse(p); } catch {}

  return (
    <aside className="hidden md:flex flex-col w-64 shrink-0 min-h-0 h-full">
      <div className="flex-1 rounded-2xl border border-hairline bg-surface-card flex flex-col overflow-y-auto min-h-0"
        style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}>
        {/* Header */}
        <div className="px-4 py-3.5 border-b border-hairline shrink-0 flex items-center gap-2.5 text-ink">
          <LogoMark size={16} />
          <span className="text-sm font-medium">Research Paper AI</span>
        </div>

        {/* Document list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {history.length === 0 && !current && (
            <div className="text-center py-8">
              <p className="text-xs font-mono uppercase mb-1 text-muted">Empty</p>
              <p className="text-xs text-muted-soft">Upload a file to get started</p>
            </div>
          )}

          {history.map((doc, i) => {
            const isActive = current && current.name === doc.name && current.lastModified === doc.lastModified;
            return (
              <button key={`${doc.name}-${i}`}
                onClick={() => onSelectDoc(doc)}
                className="w-full text-left rounded-xl px-3 py-2.5 transition-all active:scale-[0.98]"
                style={{
                  backgroundColor: isActive ? 'var(--canvas)' : 'transparent',
                  border: isActive ? '1px solid var(--hairline)' : '1px solid transparent',
                }}>
                <div className="flex items-start gap-2.5">
                  <span className="mt-0.5 shrink-0"><DocIcon /></span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm truncate font-medium text-ink">{doc.name}</p>
                    {doc.title && (
                      <p className="text-[11px] truncate mt-0.5 text-muted-soft">{doc.title}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono text-muted-soft">
                        {formatSize(doc.size)}
                      </span>
                      <span className="text-[10px] text-muted-soft">
                        {new Date(doc.uploadedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  </div>
                  {isActive && (
                    <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 bg-primary" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Current session details */}
        {current && (
          <div className="px-4 py-3 border-t border-hairline shrink-0">
            <p className="text-[10px] font-mono uppercase mb-1.5 text-muted">Active Session</p>
            <div className="rounded-xl px-3 py-2 bg-canvas">
              <p className="text-xs font-medium truncate text-ink">{current.name}</p>
              <p className="text-[10px] mt-0.5 text-muted-soft">
                {current.sections || 0} sections · {current.qaCount || 0} Q&A
              </p>
            </div>
          </div>
        )}

        {/* New Session button */}
        <div className="p-3 border-t border-hairline shrink-0">
          <button onClick={onReset}
            className="w-full text-xs rounded-full px-3 py-2 text-center transition-all hover:opacity-80 active:scale-[0.95] flex items-center justify-center gap-1.5 bg-canvas text-muted">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#6c6a64" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Session
          </button>
        </div>

        {/* Profile at bottom */}
        {profile && (
          <div className="px-4 py-3 border-t border-hairline shrink-0 bg-canvas">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0"
                style={{ backgroundColor: '#cc785c', color: '#fff' }}>
                {profile.name.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate text-ink">{profile.name}</p>
                <p className="text-[10px] truncate text-muted">{profile.course} · {profile.year}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

export default function PaperWizard({ onNewSession }) {
  const [step, setStep] = useState(0);
  const [prevStep, setPrevStep] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [question, setQuestion] = useState(null);
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [followUp, setFollowUp] = useState(null);
  const [messages, setMessages] = useState([]);
  const [aiTyping, setAiTyping] = useState(false);
  const [ready, setReady] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [livePaper, setLivePaper] = useState('');
  const [result, setResult] = useState(null);
  const streamDone = useRef(false);
  const evtSourceRef = useRef(null);
  const evtSourceResumeRef = useRef(null);
  const [customAnswer, setCustomAnswer] = useState('');
  const [customFollowUp, setCustomFollowUp] = useState('');
  const chatEnd = useRef(null);
  const fileRef = useRef(null);

  const [editMode, setEditMode] = useState(false);
  const [editable, setEditable] = useState(null);
  const [saving, setSaving] = useState(false);
  const [aiEditInput, setAiEditInput] = useState('');
  const [aiEditing, setAiEditing] = useState(false);
  const [previewKey, setPreviewKey] = useState(0);
  const [editError, setEditError] = useState('');
  const [uploadHistory, setUploadHistory] = useState([]);

  // Resume mode state
  const [mode, setMode] = useState(''); // '' | 'ieee' | 'resume'
  const [resumeQuestion, setResumeQuestion] = useState(null);
  const [resumeMessages, setResumeMessages] = useState([]);
  const [resumeReady, setResumeReady] = useState(false);
  const [resumeGenerating, setResumeGenerating] = useState(false);
  const [liveResume, setLiveResume] = useState('');
  const [resumeResult, setResumeResult] = useState(null);
  const [resumeEditMode, setResumeEditMode] = useState(false);
  const [resumeEditable, setResumeEditable] = useState('');
  const [resumeSaving, setResumeSaving] = useState(false);
  const [resumeAiEditInput, setResumeAiEditInput] = useState('');
  const [resumeAiEditing, setResumeAiEditing] = useState(false);
  const [resumePreviewKey, setResumePreviewKey] = useState(0);
  const [resumeCustomAnswer, setResumeCustomAnswer] = useState('');

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, aiTyping]);
  useEffect(() => {
    return () => {
      evtSourceRef.current?.close();
      evtSourceResumeRef.current?.close();
    };
  }, []);

  const goStep = useCallback((s) => {
    setPrevStep(step);
    setStep(s);
  }, [step]);

  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);
  const handleDrop = (e) => { e.preventDefault(); setDragOver(false); setFile(e.dataTransfer.files[0]); };
  const handleFileSelect = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) { setError('Select a file'); return; }
    setLoading(true); setError('');
    try {
      const data = await apiService.uploadFile(file);
      setSessionId(data.session_id);
      const docEntry = {
        name: file.name,
        size: file.size,
        lastModified: file.lastModified,
        sessionId: data.session_id,
        title: '',
        uploadedAt: Date.now(),
        sections: 0,
        qaCount: 0,
      };
      setUploadHistory(prev => {
        const filtered = prev.filter(d => d.name !== file.name || d.lastModified !== file.lastModified);
        return [docEntry, ...filtered].slice(0, 50);
      });
      goStep(1);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const answerQuestion = async (answer) => {
    if (!question || !answer.trim()) return;
    setLoading(true);
    setQuestion(null);
    const q = question.question;
    setMessages(prev => [...prev, { role: 'user', text: answer }]);
    setAiTyping(true);
    try {
      const data = await apiService.submitAnswer(sessionId, q, answer);
      setCustomAnswer('');
      setShowFollowUp(false);
      await new Promise(r => setTimeout(r, 700));
      if (data.needs_clarification) {
        setFollowUp(data);
        setQuestion(data);
        setShowFollowUp(true);
        setAiTyping(false);
        setMessages(prev => [...prev, { role: 'ai', text: `Could you clarify? ${data.follow_up || ''}` }]);
      } else if (data.ready) {
        setReady(true); setAiTyping(false);
        setMessages(prev => [...prev, { role: 'ai', text: 'Great — I have enough information to generate the paper!' }]);
        goStep(3);
      } else {
        setQuestion(data); setAiTyping(false);
        setMessages(prev => [...prev, { role: 'ai', text: data.question || '' }]);
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleFollowUpAnswer = async (answer) => {
    if (!answer.trim()) return;
    setLoading(true);
    setShowFollowUp(false);
    setMessages(prev => [...prev, { role: 'user', text: answer }]);
    setAiTyping(true);
    try {
      const data = await apiService.submitAnswer(sessionId, followUp.follow_up, answer);
      setCustomFollowUp('');
      await new Promise(r => setTimeout(r, 700));
      if (data.ready) {
        setReady(true); setAiTyping(false);
        setMessages(prev => [...prev, { role: 'ai', text: 'Great — I have enough information!' }]);
        goStep(3);
      } else {
        setQuestion(data); setAiTyping(false);
        setMessages(prev => [...prev, { role: 'ai', text: data.question || '' }]);
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const skipInterview = async () => {
    setLoading(true);
    try {
      const data = await apiService.askQuestion(sessionId);
      if (data.ready) {
        setReady(true); setQuestion(null);
        setMessages(prev => [...prev, { role: 'ai', text: 'Skipping — enough information to generate the paper!' }]);
      } else {
        setQuestion(data);
        setMessages(prev => [...prev, { role: 'ai', text: `${data.question}` }]);
      }
      goStep(2);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleGenerate = () => {
    setGenerating(true); setError('');
    setLivePaper('');
    streamDone.current = false;
    evtSourceRef.current?.close();
    const es = new EventSource(`${BASE}/api/generate-stream/${sessionId}`);
    evtSourceRef.current = es;
    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'token') {
          setLivePaper(prev => prev + (data.content || '').replace(/\\n/g, '\n').replace(/\\r/g, '\r'));
        } else if (data.type === 'error') {
          streamDone.current = true;
          setError(data.message || 'Generation failed');
          setGenerating(false);
          es.close();
        } else if (data.type === 'done') {
          streamDone.current = true;
          setResult(data.result);
          setStep(3);
          setGenerating(false);
          es.close();
        }
      } catch (e) {}
    };
    es.onerror = () => {
      if (streamDone.current) return;
      setError('Connection lost during generation');
      setGenerating(false);
      es.close();
    };
  };

  const enterEdit = () => {
    const pj = result.paper_json || {};
    setEditable({
      title: pj.title || '',
      authors: (pj.authors || []).map(a => ({ name: a.name || '', affiliation: a.affiliation || '', email: a.email || '' })),
      abstract: pj.abstract || '',
      keywords: Array.isArray(pj.keywords) ? pj.keywords.join(', ') : (pj.keywords || ''),
      sections: (pj.sections || []).map(s => ({ title: s.title || '', content: s.content || '' })),
      references: (pj.references || []).map(r => (typeof r === 'string' ? r : (r.citation || ''))),
    });
    setEditError('');
    setEditMode(true);
  };

  const updateEditable = (patch) => setEditable(prev => ({ ...prev, ...patch }));

  const updateAuthor = (i, patch) => setEditable(prev => ({
    ...prev,
    authors: prev.authors.map((a, j) => (j === i ? { ...a, ...patch } : a)),
  }));

  const updateSection = (i, patch) => setEditable(prev => ({
    ...prev,
    sections: prev.sections.map((s, j) => (j === i ? { ...s, ...patch } : s)),
  }));

  const updateReference = (i, value) => setEditable(prev => ({
    ...prev,
    references: prev.references.map((r, j) => (j === i ? value : r)),
  }));

  const handleSave = async () => {
    setSaving(true); setEditError('');
    try {
      const data = await apiService.savePaper(sessionId, editable);
      setResult(prev => ({ ...prev, html_content: data.html_content, paper_json: data.paper_json }));
      setEditMode(false);
      setPreviewKey(k => k + 1);
    } catch (e) { setEditError(e.message); }
    finally { setSaving(false); }
  };

  const handleAiEdit = async () => {
    if (!aiEditInput.trim()) return;
    setAiEditing(true); setEditError('');
    try {
      const data = await apiService.editPaper(sessionId, aiEditInput);
      setResult(data);
      setEditMode(false);
      setPreviewKey(k => k + 1);
      setAiEditInput('');
    } catch (e) { setEditError(e.message); }
    finally { setAiEditing(false); }
  };

  // ─── Mode selection ──────────────────────────────────────────────────────
  const handleSelectMode = async (selectedMode) => {
    setMode(selectedMode);
    setLoading(true); setError('');
    try {
      const data = await apiService.setMode(sessionId, selectedMode);
      if (selectedMode === 'resume') {
        if (data.ready) {
          setResumeReady(true);
          setResumeMessages([{ role: 'ai', text: `I've analyzed "${file.name}". Ready to generate your resume!` }]);
        } else if (data.question) {
          setResumeQuestion(data.question);
          setResumeMessages([{ role: 'ai', text: `I've analyzed your document for resume content. Let me ask a few questions.\n\n${data.question.question}` }]);
        }
        goStep(2);
      } else {
        // IEEE mode — set analysis and first question
        setAnalysis(data.analysis);
        const docTitle = data.analysis?.title || file?.name || 'Untitled';
        setUploadHistory(prev => prev.map(d =>
          d.sessionId === sessionId ? { ...d, title: docTitle } : d
        ));
        if (data.question) {
          setQuestion(data.question);
          setAiTyping(true);
          setTimeout(() => {
            setAiTyping(false);
            setMessages([{ role: 'ai', text: `I've analyzed "${file.name}". Let me ask a few questions.\n\n${data.question.question}` }]);
            goStep(2);
          }, 600);
        } else {
          setReady(true);
          setMessages([{ role: 'ai', text: `I've analyzed "${file.name}". The analysis is clear enough to generate a paper!` }]);
        }
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  // ─── Resume interview ────────────────────────────────────────────────────
  const answerResumeQuestion = async (answer) => {
    if (!resumeQuestion || !answer.trim()) return;
    setLoading(true);
    setResumeQuestion(null);
    const q = resumeQuestion.question;
    setResumeMessages(prev => [...prev, { role: 'user', text: answer }]);
    setAiTyping(true);
    try {
      const data = await apiService.submitResumeAnswer(sessionId, q, answer);
      setResumeCustomAnswer('');
      await new Promise(r => setTimeout(r, 700));
      if (data.ready) {
        setResumeReady(true); setAiTyping(false);
        setResumeMessages(prev => [...prev, { role: 'ai', text: 'Great — I have enough information to generate your resume!' }]);
      } else {
        setResumeQuestion(data); setAiTyping(false);
        setResumeMessages(prev => [...prev, { role: 'ai', text: data.question || '' }]);
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  // ─── Resume generation ───────────────────────────────────────────────────
  const handleResumeGenerate = () => {
    setResumeGenerating(true); setError('');
    setLiveResume('');
    streamDone.current = false;
    evtSourceResumeRef.current?.close();
    const es = new EventSource(`${BASE}/api/generate-resume-stream/${sessionId}`);
    evtSourceResumeRef.current = es;
    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'token') {
          setLiveResume(prev => prev + (data.content || '').replace(/\\n/g, '\n').replace(/\\r/g, '\r'));
        } else if (data.type === 'error') {
          streamDone.current = true;
          setError(data.message || 'Generation failed');
          setResumeGenerating(false);
          es.close();
        } else if (data.type === 'done') {
          streamDone.current = true;
          setResumeResult(data.result);
          setStep(3);
          setResumeGenerating(false);
          es.close();
        }
      } catch (e) {}
    };
    es.onerror = () => {
      if (streamDone.current) return;
      setError('Connection lost during generation');
      setResumeGenerating(false);
      es.close();
    };
  };

  // ─── Resume editing ──────────────────────────────────────────────────────
  const enterResumeEdit = () => {
    setResumeEditable(resumeResult.resume_text || '');
    setEditError('');
    setResumeEditMode(true);
  };

  const handleResumeSave = async () => {
    setResumeSaving(true); setEditError('');
    try {
      const data = await apiService.saveResume(sessionId, resumeEditable);
      setResumeResult(prev => ({ ...prev, ...data }));
      setResumeEditMode(false);
      setResumePreviewKey(k => k + 1);
    } catch (e) { setEditError(e.message); }
    finally { setResumeSaving(false); }
  };

  const handleResumeAiEdit = async () => {
    if (!resumeAiEditInput.trim()) return;
    setResumeAiEditing(true); setEditError('');
    try {
      const data = await apiService.editResume(sessionId, resumeAiEditInput);
      setResumeResult(data);
      setResumeEditMode(false);
      setResumePreviewKey(k => k + 1);
      setResumeAiEditInput('');
    } catch (e) { setEditError(e.message); }
    finally { setResumeAiEditing(false); }
  };

  const handleSelectDoc = (doc) => {
    if (doc.sessionId && doc.sessionId !== sessionId) {
      setSessionId(doc.sessionId);
      goStep(1);
    }
  };

  const currentDocInfo = file ? {
    name: file.name,
    size: file.size,
    lastModified: file.lastModified,
    sections: analysis?.present_sections?.length || 0,
    qaCount: messages.filter(m => m.role === 'user').length,
  } : null;

  const handleReset = () => {
    setFile(null);
    setSessionId(null);
    goStep(0);
  };

  return (
    <div className="flex flex-1 min-h-0 p-3 md:p-4 gap-3 md:gap-6">
      <Sidebar
        current={currentDocInfo}
        history={uploadHistory}
        onSelectDoc={handleSelectDoc}
        onReset={handleReset}
      />
      <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
        <div className={`flex-1 flex flex-col max-w-5xl w-full mx-auto min-h-0 ${(result || generating || resumeResult || resumeGenerating) ? 'py-0 space-y-0' : 'py-6 space-y-6'}`}>

          {!result && !generating && (
          <div className="flex justify-center items-center gap-0.5 md:gap-1 flex-wrap">
            {steps.map((s, i) => (
              <div key={s} className="flex items-center">
                <div
                  className="flex items-center gap-1 md:gap-2 px-2 md:px-3 py-1.5 text-xs font-mono transition-all duration-500 rounded-full"
                  style={
                    i === step
                      ? { backgroundColor: '#cc785c', color: '#ffffff', boxShadow: '0 2px 8px rgba(204,120,92,0.25)' }
                      : i < step
                      ? { backgroundColor: '#efe9de', color: '#141413' }
                      : { backgroundColor: 'transparent', color: '#6c6a64' }
                  }>
                  {i < step ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#cc785c" stroke="#ffffff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-[10px] leading-none font-mono"
                      style={{ backgroundColor: i === step ? '#ffffff' : '#e6dfd8', color: i === step ? '#cc785c' : '#6c6a64' }}>
                      {i + 1}
                    </span>
                  )}
                  <span className="hidden sm:inline">{s}</span>
                </div>
                {i < steps.length - 1 && <div className="w-6 md:w-8 h-px bg-hairline shrink-0" />}
              </div>
            ))}
          </div>
          )}

          {error && (
            <div className="rounded-2xl p-4 text-sm border shrink-0"
              style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4', color: '#c64545' }}>{error}</div>
          )}

          {step === 0 && (
            <div
              className="rounded-2xl border-2 transition-all duration-300 cursor-pointer select-none flex flex-col items-center justify-center text-center"
              style={{
                borderStyle: file ? 'solid' : 'dashed',
                borderColor: dragOver ? '#cc785c' : file ? '#cc785c' : '#e6dfd8',
                backgroundColor: file ? '#faf9f5' : dragOver ? 'rgba(204,120,92,0.04)' : '#efe9de',
                padding: file ? '32px 24px' : '64px 40px',
                transform: dragOver ? 'scale(1.01)' : 'scale(1)',
                boxShadow: dragOver ? '0 0 0 4px rgba(204,120,92,0.12), 0 4px 20px rgba(0,0,0,0.06)' : 'none',
              }}
              onClick={() => fileRef.current?.click()}
              onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>

              {!file && (
                <>
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
                    style={{ backgroundColor: '#e6dfd8', transform: dragOver ? 'scale(1.1)' : 'scale(1)', transition: 'transform 0.3s' }}>
                    <LogoMark size={32} />
                  </div>
                  <p className="text-lg mb-1.5 font-medium" style={{ color: '#141413' }}>
                    {dragOver ? 'Release to upload' : 'Upload your research documents'}
                  </p>
                  <p className="text-sm mb-6" style={{ color: '#6c6a64' }}>
                    Drag & drop or{' '}
                    <span style={{ color: '#cc785c', textDecoration: 'underline', textUnderlineOffset: '2px' }}>browse</span>
                    {' '}— any file type supported
                  </p>
                  <input ref={fileRef} type="file" className="hidden" onChange={handleFileSelect} />
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 w-full max-w-lg mt-2">
                    {FORMAT_INFO.map(fmt => (
                      <div key={fmt.label} className="rounded-xl px-2 py-2 text-center" style={{ backgroundColor: '#e6dfd8' }}>
                        <p className="text-xs font-semibold" style={{ color: '#141413' }}>{fmt.label}</p>
                        <p className="text-[10px] mt-0.5 leading-tight" style={{ color: '#6c6a64' }}>{fmt.desc}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {file && (
                <>
                  <div className="w-full max-w-md mb-5">
                    <div className="flex items-center gap-3 rounded-xl px-4 py-3 text-left"
                      style={{ backgroundColor: 'rgba(204,120,92,0.06)', border: '1px solid rgba(204,120,92,0.15)' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#cc785c" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                      </svg>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm truncate font-medium" style={{ color: '#141413' }}>{file.name}</p>
                        <p className="text-xs" style={{ color: '#6c6a64' }}>{formatSize(file.size)}</p>
                      </div>
                      <button onClick={e => { e.stopPropagation(); setFile(null); }}
                        className="text-xs hover:opacity-70 shrink-0" style={{ color: '#c64545' }}>✕</button>
                    </div>
                  </div>
                  <input ref={fileRef} type="file" className="hidden" onChange={handleFileSelect} />
                  <button onClick={e => { e.stopPropagation(); handleUpload(); }} disabled={loading}
                    className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40 disabled:cursor-not-allowed">
                    {loading ? <>Uploading<TypingDots /></> : 'Upload'}
                  </button>
                </>
              )}
            </div>
          )}

          {step === 1 && !loading && !analysis && (
            <div className="rounded-2xl border transition-all duration-200 bg-surface-card border-hairline">
              <div className="p-5 md:p-8 text-center">
                <h2 className="text-xl md:text-2xl font-display mb-2 font-normal text-ink" style={{ letterSpacing: '-0.5px' }}>Choose your output</h2>
                <p className="text-sm text-muted mb-6">What would you like to generate from this document?</p>
                <div className="flex flex-wrap justify-center gap-3">
                  <button onClick={() => handleSelectMode('resume')}
                    className="rounded-full text-sm font-medium px-6 py-3 bg-primary text-white transition-all active:scale-[0.95] hover:shadow-md">
                    Generate Resume
                  </button>
                  <button onClick={() => handleSelectMode('ieee')}
                    className="rounded-full text-sm font-medium px-6 py-3 border border-hairline text-ink transition-all active:scale-[0.95] hover:bg-canvas">
                    Generate IEEE Paper
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 1 && !loading && analysis && mode === 'ieee' && (
            <div className="rounded-2xl border transition-all duration-200 bg-surface-card border-hairline">
              <div className="p-5 md:p-8">
                <h2 className="text-xl md:text-2xl font-display mb-4 font-normal text-ink" style={{ letterSpacing: '-0.5px' }}>Analysis complete</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="rounded-2xl p-4 border border-hairline bg-canvas">
                    <p className="text-xs font-mono uppercase mb-1 text-muted">Title</p>
                    <p className="font-medium text-ink">{analysis.title || 'Auto-detected'}</p>
                  </div>
                  <div className="rounded-2xl p-4 border border-hairline bg-canvas">
                    <p className="text-xs font-mono uppercase mb-1 text-muted">Domain</p>
                    <p className="font-medium text-ink">{analysis.domain || 'General'}</p>
                  </div>
                </div>
                {analysis.present_sections && (
                  <div className="mb-6">
                    <p className="text-xs font-mono uppercase mb-2 text-muted">Detected Sections</p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.present_sections.map(s => (
                        <span key={s} className="px-3 py-1 text-sm rounded-full bg-canvas border border-hairline text-muted">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {analysis.missing_info?.length > 0 && (
                  <div className="mb-6">
                    <p className="text-xs font-mono uppercase mb-2 text-muted">Missing Information</p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.missing_info.map(m => (
                        <span key={m} className="px-3 py-1 text-sm rounded-full"
                          style={{ backgroundColor: '#fdf0ef', border: '1px solid #e8b4b4', color: '#c64545' }}>{m}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 1 && loading && (
            <div className="rounded-2xl p-8 border animate-pulse bg-surface-card border-hairline">
              <div className="h-6 w-48 rounded-full mb-4 bg-hairline" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="h-20 rounded-2xl bg-hairline" />
                <div className="h-20 rounded-2xl bg-hairline" />
              </div>
              <div className="h-8 w-32 rounded-full bg-hairline" />
            </div>
          )}

          {(step === 2 || (step === 1 && question)) && (
            <div className="flex flex-col border rounded-2xl overflow-hidden flex-1 min-h-0 bg-canvas border-hairline"
              style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.04)' }}>
              <div className="px-4 md:px-6 py-3 border-b border-hairline text-sm shrink-0 flex items-center gap-2 text-muted">
                <span className="w-2 h-2 rounded-full bg-accent-teal" />
                <span className="hidden sm:inline">AI Interview —</span> answering questions
              </div>
              <div className="flex-1 overflow-y-auto px-4 md:px-6 py-5 space-y-4" style={{ scrollBehavior: 'smooth' }}>
                {messages.length === 0 && !aiTyping && (
                  <div className="flex flex-col items-center justify-center h-full text-center text-muted">
                    <span className="w-12 h-12 rounded-full flex items-center justify-center mb-3 text-lg bg-surface-card">💬</span>
                    <p className="text-sm">The interview will begin after analysis.</p>
                  </div>
                )}
                {messages.map((m, i) => {
                  const prevRole = i > 0 ? messages[i-1].role : null;
                  const isConsecutive = m.role === prevRole;
                  return (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} ${isConsecutive ? 'mt-1' : 'mt-4'} ${i === messages.length - 1 ? 'animate-fadeIn' : ''}`}>
                      <div className="flex items-start gap-2 max-w-[80%]">
                        {m.role === 'ai' && (
                          <span className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-[11px] font-semibold bg-primary text-white">AI</span>
                        )}
                        <div className="rounded-2xl px-4 py-3 text-sm leading-relaxed"
                          style={m.role === 'user'
                            ? { backgroundColor: 'var(--primary)', color: '#ffffff', borderBottomRightRadius: '6px' }
                            : { backgroundColor: 'var(--surface-card)', color: '#252523', borderBottomLeftRadius: '6px' }}>
                          {m.text.split('\n').map((l, j) => (
                            <p key={j} className={j > 0 ? 'mt-2' : ''}>{l}</p>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {aiTyping && (
                  <div className="flex justify-start">
                    <div className="flex items-start gap-2">
                      <span className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-[11px] font-semibold bg-primary text-white">AI</span>
                      <div className="rounded-2xl px-4 py-3 bg-surface-card" style={{ borderBottomLeftRadius: '6px' }}>
                        <TypingDots />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEnd} />
              </div>
              <div className="px-4 md:px-6 py-4 border-t border-hairline shrink-0 bg-canvas">
                {showFollowUp && question && (
                  <div className="mb-3 p-4 rounded-2xl border" style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4' }}>
                    <p className="text-xs font-mono uppercase flex items-center gap-1.5 mb-2 text-error">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                      </svg>
                      Clarify: {followUp?.follow_up?.replace(/\*\*(.*?)\*\*/g, '$1')}
                    </p>
                    {followUp?.options?.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-2">
                        {followUp.options.map((o, i) => (
                          <button key={i} onClick={() => handleFollowUpAnswer(o)} disabled={loading}
                            className="rounded-full text-sm px-4 py-2 transition-all active:scale-[0.95] hover:opacity-85 bg-canvas border border-hairline text-ink">
                            {o}
                          </button>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <input className="flex-1 rounded-full px-4 py-2 text-sm outline-none border transition-all duration-200 bg-canvas text-ink"
                        style={{ borderColor: '#e8b4b4', boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.04)' }}
                        placeholder="Type your answer..."
                        value={customFollowUp} onChange={e => setCustomFollowUp(e.target.value)}
                        onFocus={e => { e.target.style.borderColor = 'var(--primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(204,120,92,0.15)'; }}
                        onBlur={e => { e.target.style.borderColor = '#e8b4b4'; e.target.style.boxShadow = 'inset 0 1px 2px rgba(0,0,0,0.04)'; }}
                        onKeyDown={e => e.key === 'Enter' && handleFollowUpAnswer(customFollowUp)} />
                      <button onClick={() => handleFollowUpAnswer(customFollowUp)} disabled={loading || !customFollowUp.trim()}
                        className="rounded-full text-sm font-medium px-4 py-2 bg-error text-white transition-all active:scale-[0.95] disabled:opacity-40">
                        Send
                      </button>
                    </div>
                  </div>
                )}
                {question && !showFollowUp && (
                  <div>
                    <p className="text-xs font-mono uppercase mb-2.5 flex items-center gap-1.5 text-muted">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                      {question.options?.length > 0 ? 'Choose an option or type a custom answer' : 'Type your answer'}
                    </p>
                    {question.options?.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {question.options.map((o, i) => (
                          <button key={i} onClick={() => answerQuestion(o)} disabled={loading}
                            className="rounded-full text-sm px-4 py-2 transition-all active:scale-[0.95] hover:opacity-85 bg-canvas border border-hairline text-ink">
                            {o}
                          </button>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <input className="flex-1 rounded-full px-5 py-2.5 text-sm outline-none border transition-all duration-200 bg-canvas border-hairline text-ink"
                        style={{ boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.04)' }}
                        placeholder={question.options?.length > 0 ? 'Or type a custom answer...' : 'Type your answer...'}
                        value={customAnswer} onChange={e => setCustomAnswer(e.target.value)}
                        onFocus={e => { e.target.style.borderColor = 'var(--primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(204,120,92,0.15)'; }}
                        onBlur={e => { e.target.style.borderColor = 'var(--hairline)'; e.target.style.boxShadow = 'inset 0 1px 3px rgba(0,0,0,0.04)'; }}
                        onKeyDown={e => e.key === 'Enter' && answerQuestion(customAnswer)} />
                      <button onClick={() => answerQuestion(customAnswer)} disabled={loading || !customAnswer.trim()}
                        className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40">
                        Send
                      </button>
                    </div>
                  </div>
                )}
                {!question && !showFollowUp && messages.length > 0 && (
                  <p className="text-xs text-center text-muted">Waiting for AI response...</p>
                )}
              </div>
            </div>
          )}

          {(step === 3 || ready) && !result && !generating && (
            <div className="rounded-2xl border transition-all duration-200 bg-surface-card border-hairline">
              <div className="p-5 md:p-8 text-center">
                <p className="text-base md:text-lg mb-4 font-display text-ink" style={{ letterSpacing: '-0.3px' }}>Ready to generate your IEEE-format paper</p>
                <button onClick={handleGenerate}
                  className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95]">
                  Generate Paper
                </button>
              </div>
            </div>
          )}

          {generating && (
            <div className="flex flex-col border rounded-2xl overflow-hidden bg-surface-dark border-surface-dark-elevated min-h-0"
              style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.15)', maxHeight: 'calc(100vh - 180px)' }}>
              <div className="px-5 py-3 border-b border-surface-dark-elevated shrink-0 flex items-center gap-2 text-muted">
                <span className="w-2 h-2 rounded-full animate-pulse bg-accent-teal" />
                <span className="text-xs font-mono">Generating paper</span>
                <TypingDots />
              </div>
              <div className="flex-1 overflow-y-auto p-5">
                <pre className="text-sm whitespace-pre-wrap font-serif leading-relaxed" style={{ color: '#d4d0c8' }}>
                  {livePaper || <span className="text-muted">Waiting for response...</span>}
                </pre>
              </div>
            </div>
          )}

          {/* ─── Resume interview (step 2, mode=resume) ──────────────────── */}
          {mode === 'resume' && (step === 2 || (step === 1 && resumeQuestion)) && (
            <div className="flex flex-col border rounded-2xl overflow-hidden flex-1 min-h-0 bg-canvas border-hairline"
              style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.04)' }}>
              <div className="px-4 md:px-6 py-3 border-b border-hairline text-sm shrink-0 flex items-center gap-2 text-muted">
                <span className="w-2 h-2 rounded-full bg-accent-teal" />
                <span className="hidden sm:inline">Resume Interview —</span> answering questions
              </div>
              <div className="flex-1 overflow-y-auto px-4 md:px-6 py-5 space-y-4" style={{ scrollBehavior: 'smooth' }}>
                {resumeMessages.map((m, i) => {
                  const prevRole = i > 0 ? resumeMessages[i-1].role : null;
                  const isConsecutive = m.role === prevRole;
                  return (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} ${isConsecutive ? 'mt-1' : 'mt-4'} ${i === resumeMessages.length - 1 ? 'animate-fadeIn' : ''}`}>
                      <div className="flex items-start gap-2 max-w-[80%]">
                        {m.role === 'ai' && (
                          <span className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-[11px] font-semibold bg-primary text-white">AI</span>
                        )}
                        <div className="rounded-2xl px-4 py-3 text-sm leading-relaxed"
                          style={m.role === 'user'
                            ? { backgroundColor: 'var(--primary)', color: '#ffffff', borderBottomRightRadius: '6px' }
                            : { backgroundColor: 'var(--surface-card)', color: '#252523', borderBottomLeftRadius: '6px' }}>
                          {m.text.split('\n').map((l, j) => (
                            <p key={j} className={j > 0 ? 'mt-2' : ''}>{l}</p>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {aiTyping && (
                  <div className="flex justify-start">
                    <div className="flex items-start gap-2">
                      <span className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-[11px] font-semibold bg-primary text-white">AI</span>
                      <div className="rounded-2xl px-4 py-3 bg-surface-card" style={{ borderBottomLeftRadius: '6px' }}>
                        <TypingDots />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEnd} />
              </div>
              <div className="px-4 md:px-6 py-4 border-t border-hairline shrink-0 bg-canvas">
                {resumeQuestion && (
                  <div>
                    <p className="text-xs font-mono uppercase mb-2.5 flex items-center gap-1.5 text-muted">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                      {resumeQuestion.options?.length > 0 ? 'Choose an option or type a custom answer' : 'Type your answer'}
                    </p>
                    {resumeQuestion.options?.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {resumeQuestion.options.map((o, i) => (
                          <button key={i} onClick={() => answerResumeQuestion(o)} disabled={loading}
                            className="rounded-full text-sm px-4 py-2 transition-all active:scale-[0.95] hover:opacity-85 bg-canvas border border-hairline text-ink">
                            {o}
                          </button>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <input className="flex-1 rounded-full px-5 py-2.5 text-sm outline-none border transition-all duration-200 bg-canvas border-hairline text-ink"
                        style={{ boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.04)' }}
                        placeholder={resumeQuestion.options?.length > 0 ? 'Or type a custom answer...' : 'Type your answer...'}
                        value={resumeCustomAnswer} onChange={e => setResumeCustomAnswer(e.target.value)}
                        onFocus={e => { e.target.style.borderColor = 'var(--primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(204,120,92,0.15)'; }}
                        onBlur={e => { e.target.style.borderColor = 'var(--hairline)'; e.target.style.boxShadow = 'inset 0 1px 3px rgba(0,0,0,0.04)'; }}
                        onKeyDown={e => e.key === 'Enter' && answerResumeQuestion(resumeCustomAnswer)} />
                      <button onClick={() => answerResumeQuestion(resumeCustomAnswer)} disabled={loading || !resumeCustomAnswer.trim()}
                        className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40">
                        Send
                      </button>
                    </div>
                  </div>
                )}
                {!resumeQuestion && resumeMessages.length > 0 && (
                  <p className="text-xs text-center text-muted">Waiting for AI response...</p>
                )}
              </div>
            </div>
          )}

          {/* ─── Resume ready to generate (step 3, mode=resume) ──────────── */}
          {mode === 'resume' && (step === 3 || resumeReady) && !resumeResult && !resumeGenerating && (
            <div className="rounded-2xl border transition-all duration-200 bg-surface-card border-hairline">
              <div className="p-5 md:p-8 text-center">
                <p className="text-base md:text-lg mb-4 font-display text-ink" style={{ letterSpacing: '-0.3px' }}>Ready to generate your resume</p>
                <button onClick={handleResumeGenerate}
                  className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95]">
                  Generate Resume
                </button>
              </div>
            </div>
          )}

          {/* ─── Resume generating ────────────────────────────────────────── */}
          {mode === 'resume' && resumeGenerating && (
            <div className="flex flex-col border rounded-2xl overflow-hidden bg-surface-dark border-surface-dark-elevated min-h-0"
              style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.15)', maxHeight: 'calc(100vh - 180px)' }}>
              <div className="px-5 py-3 border-b border-surface-dark-elevated shrink-0 flex items-center gap-2 text-muted">
                <span className="w-2 h-2 rounded-full animate-pulse bg-accent-teal" />
                <span className="text-xs font-mono">Generating resume</span>
                <TypingDots />
              </div>
              <div className="flex-1 overflow-y-auto p-5">
                <pre className="text-sm whitespace-pre-wrap font-sans leading-relaxed" style={{ color: '#d4d0c8' }}>
                  {liveResume || <span className="text-muted">Waiting for response...</span>}
                </pre>
              </div>
            </div>
          )}

          {result && mode !== 'resume' && (
            <div className="flex flex-col rounded-2xl border bg-surface-dark border-surface-dark-elevated overflow-hidden min-h-0"
              style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.15)', maxHeight: 'calc(100vh - 180px)' }}>
              <div className="px-5 md:px-8 py-4 border-b border-surface-dark-elevated shrink-0 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-display text-on-dark flex items-center gap-2">
                  Paper generated <span className="text-accent-teal">✓</span>
                </h2>
                <div className="flex flex-wrap gap-2">
                  {!editMode && (
                    <button onClick={enterEdit}
                      className="rounded-full text-sm font-medium px-4 py-1.5 transition-all active:scale-[0.95] inline-flex items-center gap-1.5 border border-surface-dark-elevated text-muted hover:border-on-dark-soft hover:text-white">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                      Edit Document
                    </button>
                  )}
                  <a href={apiService.getDownloadUrl(sessionId, "pdf")}
                    className="rounded-full text-sm font-medium px-4 py-1.5 transition-all active:scale-[0.95] inline-flex items-center gap-1.5 bg-primary text-white"
                    download={result.filename_html.replace('.html', '.pdf')}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                    Download PDF
                  </a>
                  <a href={apiService.getDownloadUrl(sessionId, "html")}
                    className="rounded-full text-sm font-medium px-4 py-1.5 border transition-all active:scale-[0.95] border-surface-dark-elevated text-muted hover:border-on-dark-soft hover:text-white"
                    download={result.filename_html}>
                    Download HTML
                  </a>
                </div>
              </div>

              {editMode && editable ? (
                <div className="flex-1 min-h-0 overflow-y-auto p-5 md:p-8 space-y-6">
                  <div>
                    <p className="text-xs font-mono uppercase mb-1.5 text-muted">Title</p>
                    <input className="w-full rounded-xl px-4 py-2.5 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary"
                      value={editable.title} onChange={e => updateEditable({ title: e.target.value })} />
                  </div>

                  <div>
                    <p className="text-xs font-mono uppercase mb-2 text-muted">Authors</p>
                    <div className="space-y-2">
                      {editable.authors.map((a, i) => (
                        <div key={i} className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                          <input className="rounded-xl px-3 py-2 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary" placeholder="Name"
                            value={a.name} onChange={e => updateAuthor(i, { name: e.target.value })} />
                          <input className="rounded-xl px-3 py-2 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary" placeholder="Affiliation"
                            value={a.affiliation} onChange={e => updateAuthor(i, { affiliation: e.target.value })} />
                          <input className="rounded-xl px-3 py-2 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary" placeholder="Email"
                            value={a.email} onChange={e => updateAuthor(i, { email: e.target.value })} />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="text-xs font-mono uppercase mb-1.5 text-muted">Abstract</p>
                    <textarea className="w-full rounded-xl px-4 py-3 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary resize-y min-h-[90px]"
                      value={editable.abstract} onChange={e => updateEditable({ abstract: e.target.value })} />
                  </div>

                  <div>
                    <p className="text-xs font-mono uppercase mb-1.5 text-muted">Index Terms (comma separated)</p>
                    <input className="w-full rounded-xl px-4 py-2.5 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary"
                      value={editable.keywords} onChange={e => updateEditable({ keywords: e.target.value })} />
                  </div>

                  <div>
                    <p className="text-xs font-mono uppercase mb-2 text-muted">Sections</p>
                    <div className="space-y-4">
                      {editable.sections.map((s, i) => (
                        <div key={i} className="rounded-xl p-4 border border-surface-dark-elevated">
                          <input className="w-full rounded-lg px-3 py-2 text-sm font-medium outline-none bg-surface-dark text-on-dark border border-transparent focus:border-primary mb-2"
                            value={s.title} onChange={e => updateSection(i, { title: e.target.value })} />
                          <textarea className="w-full rounded-lg px-3 py-2 text-sm outline-none bg-surface-dark text-on-dark border border-transparent focus:border-primary resize-y min-h-[100px]"
                            value={s.content} onChange={e => updateSection(i, { content: e.target.value })} />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="text-xs font-mono uppercase mb-2 text-muted">References</p>
                    <div className="space-y-2">
                      {editable.references.map((r, i) => (
                        <textarea key={i} className="w-full rounded-xl px-3 py-2 text-sm outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary resize-y min-h-[48px]"
                          value={r} onChange={e => updateReference(i, e.target.value)} />
                      ))}
                    </div>
                  </div>

                  {editError && (
                    <div className="rounded-xl p-3 text-sm border" style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4', color: '#c64545' }}>{editError}</div>
                  )}

                  <div className="flex gap-2 pt-1">
                    <button onClick={handleSave} disabled={saving}
                      className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40">
                      {saving ? 'Saving…' : 'Save Changes'}
                    </button>
                    <button onClick={() => setEditMode(false)} disabled={saving}
                      className="rounded-full text-sm font-medium px-5 py-2.5 border border-surface-dark-elevated text-muted hover:text-white transition-all active:scale-[0.95] disabled:opacity-40">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex-1 min-h-0">
                  <iframe
                    key={previewKey}
                    src={result?.preview_html || apiService.getDownloadUrl(sessionId, "html")}
                    className="w-full h-full border-0"
                    title="Paper Preview"
                  />
                </div>
              )}

              <div className="px-5 md:px-8 py-4 border-t border-surface-dark-elevated shrink-0 bg-surface-dark">
                <p className="text-xs font-mono uppercase mb-2 text-muted">Ask AI to edit</p>
                <div className="flex gap-2">
                  <input className="flex-1 rounded-full px-5 py-2.5 text-sm outline-none border transition-all duration-200 bg-surface-dark-elevated text-on-dark border-transparent focus:border-primary"
                    placeholder="e.g. Shorten the abstract, add a Limitations section, make the conclusion stronger"
                    value={aiEditInput} onChange={e => setAiEditInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleAiEdit()} />
                  <button onClick={handleAiEdit} disabled={aiEditing || !aiEditInput.trim()}
                    className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40 inline-flex items-center gap-1.5">
                    {aiEditing ? <>Editing<TypingDots /></> : 'Apply'}
                  </button>
                </div>
                {editError && !editMode && (
                  <div className="mt-2 rounded-xl p-3 text-sm border" style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4', color: '#c64545' }}>{editError}</div>
                )}
              </div>
            </div>
          )}

          {/* ─── Resume result / edit (mode=resume) ───────────────────────── */}
          {mode === 'resume' && resumeResult && (
            <div className="flex flex-col rounded-2xl border bg-surface-dark border-surface-dark-elevated overflow-hidden min-h-0"
              style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.15)', maxHeight: 'calc(100vh - 180px)' }}>
              <div className="px-5 md:px-8 py-4 border-b border-surface-dark-elevated shrink-0 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-display text-on-dark flex items-center gap-2">
                  Resume generated <span className="text-accent-teal">✓</span>
                </h2>
                <div className="flex flex-wrap gap-2">
                  {!resumeEditMode && (
                    <button onClick={enterResumeEdit}
                      className="rounded-full text-sm font-medium px-4 py-1.5 transition-all active:scale-[0.95] inline-flex items-center gap-1.5 border border-surface-dark-elevated text-muted hover:border-on-dark-soft hover:text-white">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                      Edit Resume
                    </button>
                  )}
                  <a href={apiService.getResumeDownloadUrl(sessionId, "pdf")}
                    className="rounded-full text-sm font-medium px-4 py-1.5 transition-all active:scale-[0.95] inline-flex items-center gap-1.5 bg-primary text-white"
                    download={resumeResult.filename_html?.replace('.html', '.pdf')}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                    Download PDF
                  </a>
                  <a href={apiService.getResumeDownloadUrl(sessionId, "html")}
                    className="rounded-full text-sm font-medium px-4 py-1.5 border transition-all active:scale-[0.95] border-surface-dark-elevated text-muted hover:border-on-dark-soft hover:text-white"
                    download={resumeResult.filename_html}>
                    Download HTML
                  </a>
                </div>
              </div>

              {resumeEditMode ? (
                <div className="flex-1 min-h-0 overflow-y-auto p-5 md:p-8">
                  <textarea className="w-full h-full min-h-[400px] rounded-xl px-4 py-3 text-sm font-mono outline-none bg-surface-dark-elevated text-on-dark border border-transparent focus:border-primary resize-y"
                    value={resumeEditable} onChange={e => setResumeEditable(e.target.value)} />
                  {editError && (
                    <div className="mt-3 rounded-xl p-3 text-sm border" style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4', color: '#c64545' }}>{editError}</div>
                  )}
                  <div className="flex gap-2 pt-3">
                    <button onClick={handleResumeSave} disabled={resumeSaving}
                      className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40">
                      {resumeSaving ? 'Saving…' : 'Save Changes'}
                    </button>
                    <button onClick={() => setResumeEditMode(false)} disabled={resumeSaving}
                      className="rounded-full text-sm font-medium px-5 py-2.5 border border-surface-dark-elevated text-muted hover:text-white transition-all active:scale-[0.95] disabled:opacity-40">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex-1 min-h-0">
                  <iframe
                    key={resumePreviewKey}
                    src={`${BASE}/api/preview-resume/${sessionId}/html`}
                    className="w-full h-full border-0"
                    title="Resume Preview"
                  />
                </div>
              )}

              <div className="px-5 md:px-8 py-4 border-t border-surface-dark-elevated shrink-0 bg-surface-dark">
                <p className="text-xs font-mono uppercase mb-2 text-muted">Ask AI to edit</p>
                <div className="flex gap-2">
                  <input className="flex-1 rounded-full px-5 py-2.5 text-sm outline-none border transition-all duration-200 bg-surface-dark-elevated text-on-dark border-transparent focus:border-primary"
                    placeholder="e.g. Add more skills, shorten the summary, reorder sections"
                    value={resumeAiEditInput} onChange={e => setResumeAiEditInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleResumeAiEdit()} />
                  <button onClick={handleResumeAiEdit} disabled={resumeAiEditing || !resumeAiEditInput.trim()}
                    className="rounded-full text-sm font-medium px-5 py-2.5 bg-primary text-white transition-all active:scale-[0.95] disabled:opacity-40 inline-flex items-center gap-1.5">
                    {resumeAiEditing ? <>Editing<TypingDots /></> : 'Apply'}
                  </button>
                </div>
                {editError && !resumeEditMode && (
                  <div className="mt-2 rounded-xl p-3 text-sm border" style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4', color: '#c64545' }}>{editError}</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
