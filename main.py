import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from config import settings
from services.extract import extract_text
from services.gemini import summarize_stream, MAX_CHARS

app = FastAPI(title="Book Summarizer")


@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_loaded": bool(settings.gemini_api_key)}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = await run_in_threadpool(extract_text, file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from this file.")

    return {
        "filename": file.filename,
        "char_count": len(text),
        "preview": text[:500],
    }


@app.post("/summarize")
async def summarize_book(file: UploadFile = File(...)):
    file_bytes = await file.read()
    filename = file.filename

    try:
        text = await run_in_threadpool(extract_text, filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from this file.")

    if len(text) > MAX_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Book is too long to summarize in one call ({len(text)} chars, max {MAX_CHARS}).",
        )

    async def event_stream():
        # Sent first so the frontend can show filename/char_count immediately.
        yield json.dumps({"type": "meta", "filename": filename, "char_count": len(text)}) + "\n"
        try:
            async for piece in summarize_stream(text):
                yield json.dumps({"type": "chunk", "text": piece}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
        except Exception as e:
            # Headers are already sent by this point, so errors mid-stream
            # have to be signaled in-band rather than as an HTTP status code.
            yield json.dumps({"type": "error", "detail": f"Gemini API error: {e}"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


# Serve the built React frontend. Must be mounted last so it doesn't
# shadow the /health, /extract, /summarize routes above.
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
