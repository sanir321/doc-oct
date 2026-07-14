import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LogoMark from './components/LogoMark';

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
    title: 'Two Modes — Paper or Resume',
    desc: 'Upload once, pick your mode. Generate a full IEEE paper or a professional resume from the same document.',
  },
  {
    title: 'AI Interview',
    desc: 'AI detects gaps and asks targeted questions before generating — ensures nothing is missed.',
  },
  {
    title: 'IEEE Paper Generator',
    desc: 'Well-structured papers following IEEE conference guidelines. PDF & HTML export.',
  },
  {
    title: 'AI Resume Builder',
    desc: 'Extracts experience, skills, and education. Formats a professional resume with download + AI editing.',
  },
  {
    title: 'Smart Editor',
    desc: 'Edit any section manually or ask the AI to rewrite, expand, or fix tone — all in the same view.',
  },
  {
    title: 'Upload Anything',
    desc: 'PDF, DOCX, images, code, Markdown, LaTeX — AI extracts & analyzes all content.',
  },
];

const STEPS = [
  { num: '01', title: 'Upload', desc: 'Upload any file — research notes, draft, or reference documents.' },
  { num: '02', title: 'Pick Mode', desc: 'Choose your output — IEEE research paper or professional resume.' },
  { num: '03', title: 'AI Interview', desc: 'Answer clarifying questions to fill in the gaps.' },
  { num: '04', title: 'Generate', desc: 'Get your formatted paper or resume. Download, edit, or regenerate.' },
];

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

  return (
    <div className="min-h-screen bg-canvas text-body">
      {/* Profile Setup Modal */}
      {showProfile && (
        <ProfileSetup onSave={saveProfile} onClose={() => setShowProfile(false)} />
      )}

      {/* Fixed Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-canvas/80 backdrop-blur-lg border-b border-hairline">
        <div className="max-w-5xl mx-auto px-4 md:px-6 h-14 md:h-16 flex items-center justify-between">
          <span className="text-ink text-sm font-medium flex items-center gap-2">
            <LogoMark size={16} />
            PaperAI
          </span>
          <div className="flex items-center gap-3">
            {profile && (
              <span className="text-xs text-muted truncate max-w-[120px] hidden sm:block">
                {profile.name}
              </span>
            )}
            <button onClick={handleGetStarted}
              className="text-sm font-medium rounded-md px-[18px] py-[10px] bg-primary text-on-primary transition-all hover:opacity-90 hover:shadow-lg active:scale-[0.97]">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-28 md:pt-36 pb-20 md:pb-28 px-4 md:px-6 max-w-5xl mx-auto text-center overflow-hidden">
        {/* Subtle ambient glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-[400px] rounded-full bg-primary/3 blur-3xl pointer-events-none" />

        <div className="relative">
          <div className="mb-8 flex justify-center animate-fadeIn">
            <LogoMark size={52} />
          </div>

          <h1 className="font-display text-5xl md:text-6xl font-normal leading-[1.05] mb-6 text-ink animate-fadeIn opacity-0"
            style={{ letterSpacing: '-1.5px', animationDelay: '0.1s', animationFillMode: 'forwards' }}>
            Upload once.<br />
            Paper or resume.
          </h1>

          <p className="text-body text-base max-w-xl mx-auto mb-10 leading-relaxed animate-fadeIn opacity-0"
            style={{ animationDelay: '0.2s', animationFillMode: 'forwards' }}>
            Upload any document — AI extracts everything, interviews you on gaps, then generates either an
            IEEE-formatted research paper or a professional resume. Two modes, one upload.
          </p>

          <div className="flex flex-wrap justify-center gap-4 animate-fadeIn opacity-0"
            style={{ animationDelay: '0.3s', animationFillMode: 'forwards' }}>
            <button onClick={handleGetStarted}
              className="text-sm font-medium rounded-md px-[22px] py-[11px] bg-primary text-on-primary transition-all hover:opacity-90 hover:shadow-lg hover:-translate-y-0.5 active:scale-[0.97]">
              Start Generating
            </button>
            <button
              className="text-sm font-medium rounded-md px-[21px] py-[10px] border border-hairline text-ink transition-all hover:bg-surface-card hover:border-ink/20 active:scale-[0.97]"
              onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>
              How It Works
            </button>
          </div>

          {/* Tech badges */}
          <div className="flex flex-wrap justify-center gap-2 mt-14 pt-10 border-t border-hairline animate-fadeIn opacity-0"
            style={{ animationDelay: '0.4s', animationFillMode: 'forwards' }}>
            {['PDF', 'DOCX', 'Images', 'TXT', 'LaTeX', 'Code', 'CSV', 'HTML'].map(b => (
              <span key={b}
                className="rounded-full px-[10px] py-[4px] text-[11px] font-semibold tracking-[0.88px] uppercase bg-surface-card text-ink transition-all hover:bg-surface-cream-strong hover:scale-105 cursor-default">
                {b}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Gradient divider */}
      <div className="max-w-5xl mx-auto px-4 md:px-6">
        <div className="h-px bg-gradient-to-r from-transparent via-hairline to-transparent" />
      </div>

      {/* Features */}
      <section className="px-4 md:px-6 py-20 md:py-28 bg-surface-soft">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16 animate-fadeIn opacity-0"
            style={{ animationFillMode: 'forwards' }}>
            <span className="inline-block rounded-full px-[10px] py-[4px] text-[11px] font-semibold tracking-[0.88px] uppercase mb-4 bg-surface-cream-strong text-ink">
              Features
            </span>
            <h2 className="font-display text-3xl md:text-4xl font-normal leading-[1.1] text-ink"
              style={{ letterSpacing: '-1px' }}>
              Why use this tool?
            </h2>
            <p className="mt-3 text-muted max-w-md mx-auto">
              Everything you need — whether you're writing a paper or a résumé
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FEATURES.map((f, i) => (
              <div key={f.title}
                className="group rounded-xl p-7 bg-surface-card border border-transparent transition-all hover:border-hairline hover:shadow-lg hover:-translate-y-0.5 animate-fadeIn opacity-0 cursor-default"
                style={{ animationDelay: `${i * 0.12}s`, animationFillMode: 'forwards' }}>
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/15 transition-colors">
                  <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2 text-ink">{f.title}</h3>
                <p className="text-sm text-muted-soft leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Gradient divider */}
      <div className="max-w-5xl mx-auto px-4 md:px-6">
        <div className="h-px bg-gradient-to-r from-transparent via-hairline to-transparent" />
      </div>

      {/* How it Works */}
      <section id="how-it-works" className="px-4 md:px-6 py-20 md:py-28 max-w-5xl mx-auto">
        <div className="text-center mb-16 animate-fadeIn opacity-0"
          style={{ animationFillMode: 'forwards' }}>
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
        <div className="relative grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Connecting line between step numbers */}
          <div className="hidden md:block absolute top-9 left-[calc(12.5%+36px)] right-[calc(12.5%+36px)] h-px bg-gradient-to-r from-primary/30 via-primary/15 to-transparent" />

          {STEPS.map((s, i) => (
            <div key={s.num}
              className="relative rounded-xl p-6 text-left bg-surface-card border border-transparent transition-all hover:border-hairline hover:shadow-md hover:-translate-y-0.5 animate-fadeIn opacity-0 cursor-default group"
              style={{ animationDelay: `${0.3 + i * 0.15}s`, animationFillMode: 'forwards' }}>
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-semibold font-mono group-hover:bg-primary/15 transition-colors">
                  {s.num}
                </span>
              </div>
              <h3 className="font-semibold mb-2 text-ink">{s.title}</h3>
              <p className="text-sm text-muted-soft leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Gradient divider */}
      <div className="max-w-5xl mx-auto px-4 md:px-6">
        <div className="h-px bg-gradient-to-r from-transparent via-hairline to-transparent" />
      </div>

      {/* CTA */}
      <section className="px-6 py-20 md:py-28 max-w-4xl mx-auto">
        <div className="relative text-center rounded-xl p-8 md:p-16 bg-primary overflow-hidden">
          {/* Decorative circles */}
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white/5 translate-x-1/2 -translate-y-1/2 pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-white/5 -translate-x-1/3 translate-y-1/3 pointer-events-none" />

          <div className="relative">
            <h2 className="font-display text-3xl md:text-4xl font-normal leading-[1.15] mb-3 text-white"
              style={{ letterSpacing: '-0.5px' }}>
              Ready to generate?
            </h2>
            <p className="mb-8 max-w-md mx-auto text-white/80 text-sm">
              Upload a document and pick your mode — paper or resume. AI does the rest.
            </p>
            <button onClick={handleGetStarted}
              className="text-sm font-medium rounded-md px-[22px] py-[11px] bg-white text-ink transition-all hover:shadow-xl hover:-translate-y-0.5 active:scale-[0.97]">
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 md:py-16 px-6 bg-surface-dark border-t border-white/5">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm text-on-dark-soft flex items-center gap-2 transition-colors hover:text-on-dark">
            <LogoMark size={14} />
            PaperAI
          </span>
          <span className="text-xs font-mono text-on-dark-soft">
            AI-powered paper & résumé generator
          </span>
        </div>
      </footer>
    </div>
  );
}
