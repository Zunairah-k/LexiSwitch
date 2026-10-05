import { useState } from "react";
import { compare } from "../lib/api";
import MiniCanvas from "./MiniCanvas";
import FlowBar from "./FlowBar";
import Fingerprint from "./Fingerprint";
import CompareTable from "./CompareTable";

const PAIRS = [
  {
    label: "Telugu pair",
    a: "I submitted my assignment yesterday.",
    b: "Nenu assignment submit chesanu yesterday.",
  },
  {
    label: "Hindi pair",
    a: "I will call you after the meeting.",
    b: "Main meeting ke baad tumhe call karunga.",
  },
];

const NO_HOVER = { lang: null, key: null };

function Card({ title, children }) {
  return (
    <div>
      {title && (
        <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">{title}</h3>
      )}
      <div className="rounded-xl border border-rule bg-white/50 p-5">{children}</div>
    </div>
  );
}

export default function CompareView() {
  const [a, setA] = useState(PAIRS[0].a);
  const [b, setB] = useState(PAIRS[0].b);
  const [res, setRes] = useState(null);
  const [runId, setRunId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hover, setHover] = useState(NO_HOVER);

  async function run(ta = a, tb = b) {
    if (!ta.trim() || !tb.trim()) return;
    setLoading(true);
    setError("");
    try {
      setRes(await compare(ta, tb));
      setHover(NO_HOVER);
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

  const input = (id, label, hint, value, set) => (
    <div className="rounded-xl border border-rule bg-white/60 p-4 transition-colors focus-within:border-ink">
      <label htmlFor={id} className="font-mono text-[11px] uppercase tracking-[0.18em] text-ink-soft">
        {label}
      </label>
      <p className="text-xs text-ink-soft">{hint}</p>
      <textarea
        id={id}
        rows={3}
        maxLength={2000}
        value={value}
        onChange={(e) => set(e.target.value)}
        className="mt-2 w-full resize-none bg-transparent font-display text-xl leading-snug outline-none"
      />
    </div>
  );

  return (
    <div>
      <div className="grid gap-4 md:grid-cols-2">
        {input("cmp-a", "Text A", "Try a single-language sentence", a, setA)}
        {input("cmp-b", "Text B", "Try a code-switched sentence", b, setB)}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {PAIRS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => {
              setA(p.a);
              setB(p.b);
              run(p.a, p.b);
            }}
            className="rounded-full border border-rule bg-white/50 px-4 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-soft transition hover:border-ink hover:text-ink"
          >
            {p.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => run()}
          disabled={!a.trim() || !b.trim() || loading}
          className="ml-auto rounded-full bg-ink px-6 py-2.5 font-mono text-xs uppercase tracking-[0.16em] text-paper transition hover:bg-te disabled:opacity-40 disabled:hover:bg-ink"
        >
          {loading ? "Comparing…" : "Compare →"}
        </button>
      </div>

      {error && <p className="mt-6 rounded-lg border border-te px-4 py-3 text-sm text-te">{error}</p>}

      {res && (
        <div className="mt-10 space-y-10">
          <p className="font-mono text-[11px] text-ink-soft">
            Hover a word or a bar to highlight every word of the same language in both texts.
          </p>
          <div className="grid gap-8 md:grid-cols-2">
            {[
              ["A", res.a],
              ["B", res.b],
            ].map(([side, data]) => (
              <div key={`${side}-${runId}`} className="space-y-5">
                <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-ink-soft">
                  Text {side}
                </h2>
                <MiniCanvas side={side} tokens={data.tokens} hover={hover} setHover={setHover} />
                <Card title="Language flow">
                  <FlowBar segments={data.analysis.segments} hover={hover} setHover={setHover} />
                </Card>
                <Card title="Language fingerprint">
                  <Fingerprint distribution={data.analysis.distribution} />
                </Card>
              </div>
            ))}
          </div>
          <Card title="Side by side">
            <CompareTable a={res.a.analysis} b={res.b.analysis} />
          </Card>
        </div>
      )}
    </div>
  );
}