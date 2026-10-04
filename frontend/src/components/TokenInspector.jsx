import { langInfo } from "../lib/languages";

const METHOD = {
  "script-rule": "Script rule (only one language uses this script)",
  lexicon: "Dictionary lookup (word listed under one language)",
  "lexicon+char-ngram-nb": "Dictionary + n-gram model (word listed under several languages)",
  "char-ngram-nb": "Character n-gram model (word not in the dictionary)",
  "no-letters": "No letters (number or symbol)",
  "unsupported-script": "Script not supported by the model",
};

const prettyScript = (s) => (!s || s === "NONE" ? "—" : s.charAt(0) + s.slice(1).toLowerCase());

function Row({ label, children }) {
  return (
    <div className="mt-5">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">{label}</div>
      <div className="mt-1">{children}</div>
    </div>
  );
}

export default function TokenInspector({ token }) {
  if (!token) {
    return (
      <aside className="rounded-xl border border-dashed border-rule p-6 lg:sticky lg:top-6">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">Token inspector</p>
        <p className="mt-3 font-display text-lg italic text-ink-soft">
          Select a word in the sentence to inspect it.
        </p>
      </aside>
    );
  }

  const info = langInfo(token.language);
  const runner = token.runner_up ? langInfo(token.runner_up) : null;
  const p = token.probability;

  return (
    <aside
      className="rounded-xl border border-rule bg-white/60 p-6 lg:sticky lg:top-6"
      style={{ borderTop: `4px solid ${info.color}` }}
    >
      <Row label="Token">
        <span className="font-display text-3xl">{token.text}</span>
      </Row>
      <Row label="Language">
        <span className="font-display text-xl font-semibold" style={{ color: info.color }}>
          {info.name}
        </span>
      </Row>
      <Row label="Position">
        <span className="font-mono text-sm">{token.index + 1}</span>
      </Row>
      <Row label="Script">
        <span className="font-mono text-sm">{prettyScript(token.script)}</span>
      </Row>

      {p != null ? (
        <Row label="Model probability">
          <div className="font-mono text-sm">{(p * 100).toFixed(1)}%</div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-rule">
            <div
              className="h-full rounded-full"
              style={{ width: `${p * 100}%`, backgroundColor: info.color }}
            />
          </div>
          {runner && (
            <div className="mt-2 font-mono text-xs text-ink-soft">
              runner-up: {runner.name} {(token.runner_up_probability * 100).toFixed(1)}%
            </div>
          )}
          <p className="mt-2 text-xs leading-relaxed text-ink-soft">
            Naive Bayes probability, rescaled by temperature scaling fitted on held-out words.
          </p>
        </Row>
      ) : (
        <Row label="Model output">
          <span className="font-mono text-sm">{info.name}</span>
        </Row>
      )}

      <Row label="Decided by">
        <span className="text-sm leading-snug">{METHOD[token.method] ?? token.method}</span>
      </Row>
    </aside>
  );
}