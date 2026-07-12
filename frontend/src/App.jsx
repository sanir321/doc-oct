import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function ProfileSetup({ onSave, onClose }) {
  const [form, setForm] = useState({ name: '', course: '', degree: '', year: '' });
  const valid = form.name.trim() && form.course.trim() && form.degree.trim() && form.year.trim();

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}>
      <div className="w-full max-w-sm rounded-2xl border border-hairline bg-surface-card shadow-xl p-6"
        onClick={e => e.stopPropagation()}
        style={{ boxShadow: '0 8px 32px rgba(0,0,0,0.12)' }}>
        <h2 className="text-lg font-semibold mb-1 text-ink">Create Profile</h2>
        <p className="text-xs text-muted-soft mb-5">Tell us about yourself before we start</p>
        <div className="space-y-3">
          {[
            { key: 'name', label: 'Full Name', placeholder: 'e.g. John Doe' },
            { key: 'course', label: 'Course', placeholder: 'e.g. B.Tech Computer Science' },
            { key: 'degree', label: 'Degree', placeholder: 'e.g. Bachelor of Technology' },
            { key: 'year', label: 'Year', placeholder: 'e.g. 3rd Year' },
          ].map(f => (
            <div key={f.key}>
              <label className="text-xs font-medium mb-1 block text-ink">{f.label}</label>
              <input
                value={form[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full rounded-xl border border-hairline bg-canvas px-3.5 py-2.5 text-sm text-ink placeholder:text-muted-soft outline-none focus:border-primary transition-colors"
                onKeyDown={e => e.key === 'Enter' && valid && onSave(form)}
                autoFocus={f.key === 'name'}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-2 mt-5">
          <button onClick={onClose}
            className="flex-1 text-sm rounded-xl px-4 py-2.5 border border-hairline text-muted transition-colors hover:bg-canvas">
            Cancel
          </button>
          <button onClick={() => onSave(form)} disabled={!valid}
            className="flex-1 text-sm font-medium rounded-xl px-4 py-2.5 bg-primary text-white transition-all hover:opacity-90 disabled:opacity-40">
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}

const FEATURES = [
  {
    title: 'Upload Any File',
    desc: 'PDF, DOCX, images, code, Markdown, LaTeX — AI extracts & analyzes all content.',
  },
  {
    title: 'AI-Powered Interview',
    desc: 'Our AI identifies gaps in your document and asks targeted questions before generation.',
  },
  {
    title: 'IEEE-Format Output',
    desc: 'Generates well-structured academic papers following IEEE conference guidelines.',
  },
  {
    title: 'LaTeX & HTML Export',
    desc: 'Download .tex for Overleaf or HTML for instant print-to-PDF in your browser.',
  },
];

const STEPS = [
  { num: '01', title: 'Upload', desc: 'Upload your research notes, draft, or reference documents.' },
  { num: '02', title: 'Analysis', desc: 'AI analyzes your content and detects missing sections.' },
  { num: '03', title: 'Interview', desc: 'Answer clarifying questions to fill in the gaps.' },
  { num: '04', title: 'Generate', desc: 'Get a complete IEEE-format paper ready for submission.' },
];

function LogoMark({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <rect x="5" y="3" width="22" height="26" rx="2" stroke="#cc785c" strokeWidth="1.5" />
      <line x1="9" y1="10" x2="23" y2="10" stroke="#cc785c" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="9" y1="15" x2="20" y2="15" stroke="#cc785c" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="9" y1="20" x2="17" y2="20" stroke="#cc785c" strokeWidth="1.5" strokeLinecap="round"/>
      <circle cx="27" cy="6" r="6" fill="#cc785c"/>
      <path d="M25 6h4M27 4v4" stroke="#fff" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

export default function App() {
  const navigate = useNavigate();
  const [showProfile, setShowProfile] = useState(false);
  const [profile, setProfile] = useState(() => {
    const saved = localStorage.getItem('userProfile');
    return saved ? JSON.parse(saved) : null;
  });

  const handleGetStarted = () => {
    if (profile) {
      navigate('/generate');
    } else {
      setShowProfile(true);
    }
  };

  const saveProfile = (data) => {
    localStorage.setItem('userProfile', JSON.stringify(data));
    setProfile(data);
    setShowProfile(false);
    navigate('/generate');
  };

  const handleResetProfile = () => {
    localStorage.removeItem('userProfile');
    setProfile(null);
  };

  return (
    <div className="min-h-screen bg-canvas text-body">
      {/* Profile Setup Modal */}
      {showProfile && (
        <ProfileSetup onSave={saveProfile} onClose={() => setShowProfile(false)} />
      )}

      {/* Fixed Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-canvas border-b border-hairline">
        <div className="max-w-5xl mx-auto px-4 md:px-6 h-14 md:h-16 flex items-center justify-between">
          <span className="text-ink text-sm font-medium flex items-center gap-2">
            <LogoMark size={16} />
            Research Paper AI
          </span>
          <div className="flex items-center gap-4">
            <button onClick={handleGetStarted}
              className="text-sm font-medium rounded-md px-[18px] py-[10px] bg-primary text-on-primary transition-opacity hover:opacity-90">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-24 md:pt-32 pb-20 md:pb-24 px-4 md:px-6 max-w-5xl mx-auto text-center">
        <div className="mb-6 flex justify-center">
          <LogoMark size={48} />
        </div>
        <div className="inline-flex items-center gap-2 rounded-full px-[10px] py-[4px] mb-10 bg-surface-card">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-teal" />
          <span className="text-[11px] font-semibold tracking-[0.88px] uppercase text-muted">
            AI-Powered Academic Writing
          </span>
        </div>

        <h1 className="font-display text-5xl md:text-6xl font-normal leading-[1.05] mb-6 text-ink"
          style={{ letterSpacing: '-1.5px' }}>
          Upload your notes.<br />
          AI writes the paper.
        </h1>

        <p className="text-body text-base max-w-2xl mx-auto mb-10 leading-relaxed">
          Drop any file — PDF, DOCX, images, code, or plain text. AI extracts everything, interviews you on gaps, and outputs a complete IEEE-formatted paper.
        </p>

        <div className="flex flex-wrap justify-center gap-4">
          <button onClick={handleGetStarted}
            className="text-sm font-medium rounded-md px-[18px] py-[10px] bg-primary text-on-primary transition-opacity hover:opacity-90">
            Start Generating
          </button>
          <button
            className="text-sm font-medium rounded-md px-[17px] py-[9px] border border-hairline text-ink transition-colors"
            onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>
            How It Works
          </button>
        </div>

        {/* Tech badges */}
        <div className="flex flex-wrap justify-center gap-2 mt-12 pt-10 border-t border-hairline">
          {['PDF', 'DOCX', 'Images', 'Code', 'Markdown', 'LaTeX', 'CSV', 'HTML'].map(b => (
            <span key={b} className="rounded-full px-[10px] py-[4px] text-[11px] font-semibold tracking-[0.88px] uppercase bg-surface-card text-ink">
              {b}
            </span>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-4 md:px-6 py-16 md:py-24 bg-surface-soft">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <span className="inline-block rounded-full px-[10px] py-[4px] text-[11px] font-semibold tracking-[0.88px] uppercase mb-4 bg-surface-cream-strong text-ink">
              Features
            </span>
            <h2 className="font-display text-3xl md:text-4xl font-normal leading-[1.1] text-ink"
              style={{ letterSpacing: '-1px' }}>
              Why use this tool?
            </h2>
            <p className="mt-3 text-muted max-w-md mx-auto">
              Everything you need to go from idea to formatted paper
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FEATURES.map((f, i) => (
              <div key={f.title} className="rounded-xl p-7 bg-surface-card transition-opacity hover:opacity-90 animate-fadeIn opacity-0"
                style={{ animationDelay: `${i * 0.12}s`, animationFillMode: 'forwards' }}>
                <h3 className="text-lg font-semibold mb-2 text-ink">{f.title}</h3>
                <p className="text-sm text-muted-soft leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="px-4 md:px-6 py-16 md:py-24 max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full px-[10px] py-[4px] text-[11px] font-semibold tracking-[0.88px] uppercase mb-4 bg-surface-card text-ink">
            Workflow
          </span>
          <h2 className="font-display text-3xl md:text-4xl font-normal leading-[1.1] text-ink"
            style={{ letterSpacing: '-1px' }}>
            How it works
          </h2>
          <p className="mt-3 text-muted max-w-md mx-auto">
            From upload to download in 4 simple steps
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {STEPS.map((s, i) => (
            <div key={s.num} className="relative rounded-xl p-6 text-left bg-surface-card transition-opacity hover:opacity-90 animate-fadeIn opacity-0"
              style={{ animationDelay: `${0.5 + i * 0.15}s`, animationFillMode: 'forwards' }}>
              <div className="text-2xl font-normal mb-3 font-display text-primary">{s.num}</div>
              <h3 className="font-semibold mb-2 text-ink">{s.title}</h3>
              <p className="text-sm text-muted-soft leading-relaxed">{s.desc}</p>
              {i < STEPS.length - 1 && (
                <div className="hidden md:block absolute top-1/2 -right-4 text-2xl font-mono text-primary">→</div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-16 md:py-24 max-w-4xl mx-auto border-t border-hairline">
        <div className="text-center rounded-xl p-8 md:p-16 bg-primary">
          <h2 className="font-display text-3xl font-normal leading-[1.15] mb-3 text-white"
            style={{ letterSpacing: '-0.5px' }}>
            Ready to generate your paper?
          </h2>
          <p className="mb-8 max-w-md mx-auto" style={{ color: 'rgba(255,255,255,0.8)' }}>
            Upload your research document and let AI do the heavy lifting.
          </p>
          <button onClick={handleGetStarted}
            className="text-sm font-medium rounded-md px-[18px] py-[10px] bg-white text-ink transition-opacity hover:opacity-90">
            Get Started
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 md:py-16 px-6 bg-surface-dark">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm text-on-dark-soft flex items-center gap-2">
            <LogoMark size={14} />
            Research Paper AI
          </span>
          <span className="text-xs font-mono text-on-dark-soft">AI-powered academic writing assistant</span>
        </div>
      </footer>
    </div>
  );
}
