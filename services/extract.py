import pymupdf as fitz
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def extract_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(text_parts)


def extract_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def extract_from_epub(file_bytes: bytes) -> str:
    # ebooklib needs a file path, so write to a temp file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        book = epub.read_epub(tmp_path)
        text_parts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text_parts.append(soup.get_text(separator="\n"))
        return "\n".join(text_parts)
    finally:
        os.remove(tmp_path)


def _clean(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def extract_text(filename: str, file_bytes: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        raw = extract_from_pdf(file_bytes)
    elif ext == "txt":
        raw = extract_from_txt(file_bytes)
    elif ext == "epub":
        raw = extract_from_epub(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    return _clean(raw)
