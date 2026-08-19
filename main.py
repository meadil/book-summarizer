from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from config import settings
from services.extract import extract_text
from services.gemini import summarize

app = FastAPI(title="Book Summarizer")


@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_loaded": bool(settings.gemini_api_key)}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_text(file.filename, file_bytes)
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

    try:
        text = extract_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from this file.")

    try:
        summary = summarize(text)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e}")

    return {
        "filename": file.filename,
        "char_count": len(text),
        "summary": summary,
    }


# Serve the built React frontend. Must be mounted last so it doesn't
# shadow the /health, /extract, /summarize routes above.
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
