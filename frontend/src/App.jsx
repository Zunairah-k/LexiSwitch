import { useState } from "react";
import { analyze } from "./lib/api";
import { langInfo } from "./lib/languages";
import Header from "./components/Header";
import InputPanel from "./components/InputPanel";
import StatStrip from "./components/StatStrip";
import LanguageCanvas from "./components/LanguageCanvas";
import TokenInspector from "./components/TokenInspector";
import FlowTimeline from "./components/FlowTimeline";
import Fingerprint from "./components/Fingerprint";
import AnalysisSummary from "./components/AnalysisSummary";
import UncertaintyView from "./components/UncertaintyView";

function Section({ title, children }) {
  return (
    <section>
      <h2 className="mb-3 font-mono text-[11px] uppercase tracking-[0.2em] text-ink-soft">{title}</h2>
      {children}
    </section>
  );
}

const Card = ({ children }) => (
  <div className="rounded-xl border border-rule bg-white/50 p-6">{children}</div>
);

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [runId, setRunId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [selectedSwitch, setSelectedSwitch] = useState(null);
  const [hoverSeg, setHoverSeg] = useState(null);

  async function run(override) {
    const input = (typeof override === "string" ? override : text).trim();
    if (!input) return;
    setLoading(true);
    setError("");
    try {
      const data = await analyze(input);
      setResult(data);
      setSelected(null);
      setSelectedSwitch(null);
      setHoverSeg(null);
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

  const a = result?.analysis;
  const selectedToken = result && selected !== null ? result.tokens[selected] : null;

  // What is highlighted in the sentence: hovered segment > selected word > selected switch.
  let focusSet = null;
  if (a) {
    if (hoverSeg !== null && a.segments[hoverSeg]) {
      focusSet = new Set(a.segments[hoverSeg].token_indices);
    } else if (selected !== null) {
      focusSet = new Set([selected]);
    } else if (selectedSwitch !== null && a.switches[selectedSwitch]) {
      const s = a.switches[selectedSwitch];
      focusSet = new Set([s.from_token_index, s.to_token_index]);
    }
  }
  const segOfSelected =
    a && selected !== null ? a.segments.findIndex((s) => s.token_indices.includes(selected)) : -1;

  return (
    <div className="mx-auto max-w-5xl px-5 pb-24">
      <Header />
      <InputPanel value={text} onChange={setText} onSubmit={run} loading={loading} />

      {error && (
        <p className="mt-6 rounded-lg border border-te px-4 py-3 text-sm text-te">{error}</p>
      )}

      {result && (
        <main className="mt-12 space-y-12">
          <StatStrip key={`stats-${runId}`} analysis={a} />

          <Section title="Language canvas">
            <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
              <LanguageCanvas
                key={`canvas-${runId}`}
                tokens={result.tokens}
                switches={a.switches}
                selected={selected}
                onSelect={setSelected}
                focusSet={focusSet}
                selectedSwitch={selectedSwitch}
                onSwitchSelect={setSelectedSwitch}
              />
              <TokenInspector token={selectedToken} />
            </div>
          </Section>

          <Section title="Language flow">
            <Card>
              <FlowTimeline
                key={`flow-${runId}`}
                segments={a.segments}
                switches={a.switches}
                tokens={result.tokens}
                hoverSeg={hoverSeg}
                onHoverSeg={setHoverSeg}
                activeSeg={segOfSelected >= 0 ? segOfSelected : null}
                selectedSwitch={selectedSwitch}
                onSwitchSelect={setSelectedSwitch}
              />
            </Card>
          </Section>

          <div className="grid gap-12 lg:grid-cols-2">
            <Section title="Language fingerprint">
              <Card>
                <Fingerprint key={`fp-${runId}`} distribution={a.distribution} />
              </Card>
            </Section>
            <Section title="Analysis summary">
              <Card>
                <AnalysisSummary analysis={a} numLanguages={result.model_languages.length} />
              </Card>
            </Section>
          </div>

          <Section title="Model uncertainty">
            <Card>
              <UncertaintyView items={a.uncertain_tokens} onSelect={setSelected} />
            </Card>
          </Section>

          <p className="font-mono text-[11px] leading-relaxed text-ink-soft">
            Identifying among {result.model_languages.map((l) => langInfo(l.code).name).join(", ")} ·
            Unicode script rules, dictionary lookup and a character n-gram Naive Bayes classifier.
          </p>
        </main>
      )}
    </div>
  );
}