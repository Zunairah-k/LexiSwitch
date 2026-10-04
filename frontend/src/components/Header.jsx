export default function Header() {
  return (
    <header className="pb-6 pt-10">
      <div className="flex items-center gap-3">
        <svg width="34" height="22" viewBox="0 0 34 22" aria-hidden="true">
          <rect x="0" y="0" width="22" height="6" rx="3" fill="var(--color-en)" />
          <rect x="12" y="8" width="22" height="6" rx="3" fill="var(--color-te)" />
          <rect x="4" y="16" width="22" height="6" rx="3" fill="var(--color-hi)" />
        </svg>
        <h1 className="font-display text-4xl font-bold tracking-tight">LexiSwitch</h1>
      </div>
      <p className="mt-2 font-mono text-xs uppercase tracking-[0.2em] text-ink-soft">
        Multilingual Token Analysis
      </p>
      <p className="mt-4 font-display text-xl italic text-ink-soft">
        Explore how languages interact inside a sentence.
      </p>
    </header>
  );
}