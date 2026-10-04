import { motion } from "framer-motion";
import { langInfo } from "../lib/languages";

export default function LanguageCanvas({ tokens, selected, onSelect }) {
  return (
    <div className="flex flex-wrap gap-x-7 gap-y-9 rounded-xl border border-rule bg-white/50 px-7 py-9">
      {tokens.map((t, i) => {
        const info = langInfo(t.language);
        const active = selected === t.index;
        const dim = selected !== null && !active;
        const delay = i * 0.07;
        return (
          <motion.div
            key={t.index}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.35 }}
          >
            <button
              type="button"
              onClick={() => onSelect(active ? null : t.index)}
              aria-pressed={active}
              aria-label={`${t.text}, ${info.name}`}
              className="flex flex-col items-start rounded-md px-2 pb-2 pt-1 text-left outline-none transition duration-200 hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-saffron"
              style={{ backgroundColor: active ? info.tint : "transparent", opacity: dim ? 0.55 : 1 }}
            >
              <span className="font-display text-3xl leading-tight sm:text-4xl">{t.text}</span>
              <motion.span
                className="mt-1 block h-[3px] w-full origin-left rounded-full"
                style={{ backgroundColor: info.color }}
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: delay + 0.25, duration: 0.4 }}
              />
              <motion.span
                className="mt-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.18em]"
                style={{ color: info.color }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: delay + 0.4 }}
              >
                {info.name}
              </motion.span>
            </button>
          </motion.div>
        );
      })}
    </div>
  );
}