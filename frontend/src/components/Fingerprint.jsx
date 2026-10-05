import { motion } from "framer-motion";
import { langInfo } from "../lib/languages";

export default function Fingerprint({ distribution }) {
  if (!distribution.length) {
    return <p className="text-sm text-ink-soft">No language tokens to show.</p>;
  }

  return (
    <div>
      <div className="flex h-9 w-full gap-[3px] overflow-hidden rounded-md">
        {distribution.map((d, i) => (
          <motion.div
            key={d.language}
            title={`${langInfo(d.language).name}: ${d.tokens} tokens`}
            style={{ backgroundColor: langInfo(d.language).color, flexBasis: 0, flexShrink: 0 }}
            initial={{ flexGrow: 0 }}
            animate={{ flexGrow: d.tokens }}
            transition={{ delay: 0.2 + i * 0.12, duration: 0.6 }}
          />
        ))}
      </div>

      <ul className="mt-5 space-y-4">
        {distribution.map((d, i) => {
          const info = langInfo(d.language);
          return (
            <li key={d.language}>
              <div className="flex items-baseline justify-between">
                <span
                  className="font-mono text-[11px] font-medium uppercase tracking-[0.16em]"
                  style={{ color: info.color }}
                >
                  {info.name}
                </span>
                <span className="font-mono text-xs text-ink-soft">
                  {d.tokens} {d.tokens === 1 ? "token" : "tokens"} · {(d.proportion * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-rule/70">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: info.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${d.proportion * 100}%` }}
                  transition={{ delay: 0.3 + i * 0.12, duration: 0.6 }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}