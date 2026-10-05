import { motion } from "framer-motion";
import { langInfo } from "../lib/languages";

export default function FlowTimeline({
  segments,
  switches,
  tokens,
  hoverSeg,
  onHoverSeg,
  activeSeg,
  selectedSwitch,
  onSwitchSelect,
}) {
  if (!segments.length) {
    return <p className="text-sm text-ink-soft">No language tokens to show.</p>;
  }

  const base = tokens.length * 0.07 + 0.3;
  const sw = selectedSwitch !== null ? switches[selectedSwitch] : null;
  const anyFocus = hoverSeg !== null || activeSeg !== null;

  return (
    <div>
      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-[520px] gap-1">
          {segments.map((seg, k) => {
            const info = langInfo(seg.language);
            const n = seg.token_indices.length;
            const words = seg.token_indices.map((i) => tokens[i].text).join(" ");
            const highlighted = hoverSeg === k || activeSeg === k;
            const picked = selectedSwitch === k;

            return (
              <div
                key={k}
                className="relative"
                style={{ flexGrow: n, flexBasis: 0, minWidth: 64 }}
                onMouseEnter={() => onHoverSeg(k)}
                onMouseLeave={() => onHoverSeg(null)}
              >
                <motion.div
                  initial={{ clipPath: "inset(0 100% 0 0)" }}
                  animate={{ clipPath: "inset(0 0% 0 0)" }}
                  transition={{ delay: base + k * 0.12, duration: 0.5 }}
                  className="h-16 rounded-md px-3 py-2 text-paper transition-opacity duration-200"
                  style={{
                    backgroundColor: info.color,
                    opacity: anyFocus && !highlighted ? 0.5 : 1,
                  }}
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.16em]">{info.name}</div>
                  <div className="mt-0.5 font-mono text-[10px] opacity-80">
                    {n} {n === 1 ? "token" : "tokens"}
                  </div>
                </motion.div>
                <p className="mt-2 truncate text-xs text-ink-soft" title={words}>
                  {words}
                </p>

                {k < segments.length - 1 && (
                  <motion.button
                    type="button"
                    initial={{ opacity: 0, scale: 0.6 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: base + (k + 1) * 0.12 + 0.1 }}
                    onClick={() => onSwitchSelect(picked ? null : k)}
                    title={`Code-switch ${k + 1}: ${langInfo(seg.language).name} → ${
                      langInfo(segments[k + 1].language).name
                    }`}
                    aria-label={`Code-switch ${k + 1}`}
                    className="absolute -right-[11px] top-5 z-10 flex h-5 w-5 items-center justify-center rounded-full border-2 border-paper text-[9px] font-bold outline-none focus-visible:ring-2 focus-visible:ring-saffron"
                    style={{
                      backgroundColor: picked ? "var(--color-saffron)" : "var(--color-ink)",
                      color: picked ? "var(--color-ink)" : "var(--color-paper)",
                    }}
                  >
                    {k + 1}
                  </motion.button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {switches.length === 0 && (
        <p className="mt-4 text-sm text-ink-soft">No language switch detected in this text.</p>
      )}
      {switches.length > 0 && !sw && (
        <p className="mt-4 text-sm text-ink-soft">
          Select a numbered marker to inspect a code-switch.
        </p>
      )}
      {sw && (
        <motion.div
          key={selectedSwitch}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-5 rounded-xl border border-rule bg-white/60 p-5"
        >
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">
            Code-switch {selectedSwitch + 1}
          </div>
          <div className="mt-2 font-display text-2xl font-semibold">
            <span style={{ color: langInfo(sw.from_language).color }}>
              {langInfo(sw.from_language).name}
            </span>
            <span className="mx-2 text-ink-soft">→</span>
            <span style={{ color: langInfo(sw.to_language).color }}>
              {langInfo(sw.to_language).name}
            </span>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">
                Boundary
              </div>
              <div className="mt-1 font-display text-xl">
                {tokens[sw.from_token_index].text}
                <span className="mx-2 text-ink-soft">|</span>
                {tokens[sw.to_token_index].text}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">
                Position
              </div>
              <div className="mt-1 font-mono text-sm">{sw.position}</div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}