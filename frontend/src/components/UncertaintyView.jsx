import { langInfo } from "../lib/languages";

export default function UncertaintyView({ items, onSelect }) {
  if (!items.length) {
    return (
      <p className="text-sm text-ink-soft">
        No word needed the n-gram model here: every token was decided by a script rule or a
        dictionary match, so there are no model probabilities to show.
      </p>
    );
  }

  return (
    <div>
      <ul className="space-y-3">
        {items.map((u) => {
          const a = langInfo(u.language);
          const b = langInfo(u.runner_up);
          return (
            <li key={u.index}>
              <button
                type="button"
                onClick={() => onSelect(u.index)}
                className="w-full rounded-lg border border-rule bg-white/50 px-4 py-3 text-left transition hover:border-ink"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <span className="font-display text-xl">{u.token}</span>
                  <span className="font-mono text-xs text-ink-soft">
                    <span style={{ color: a.color }}>{a.name} {(u.probability * 100).toFixed(0)}%</span>
                    {" vs "}
                    <span style={{ color: b.color }}>
                      {b.name} {(u.runner_up_probability * 100).toFixed(0)}%
                    </span>
                  </span>
                </div>
                <div className="mt-2 flex h-1.5 w-full gap-[2px] overflow-hidden rounded-full bg-rule/70">
                  <div style={{ width: `${u.probability * 100}%`, backgroundColor: a.color }} />
                  <div style={{ width: `${u.runner_up_probability * 100}%`, backgroundColor: b.color }} />
                </div>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="mt-4 text-xs leading-relaxed text-ink-soft">
        Sorted by the gap between the model's top two languages. A small gap means the model was
        unsure, not necessarily wrong. Any remaining probability belongs to other languages.
      </p>
    </div>
  );
}