# Book Summarizer

**Don't read every book. Let AI read it first.**

Upload a book and get back a summary in seconds, not an hour of skimming. Decide
if it's worth your time before you commit to it.

---

## The problem

There's more to read than time to read it. The usual fix — skim — doesn't work
well, because skimming tells you what a book is *about* but not whether it's
*useful* to you.

This reads the whole thing and tells you what matters.

---

## How it works

```
  upload a file (PDF, EPUB, TXT, MD)
            ↓
    pull the text out
            ↓
    stream the summary to the browser, piece by piece
            ↓
  you read it while it's still generating
```

The summary appears as it's written rather than after a long pause — the wait
feels like watching something work.

---

## Running it

You need Python 3.10+ and a free Gemini API key ([get one
here](https://aistudio.google.com/apikey)).

```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

```bash
cp .env.example .env
# then put your key in .env
```

### Backend

```bash
uvicorn main:app --reload
```

It runs on http://localhost:8000. Check it's alive at `/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend on http://localhost:5173, pointing at the backend.

---

## How it's deployed

Docker, deployed to Render's free tier. `render.yaml` is already set up, and
`/health` is wired as the health check — so deploys are automatic and free.

```bash
docker-compose up
```

---

## Things worth knowing

**There's a size limit.** Books longer than the Gemini context window get
rejected with a clear message rather than failing halfway through. Better to know
up front.

**Errors during streaming are reported inline.** Once the response has started,
an HTTP error code isn't possible — so failures show up in the stream itself
rather than as a blank page.

**Extraction failure is reported honestly.** If a file yields no text, you get a
"no text could be extracted" error, not an empty summary.

---

## How it's built

**Backend:** Python, FastAPI, `pymupdf` for PDFs, Google Gemini for the summary
**Frontend:** React, Vite
**Streaming:** newline-delimited JSON, so text arrives as it's generated
**Hosting:** Docker on Render

---

## Layout

```
main.py            the API — /health, /extract, /summarize
config.py          settings, reads .env
services/
├── extract.py     PDF/EPUB/text extraction
└── gemini.py      the streaming summary call
frontend/          the React app
Dockerfile         container build
render.yaml        Render deployment config
```

---

Status: working. Upload, summarise, read.