import { useState, useRef, useEffect, useCallback } from 'react';
import { apiService, BASE } from '../config/api';

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

function CoralButton({ children, outline, danger, dark, onClick, disabled, small, className = '' }) {
  const size = small ? 'text-xs px-3 py-1.5' : 'text-sm px-5 py-2.5';
  let style;
  if (disabled) style = 'bg-hairline text-muted-soft opacity-40 cursor-not-allowed';
  else if (danger) style = 'bg-error text-white cursor-pointer';
  else if (outline) style = 'bg-transparent text-body border border-hairline cursor-pointer';
  else if (dark) style = 'bg-transparent text-on-dark-soft border border-surface-dark-elevated hover:text-white hover:border-on-dark-soft cursor-pointer';
  else style = 'bg-primary text-white cursor-pointer';
  return (
    <button className={`rounded-full font-medium transition-all active:scale-[0.95] ${style} ${size} ${className}`}
      onClick={onClick} disabled={disabled}>{children}</button>
  );
}

function Card({ children, hover, style, className = '' }) {
  return (
    <div className={`rounded-2xl border transition-all duration-200 ${hover ? 'hover:scale-[1.01] hover:shadow-md' : ''} bg-surface-card border-hairline ${className}`}
      style={style}>
      {children}
    </div>
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
    <aside className="hidden md:flex flex-col w-64 shrink-0">
      <div className="flex-1 rounded-2xl border border-hairline bg-surface-card flex flex-col overflow-hidden"
        style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}>
        {/* Header */}
        <div className="px-4 py-3.5 border-b border-hairline shrink-0 flex items-center gap-2.5 text-ink">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#cc785c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          <span className="text-sm font-medium">Documents</span>
        </div>

        {/* Document list — no scroll */}
        <div className="flex-1 overflow-hidden p-3 space-y-2">
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
  const [files, setFiles] = useState([]);
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
  const [customAnswer, setCustomAnswer] = useState('');
  const [customFollowUp, setCustomFollowUp] = useState('');
  const [uploadHistory, setUploadHistory] = useState([]);
  const chatEnd = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, aiTyping]);

  const goStep = useCallback((s) => {
    setPrevStep(step);
    setStep(s);
  }, [step]);

  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);
  const mergeFiles = (incoming) => setFiles(prev => {
    const existing = new Set(prev.map(f => f.name + f.lastModified));
    return [...prev, ...incoming.filter(f => !existing.has(f.name + f.lastModified))];
  });
  const handleDrop = (e) => { e.preventDefault(); setDragOver(false); mergeFiles(Array.from(e.dataTransfer.files)); };
  const handleFileSelect = (e) => mergeFiles(Array.from(e.target.files));

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx));

  const handleUpload = async () => {
    if (!files.length) { setError('Select at least one file'); return; }
    setLoading(true); setError('');
    try {
      let lastData = null;
      for (const f of files) {
        const data = await apiService.uploadFile(f);
        lastData = data;
        setSessionId(data.session_id);
        setAnalysis(data.analysis);
        setUploadHistory(prev => {
          const exists = prev.some(d => d.name === f.name && d.lastModified === f.lastModified);
          if (exists) return prev;
          return [...prev, {
            name: f.name,
            size: f.size,
            lastModified: f.lastModified,
            uploadedAt: Date.now(),
            sessionId: data.session_id,
            title: data.analysis?.title || null,
            sections: data.analysis?.present_sections?.length || 0,
          }];
        });
      }
      if (!lastData) return;
      goStep(1);
      if (lastData.question && !lastData.analysis.ready) {
        setQuestion(lastData.question);
        setAiTyping(true);
        setTimeout(() => {
          setAiTyping(false);
          setMessages([{ role: 'ai', text: `I've analyzed ${files.length} file(s). Let me ask a few questions.\n\n**${lastData.question.question}**` }]);
          goStep(2);
        }, 600);
      } else {
        setAiTyping(true);
        setTimeout(() => {
          setAiTyping(false);
          setMessages([{ role: 'ai', text: `I've analyzed ${files.length} file(s). The analysis is clear enough to generate a paper!` }]);
          setReady(true);
        }, 600);
      }
    } catch (e) { setError(e.message); setLoading(false); }
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
        setMessages(prev => [...prev, { role: 'ai', text: `**${data.question}**` }]);
      }
      goStep(2);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleGenerate = () => {
    setGenerating(true); setError('');
    setLivePaper('');
    streamDone.current = false;
    const es = new EventSource(`${BASE}/api/generate-stream/${sessionId}`);
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

  const handleReset = () => {
    onNewSession();
  };

  const handleSelectDoc = (doc) => {
    if (doc.sessionId && doc.sessionId !== sessionId) {
      setSessionId(doc.sessionId);
      goStep(1);
    }
  };

  const currentDocInfo = files.length ? {
    name: files.length === 1 ? files[0].name : `${files.length} files`,
    size: files.reduce((s, f) => s + f.size, 0),
    lastModified: files[0].lastModified,
    sections: analysis?.present_sections?.length || 0,
    qaCount: messages.filter(m => m.role === 'user').length,
  } : null;

  return (
    <div className="flex flex-1 p-3 md:p-4 gap-3 md:gap-6">
      <Sidebar
        current={currentDocInfo}
        history={uploadHistory}
        onSelectDoc={handleSelectDoc}
        onReset={handleReset}
      />

      <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
        <div className="flex-1 flex flex-col max-w-5xl w-full mx-auto py-6 space-y-6 min-h-0">
          {/* Step indicators */}
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

          {error && (
            <div className="rounded-2xl p-4 text-sm border shrink-0"
              style={{ backgroundColor: '#fdf0ef', borderColor: '#e8b4b4', color: '#c64545' }}>{error}</div>
          )}


          {/* Step 0: Upload — unified drop zone, no nested card */}
          {step === 0 && (
            <div
              className="rounded-2xl border-2 transition-all duration-300 cursor-pointer select-none flex flex-col items-center justify-center text-center"
              style={{
                borderStyle: files.length ? 'solid' : 'dashed',
                borderColor: dragOver ? '#cc785c' : files.length ? '#cc785c' : '#e6dfd8',
                backgroundColor: files.length
                    ? '#faf9f5'
                    : dragOver
                      ? 'rgba(204,120,92,0.04)'
                      : '#efe9de',
                padding: files.length ? '32px 24px' : '64px 40px',
                transform: dragOver ? 'scale(1.01)' : 'scale(1)',
                boxShadow: dragOver
                  ? '0 0 0 4px rgba(204,120,92,0.12), 0 4px 20px rgba(0,0,0,0.06)'
                  : 'none',
              }}
              onClick={() => fileRef.current?.click()}
              onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>

              {/* Empty state */}
              {!files.length && (
                <>
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
                    style={{
                      backgroundColor: '#e6dfd8',
                      transform: dragOver ? 'scale(1.1)' : 'scale(1)',
                      transition: 'transform 0.3s',
                    }}>
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
                      stroke="#6c6a64" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="12" y1="12" x2="12" y2="18" />
                      <line x1="9" y1="15" x2="15" y2="15" />
                    </svg>
                  </div>
                  <p className="text-lg mb-1.5 font-medium" style={{ color: '#141413' }}>
                    {dragOver ? 'Release to upload' : 'Upload your research documents'}
                  </p>
                  <p className="text-sm mb-6" style={{ color: '#6c6a64' }}>
                    Drag & drop or{' '}
                    <span style={{ color: '#cc785c', textDecoration: 'underline', textUnderlineOffset: '2px' }}>
                      browse
                    </span>{' '}
                    — any file type supported
                  </p>
                  <input ref={fileRef} type="file" multiple
                    className="hidden" onChange={handleFileSelect} />

                  {/* Format info */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 w-full max-w-lg mt-2">
                    {FORMAT_INFO.map(fmt => (
                      <div key={fmt.label} className="rounded-xl px-2 py-2 text-center"
                        style={{ backgroundColor: '#e6dfd8' }}>
                        <p className="text-xs font-semibold" style={{ color: '#141413' }}>{fmt.label}</p>
                        <p className="text-[10px] mt-0.5 leading-tight" style={{ color: '#6c6a64' }}>{fmt.desc}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Files selected state */}
              {files.length > 0 && (
                <>
                  <div className="w-full max-w-md space-y-2 mb-5">
                    {files.map((f, idx) => (
                      <div key={f.name + f.lastModified}
                        className="flex items-center gap-3 rounded-xl px-4 py-3 text-left"
                        style={{ backgroundColor: 'rgba(204,120,92,0.06)', border: '1px solid rgba(204,120,92,0.15)' }}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                          stroke="#cc785c" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="16" y1="13" x2="8" y2="13" />
                          <line x1="16" y1="17" x2="8" y2="17" />
                        </svg>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm truncate font-medium" style={{ color: '#141413' }}>{f.name}</p>
                          <p className="text-xs" style={{ color: '#6c6a64' }}>{formatSize(f.size)}</p>
                        </div>
                        <button onClick={e => { e.stopPropagation(); removeFile(idx); }}
                          className="text-xs hover:opacity-70 shrink-0" style={{ color: '#c64545' }}>
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                  <input ref={fileRef} type="file" multiple
                    className="hidden" onChange={handleFileSelect} />
                  <div className="flex flex-wrap gap-3 items-center">
                    <CoralButton small outline onClick={e => { e.stopPropagation(); fileRef.current?.click(); }}>
                      + Add More
                    </CoralButton>
                    <CoralButton disabled={loading} onClick={e => { e.stopPropagation(); handleUpload(); }}>
                      {loading ? <>Analyzing<TypingDots /></> : `Upload & Analyze (${files.length})`}
                    </CoralButton>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Step 1: Analysis */}
          {step === 1 && !loading && analysis && (
            <Card hover>
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
                <CoralButton onClick={skipInterview}>
                  {analysis.ready ? 'Skip to Generate →' : 'Start Interview →'}
                </CoralButton>
              </div>
            </Card>
          )}

          {/* Loading skeleton */}
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

          {/* Step 2: Interview */}
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
                          {m.text.split('\n').map((l, j) => {
                            const clean = l.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1');
                            return <p key={j} className={j > 0 ? 'mt-2' : ''}>{clean}</p>;
                          })}
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
                      Clarify: {followUp?.follow_up?.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1')}
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
                      <CoralButton small danger onClick={() => handleFollowUpAnswer(customFollowUp)} disabled={loading || !customFollowUp.trim()}>
                        Send
                      </CoralButton>
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
                        onFocus={e => {
                          e.target.style.borderColor = 'var(--primary)';
                          e.target.style.boxShadow = '0 0 0 3px rgba(204,120,92,0.15)';
                        }}
                        onBlur={e => {
                          e.target.style.borderColor = 'var(--hairline)';
                          e.target.style.boxShadow = 'inset 0 1px 3px rgba(0,0,0,0.04)';
                        }}
                        onKeyDown={e => e.key === 'Enter' && answerQuestion(customAnswer)} />
                      <CoralButton small onClick={() => answerQuestion(customAnswer)} disabled={loading || !customAnswer.trim()}>
                        Send
                      </CoralButton>
                    </div>
                  </div>
                )}
                {!question && !showFollowUp && messages.length > 0 && (
                  <p className="text-xs text-center text-muted">Waiting for AI response...</p>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Generate */}
          {(step === 3 || ready) && !result && !generating && (
            <Card hover>
              <div className="p-5 md:p-8 text-center">
                <p className="text-base md:text-lg mb-4 font-display text-ink" style={{ letterSpacing: '-0.3px' }}>Ready to generate your IEEE-format paper</p>
                <CoralButton onClick={handleGenerate}>
                  Generate Paper
                </CoralButton>
              </div>
            </Card>
          )}

          {/* Live document preview while generating */}
          {generating && (
            <div className="flex flex-col border rounded-2xl overflow-hidden flex-1 min-h-0 bg-surface-dark border-surface-dark-elevated"
              style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.15)' }}>
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

          {/* Result */}
          {result && (
            <div className="rounded-2xl p-5 md:p-8 border bg-surface-dark border-surface-dark-elevated"
              style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.15)' }}>
              <h2 className="text-xl md:text-2xl font-display font-normal leading-[1.15] mb-4 text-on-dark"
                style={{ letterSpacing: '-0.5px' }}>
                Paper generated <span className="text-accent-teal">✓</span>
              </h2>
              <div className="flex flex-wrap gap-3 mb-4">
                <a href={apiService.getDownloadUrl(sessionId, "pdf")}
                  className="rounded-full text-sm font-medium px-5 py-2.5 transition-all active:scale-[0.95] inline-flex items-center gap-2 bg-primary text-white"
                  download={result.filename_html.replace('.html', '.pdf')}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                  Download PDF
                </a>
                <a href={apiService.getDownloadUrl(sessionId, "tex")}
                  className="rounded-full text-sm font-medium px-5 py-2.5 border transition-all active:scale-[0.95] inline-flex items-center gap-2 border-surface-dark-elevated text-on-dark-soft hover:border-on-dark-soft hover:text-white"
                  download={result.filename_tex}>
                  Download .tex (Overleaf)
                </a>
                <a href={apiService.getDownloadUrl(sessionId, "html")}
                  className="rounded-full text-sm font-medium px-5 py-2.5 border transition-all active:scale-[0.95] border-surface-dark-elevated text-muted hover:border-on-dark-soft hover:text-white"
                  download={result.filename_html}>
                  Download HTML
                </a>
              </div>
              {result.paper_text && (
                <>
                  <hr className="border-t border-surface-dark-elevated my-6" />
                  <p className="text-xs font-mono uppercase tracking-wider mb-3 text-muted">Preview</p>
                  <div className="rounded-2xl p-4 text-sm max-h-96 overflow-y-auto whitespace-pre-wrap font-mono bg-surface-dark-soft text-on-dark-soft">
                    {result.paper_text.slice(0, 2000)}
                  </div>
                </>
              )}
              <button className="mt-6 text-sm transition-colors text-on-dark-soft hover:text-on-dark"
                onClick={handleReset}>
                Start Over
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
