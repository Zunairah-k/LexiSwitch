export const LANG = {
  en: { name: "English", color: "var(--color-en)", tint: "rgba(43, 68, 181, 0.10)" },
  hi: { name: "Hindi", color: "var(--color-hi)", tint: "rgba(20, 133, 100, 0.12)" },
  te: { name: "Telugu", color: "var(--color-te)", tint: "rgba(179, 38, 58, 0.10)" },
  other: { name: "Other", color: "var(--color-other)", tint: "rgba(122, 122, 140, 0.12)" },
};

export const langInfo = (code) =>
  LANG[code] ?? { name: code, color: "var(--color-other)", tint: "rgba(122, 122, 140, 0.12)" };

export const abbr = (code) => code.toUpperCase();