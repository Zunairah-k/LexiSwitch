import { useState } from "react";
import { analyze } from "./lib/api";
import { langInfo } from "./lib/languages";
import Header from "./components/Header";
import InputPanel from "./components/InputPanel";
import StatStrip from "./components/StatStrip";
import LanguageCanvas from "./components/LanguageCanvas";
import TokenInspector from "./components/TokenInspector";

function SectionLabel({ children }) {
  return (
    <h2 className="mb-3 font-mono text-[11px] uppercase tracking-[0.2em] text-ink-soft">{children}</h2>
  );
}

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [runId, setRunId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  async function run(override) {
    const input = (typeof override === "string" ? override : text).trim();
    if (!input) return;
    setLoading(true);
    setError("");
    try {
      const data = await analyze(input);
      setResult(data);
      setSelected(null);
      setRunId((n) => n + 1);
    } catch (e) {
      setError(
        e instanceof TypeError
          ? "Cannot reach the analysis server. Is the backend running on port 8000?"
          : e.message
      );
    } finally {
      setLoading(false);
    }
  }

  const selectedToken = result && selected !== null ? result.tokens[selected] : null;

  return (
    <div className="mx-auto max-w-5xl px-5 pb-24">
      <Header />
      <InputPanel value={text} onChange={setText} onSubmit={run} loading={loading} />

      {error && (
        <p className="mt-6 rounded-lg border border-te px-4 py-3 text-sm text-te">{error}</p>
      )}

      {result && (
        <main className="mt-12 space-y-10">
          <StatStrip key={`stats-${runId}`} analysis={result.analysis} />

          <section>
            <SectionLabel>Language canvas</SectionLabel>
            <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
              <LanguageCanvas
                key={`canvas-${runId}`}
                tokens={result.tokens}
                selected={selected}
                onSelect={setSelected}
              />
              <TokenInspector token={selectedToken} />
            </div>
          </section>

          <p className="font-mono text-[11px] leading-relaxed text-ink-soft">
            Identifying among {result.model_languages.map((l) => langInfo(l.code).name).join(", ")} ·
            Unicode script rules, dictionary lookup and a character n-gram Naive Bayes classifier.
          </p>
        </main>
      )}
    </div>
  );
}