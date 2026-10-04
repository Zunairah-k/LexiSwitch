import { motion } from "framer-motion";
import { langInfo } from "../lib/languages";

const names = (codes) => codes.map((c) => langInfo(c).name);

export default function StatStrip({ analysis: a }) {
  const items = [
    { label: "Languages detected", value: a.language_count, sub: names(a.languages).join(", ") || "—" },
    {
      label: "Tokens analyzed",
      value: a.tokens_analyzed,
      sub: a.tokens_neutral ? `${a.tokens_neutral} neutral skipped` : "all tokens",
    },
    {
      label: "Language switches",
      value: a.switch_count,
      sub: a.switch_density == null ? "—" : `density ${a.switch_density.toFixed(2)}`,
    },
    { label: "Dominant language", value: names(a.dominant_languages).join(" / ") || "—", small: true },
    { label: "Script", value: a.scripts.join(" + ") || "—", small: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-rule bg-rule md:grid-cols-5"
    >
      {items.map((it) => (
        <div key={it.label} className="bg-paper p-4">
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink-soft">
            {it.label}
          </div>
          <div className={`mt-2 font-display font-semibold ${it.small ? "text-xl" : "text-4xl"}`}>
            {it.value}
          </div>
          {it.sub && <div className="mt-1 text-xs text-ink-soft">{it.sub}</div>}
        </div>
      ))}
    </motion.div>
  );
}