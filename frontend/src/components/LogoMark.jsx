export default function LogoMark({ size = 20 }) {
  const sw = size / 21;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <rect x="5" y="3" width="22" height="26" rx="2" stroke="#cc785c" strokeWidth={sw} />
      <line x1="9" y1="10" x2="23" y2="10" stroke="#cc785c" strokeWidth={sw} strokeLinecap="round"/>
      <line x1="9" y1="15" x2="20" y2="15" stroke="#cc785c" strokeWidth={sw} strokeLinecap="round"/>
      <line x1="9" y1="20" x2="17" y2="20" stroke="#cc785c" strokeWidth={sw} strokeLinecap="round"/>
      <circle cx="27" cy="6" r="6" fill="#cc785c"/>
      <path d="M25 6h4M27 4v4" stroke="#fff" strokeWidth={sw} strokeLinecap="round"/>
    </svg>
  );
}
