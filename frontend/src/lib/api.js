export async function analyze(text) {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(
      res.status === 422 ? "Please enter some text to analyze." : `Server error (${res.status})`
    );
  }
  return res.json();
}