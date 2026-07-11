import { useState } from 'react';
import { Link } from 'react-router-dom';
import PaperWizard from '../components/PaperWizard';

export default function WizardPage() {
  const [sessionKey, setSessionKey] = useState(0);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      {/* Dynamic Island — floating dark pill */}
      <div className="pt-4 px-4 shrink-0">
        <nav className="w-full h-12 rounded-full flex items-center justify-between px-5"
          style={{
            backgroundColor: 'rgba(24,23,21,0.78)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
          }}>
          <Link to="/" className="flex items-center gap-2.5 text-sm font-medium tracking-tight hover:opacity-80 transition-opacity" style={{ color: '#eeede9' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#cc785c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 3L1 9l7 6" />
              <path d="M16 3l7 6-7 6" />
              <line x1="14" y1="2" x2="10" y2="22" />
            </svg>
            Research Paper Generator
          </Link>
          <div className="flex items-center gap-2">
            <button onClick={() => setSessionKey(k => k + 1)}
              className="text-xs font-medium rounded-full px-4 py-1.5 bg-primary text-white transition-all hover:opacity-90 active:scale-[0.95]">
              New Session
            </button>
            <Link to="/" className="text-xs transition-colors hover:opacity-70 px-2" style={{ color: '#a09e96' }}>
              Exit →
            </Link>
          </div>
        </nav>
      </div>

      <div className="flex-1 flex">
        <PaperWizard key={sessionKey} onNewSession={() => setSessionKey(k => k + 1)} />
      </div>
    </div>
  );
}
