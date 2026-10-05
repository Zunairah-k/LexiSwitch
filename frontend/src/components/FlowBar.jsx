import { motion } from "framer-motion";
import { langInfo } from "../lib/languages";

export default function FlowBar({ segments, hover, setHover }) {
  if (!segments.length) return <p className="text-sm text-ink-soft">No language tokens.</p>;
  return (
    <div className="flex gap-1">
      {segments.map((seg, k) => {
        const info = langInfo(seg.language);
        const n = seg.token_indices.length;
        const dim = hover.lang !== null && hover.lang !== seg.language;
        return (
          <motion.div
            key={k}
            initial={{ clipPath: "inset(0 100% 0 0)" }}
            animate={{ clipPath: "inset(0 0% 0 0)" }}
            transition={{ delay: 0.2 + k * 0.1, duration: 0.45 }}
            onMouseEnter={() => setHover({ lang: seg.language, key: null })}
            onMouseLeave={() => setHover({ lang: null, key: null })}
            title={`${info.name}: ${n} ${n === 1 ? "token" : "tokens"}`}
            className="h-10 rounded px-2 py-1 font-mono text-[9px] uppercase tracking-wider text-paper transition-opacity duration-200"
            style={{ flexGrow: n, flexBasis: 0, minWidth: 28, backgroundColor: info.color, opacity: dim ? 0.45 : 1 }}
          >
            {info.name.slice(0, 3)}
          </motion.div>
        );
      })}
    </div>
  );
}