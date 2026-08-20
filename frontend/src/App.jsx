import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const ACCEPTED = ".pdf,.epub,.txt";

export default function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  function pickFile(f) {
    if (!f) return;
    setFile(f);
    setStatus("idle");
    setResult(null);
    setError(null);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    pickFile(f);
  }

  async function handleExtract() {
    if (!file) return;
    setStatus("loading");
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/summarize", { method: "POST", body: form });

      if (!res.ok) {
        // Pre-stream validation errors (bad file, too long, etc.) still
        // come back as plain JSON with a normal HTTP error status.
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let summary = "";

      const handleLine = (line) => {
        if (!line.trim()) return;
        const event = JSON.parse(line);

        if (event.type === "meta") {
          setResult({ filename: event.filename, char_count: event.char_count, summary: "" });
          setStatus("streaming");
        } else if (event.type === "chunk") {
          summary += event.text;
          const snapshot = summary;
          setResult((prev) => (prev ? { ...prev, summary: snapshot } : prev));
        } else if (event.type === "error") {
          throw new Error(event.detail);
        }
        // "done" needs no handling — the loop ending is enough.
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // last entry may be an incomplete line — keep it buffered

        for (const line of lines) handleLine(line);
      }
      if (buffer.trim()) handleLine(buffer);

      setStatus("done");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  return (
    <div className="page">
      <header className="masthead">
        <span className="eyebrow">reading room</span>
        <h1>Book Summarizer</h1>
      </header>

      <section
        className={`slot ${dragActive ? "slot--active" : ""} ${file ? "slot--filled" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          hidden
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
        {file ? (
          <>
            <span className="slot__filename">{file.name}</span>
            <span className="slot__hint">click to choose a different book</span>
          </>
        ) : (
          <>
            <span className="slot__title">Drop a book here</span>
            <span className="slot__hint">PDF · EPUB · TXT</span>
          </>
        )}
      </section>

      <button
        className="extract-btn"
        disabled={!file || status === "loading" || status === "streaming"}
        onClick={handleExtract}
      >
        {status === "loading" || status === "streaming" ? "Reading…" : "Extract the ideas"}
      </button>

      {error && (
        <div className="error-box">
          <span className="error-box__label">Couldn't finish that one.</span>
          <span>{error}</span>
        </div>
      )}

      {result && (
        <section className="result">
          <div className="catalog-bar">
            <span className="catalog-bar__title">{result.filename}</span>
            <span className="catalog-bar__meta">
              {result.char_count.toLocaleString()} chars
            </span>
          </div>

          <div className="page-sheet">
            {status === "done" && <span className="stamp">extracted</span>}
            <div className="prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result.summary}
              </ReactMarkdown>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
