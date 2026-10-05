import { langInfo } from "../lib/languages";

const fmt = (x) => (x == null ? "n/a" : x.toFixed(2));
const names = (codes) => codes.map((c) => langInfo(c).name).join(" / ") || "—";

export default function CompareTable({ a, b }) {
  const rows = [
    ["Language tokens", a.tokens_analyzed, b.tokens_analyzed],
    ["Languages detected", names(a.languages), names(b.languages)],
    ["Dominant language", names(a.dominant_languages), names(b.dominant_languages)],
    ["Language sequence", names(a.sequence).replaceAll(" / ", " → "), names(b.sequence).replaceAll(" / ", " → ")],
    ["Code-switches", a.switch_count, b.switch_count],
    ["Switch density", fmt(a.switch_density), fmt(b.switch_density)],
    ["Mixing index", fmt(a.mixing_index), fmt(b.mixing_index)],
    ["Script", a.scripts.join(" + ") || "—", b.scripts.join(" + ") || "—"],
  ];
  const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "es"}`;

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead>
            <tr className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">
              <th className="pb-3 pr-4 font-medium">Measure</th>
              <th className="pb-3 pr-4 font-medium">Text A</th>
              <th className="pb-3 font-medium">Text B</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, x, y]) => (
              <tr key={label} className="border-t border-rule">
                <td className="py-3 pr-4 font-mono text-xs text-ink-soft">{label}</td>
                <td className="py-3 pr-4 font-display text-lg">{x}</td>
                <td className="py-3 font-display text-lg">{y}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-sm leading-relaxed text-ink-soft">
        Text A has {plural(a.switch_count, "switch")} across {a.language_count}{" "}
        {a.language_count === 1 ? "language" : "languages"}; Text B has {plural(b.switch_count, "switch")}{" "}
        across {b.language_count} {b.language_count === 1 ? "language" : "languages"}.
      </p>
    </div>
  );
}