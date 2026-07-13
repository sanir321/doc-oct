import { useNavigate } from 'react-router-dom';
import LogoMark from './components/LogoMark';

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

  return (
    <div className="min-h-screen bg-canvas text-body">
      {/* Fixed Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-canvas border-b border-hairline">
        <div className="max-w-5xl mx-auto px-4 md:px-6 h-14 md:h-16 flex items-center justify-between">
          <span className="text-ink text-sm font-medium flex items-center gap-2">
            <LogoMark size={16} />
            PaperAI
          </span>
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/generate')}
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
            AI-Powered Generation
          </span>
        </div>

        <h1 className="font-display text-5xl md:text-6xl font-normal leading-[1.05] mb-6 text-ink"
          style={{ letterSpacing: '-1.5px' }}>
          Upload once.<br />
          Paper or resume.
        </h1>

        <p className="text-body text-base max-w-xl mx-auto mb-10 leading-relaxed">
          Upload any document — AI extracts everything, interviews you on gaps, then generates either an
          IEEE-formatted research paper or a professional resume. Two modes, one upload.
        </p>

        <div className="flex flex-wrap justify-center gap-4">
            <button onClick={() => navigate('/generate')}
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
          {['PDF', 'DOCX', 'Images', 'TXT', 'LaTeX', 'Code', 'CSV', 'HTML'].map(b => (
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
              Everything you need — whether you're writing a paper or a résumé
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
            Ready to generate?
          </h2>
          <p className="mb-8 max-w-md mx-auto" style={{ color: 'rgba(255,255,255,0.8)' }}>
            Upload a document and pick your mode — paper or resume. AI does the rest.
          </p>
          <button onClick={() => navigate('/generate')}
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
