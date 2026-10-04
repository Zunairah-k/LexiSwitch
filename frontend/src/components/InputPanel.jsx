const EXAMPLES = [
  { label: "Telugu + English", text: "Nenu assignment submit chesanu but mam asked for corrections" },
  { label: "Hindi + English", text: "Kal office mein meeting hai but I'm not sure" },
  { label: "Three languages", text: "Nenu kal office mein meeting attend cheyyali but I'm not sure" },
  { label: "Native script", text: "నేను assignment submit చేశాను" },
];

export default function InputPanel({ value, onChange, onSubmit, loading }) {
  const empty = !value.trim();
  return (
    <section>
      <div className="rounded-xl border border-rule bg-white/60 p-5 transition-colors focus-within:border-ink">
        <label
          htmlFor="lexi-input"
          className="font-mono text-[11px] uppercase tracking-[0.18em] text-ink-soft"
        >
          Enter multilingual or code-switched text
        </label>
        <textarea
          id="lexi-input"
          rows={3}
          maxLength={2000}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") onSubmit();
          }}
          placeholder="Nenu assignment submit chesanu but mam asked for corrections."
          className="mt-2 w-full resize-none bg-transparent font-display text-2xl leading-snug outline-none placeholder:text-ink-soft/50"
        />
        <div className="mt-3 flex items-center justify-between gap-4">
          <span className="font-mono text-[11px] text-ink-soft">Ctrl + Enter to analyze</span>
          <button
            type="button"
            onClick={() => onSubmit()}
            disabled={empty || loading}
            className="rounded-full bg-ink px-6 py-2.5 font-mono text-xs uppercase tracking-[0.16em] text-paper transition hover:bg-te disabled:opacity-40 disabled:hover:bg-ink"
          >
            {loading ? "Analyzing…" : "Analyze →"}
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            type="button"
            onClick={() => {
              onChange(ex.text);
              onSubmit(ex.text);
            }}
            className="rounded-full border border-rule bg-white/50 px-4 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-soft transition hover:border-ink hover:text-ink"
          >
            {ex.label}
          </button>
        ))}
      </div>
    </section>
  );
}