import { motion } from "framer-motion";
import { abbr, langInfo } from "../lib/languages";

export default function LanguageCanvas({
  tokens,
  switches,
  selected,
  onSelect,
  focusSet,
  selectedSwitch,
  onSwitchSelect,
}) {
  const before = new Map(switches.map((s, k) => [s.to_token_index, { s, k }]));

  return (
    <div className="flex flex-wrap gap-x-7 gap-y-10 rounded-xl border border-rule bg-white/50 px-7 py-9">
      {tokens.map((t, i) => {
        const info = langInfo(t.language);
        const sw = before.get(t.index);
        const active = selected === t.index;
        const focused = !!focusSet && focusSet.has(t.index);
        const dim = !!focusSet && !focused;
        const swActive = !!sw && selectedSwitch === sw.k;
        const delay = i * 0.07;

        return (
          <motion.div
            key={t.index}
            className="relative"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.35 }}
          >
            {sw && (
              <button
                type="button"
                onClick={() => onSwitchSelect(swActive ? null : sw.k)}
                title={`Code-switch: ${langInfo(sw.s.from_language).name} → ${langInfo(sw.s.to_language).name}`}
                aria-label={`Code-switch ${sw.k + 1}`}
                className="group absolute bottom-7 top-0 -left-[19px] flex w-3.5 flex-col items-center outline-none"
              >
                <span
                  className={`whitespace-nowrap font-mono text-[8px] font-medium tracking-wider ${
                    swActive ? "text-ink" : "text-ink-soft"
                  }`}
                >
                  {abbr(sw.s.from_language)}→{abbr(sw.s.to_language)}
                </span>
                <span
                  className={`mt-1 w-[2px] flex-1 rounded-full transition-colors ${
                    swActive ? "bg-saffron" : "bg-rule group-hover:bg-ink-soft"
                  }`}
                />
              </button>
            )}

            <button
              type="button"
              onClick={() => onSelect(active ? null : t.index)}
              aria-pressed={active}
              aria-label={`${t.text}, ${info.name}`}
              className="flex flex-col items-start rounded-md px-2 pb-2 pt-1 text-left outline-none transition duration-200 hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-saffron"
              style={{ backgroundColor: focused ? info.tint : "transparent", opacity: dim ? 0.5 : 1 }}
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