import { motion } from "framer-motion";
import { langInfo } from "../lib/languages";

export default function MiniCanvas({ side, tokens, hover, setHover }) {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-6 rounded-xl border border-rule bg-white/50 px-5 py-6">
      {tokens.map((t, i) => {
        const info = langInfo(t.language);
        const key = `${side}-${t.index}`;
        const same = hover.lang === t.language;
        const exact = hover.key === key;
        const dim = hover.lang !== null && !same;
        const delay = i * 0.06;
        const enter = () => setHover({ lang: t.language, key });
        const leave = () => setHover({ lang: null, key: null });
        return (
          <motion.div
            key={t.index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.3 }}
          >
            <button
              type="button"
              onMouseEnter={enter}
              onMouseLeave={leave}
              onFocus={enter}
              onBlur={leave}
              aria-label={`${t.text}, ${info.name}`}
              className="flex flex-col items-start rounded-md px-1.5 pb-1.5 pt-1 text-left outline-none transition duration-200"
              style={{
                backgroundColor: same ? info.tint : "transparent",
                opacity: dim ? 0.45 : 1,
                boxShadow: exact ? `0 0 0 2px ${info.color}` : "none",
              }}
            >
              <span className="font-display text-2xl leading-tight">{t.text}</span>
              <motion.span
                className="mt-1 block h-[3px] w-full origin-left rounded-full"
                style={{ backgroundColor: info.color }}
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: delay + 0.2, duration: 0.35 }}
              />
              <span
                className="mt-1 font-mono text-[9px] font-medium uppercase tracking-[0.16em]"
                style={{ color: info.color }}
              >
                {info.name}
              </span>
            </button>
          </motion.div>
        );
      })}
    </div>
  );
}