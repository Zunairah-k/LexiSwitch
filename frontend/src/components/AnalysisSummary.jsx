import { langInfo } from "../lib/languages";

function Item({ label, value, def }) {
  return (
    <div className="border-t border-rule py-4 first:border-t-0 first:pt-0">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">{label}</div>
      <div className="mt-1 font-display text-xl font-semibold">{value}</div>
      {def && <p className="mt-1 text-xs leading-relaxed text-ink-soft">{def}</p>}
    </div>
  );
}

export default function AnalysisSummary({ analysis: a, numLanguages }) {
  const fmt = (x) => (x == null ? "n/a" : x.toFixed(2));
  return (
    <div>
      <Item
        label="Language sequence"
        value={a.sequence.map((c) => langInfo(c).name).join(" → ") || "—"}
        def="The language of each run of consecutive words, in order."
      />
      <Item
        label="Switch density"
        value={fmt(a.switch_density)}
        def="Switches ÷ (language tokens − 1): the share of neighbouring word pairs where the language changes. Needs at least two language tokens."
      />
      <Item
        label="Mixing index"
        value={fmt(a.mixing_index)}
        def={`(1 − Σp²) ÷ ((k − 1)·Σp²), where p is each language's share of tokens and k = ${numLanguages} (the languages the model can identify). 0 means one language; 1 means an even mix of all ${numLanguages}.`}
      />
      <Item
        label="Neutral tokens"
        value={a.tokens_neutral}
        def="Numbers, symbols and unsupported scripts are skipped and never count as a switch."
      />
    </div>
  );
}