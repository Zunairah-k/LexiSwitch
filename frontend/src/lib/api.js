async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(
      res.status === 422 ? "Please enter some text to analyze." : `Server error (${res.status})`
    );
  }
  return res.json();
}

export const analyze = (text) => post("/api/analyze", { text });
export const compare = (textA, textB) => post("/api/compare", { text_a: textA, text_b: textB });