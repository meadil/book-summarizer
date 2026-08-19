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

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/summarize", { method: "POST", body: form });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }

      setResult(data);
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
        disabled={!file || status === "loading"}
        onClick={handleExtract}
      >
        {status === "loading" ? "Reading…" : "Extract the ideas"}
      </button>

      {status === "error" && (
        <div className="error-box">
          <span className="error-box__label">Couldn't finish that one.</span>
          <span>{error}</span>
        </div>
      )}

      {status === "done" && result && (
        <section className="result">
          <div className="catalog-bar">
            <span className="catalog-bar__title">{result.filename}</span>
            <span className="catalog-bar__meta">
              {result.char_count.toLocaleString()} chars
            </span>
          </div>

          <div className="page-sheet">
            <span className="stamp">extracted</span>
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
