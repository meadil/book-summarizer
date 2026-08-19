from google import genai
from google.genai import types
from config import settings

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


SYSTEM_INSTRUCTION = """You summarize books for a reader who wants to extract maximum value \
without reading the full book. Your job is NOT to write a generic overview or a marketing \
blurb — it's to squeeze out the actual, specific, usable ideas the book contains.

Rules:
- Extract every distinct idea, model, framework, or actionable insight the book presents.
- Be specific: include the book's own examples, numbers, and reasoning where they matter, \
not just the abstract claim.
- Skip filler: skip repeated anecdotes, restated points, and padding the author uses to hit \
a word count.
- Do NOT add your own opinion on whether the book or its ideas are good. Present the ideas \
neutrally and let the reader judge.
- Group related ideas together under short, clear headers.
- Write as dense, information-rich bullet points. No fluff sentences like "this book explores...".
"""

USER_PROMPT_TEMPLATE = """Summarize the following book. Extract all key ideas as bullet points, \
grouped under short headers by theme. Be comprehensive — the reader is relying on this instead \
of reading the book.

BOOK TEXT:
{text}
"""


MAX_CHARS = 3_000_000  # ~750k tokens, leaves headroom under the 1M token context window


def summarize(text: str, model: str = "gemini-3.5-flash") -> str:
    if len(text) > MAX_CHARS:
        raise ValueError(
            f"Book is too long to summarize in one call ({len(text)} chars, max {MAX_CHARS}). "
            "Chunking isn't implemented yet."
        )

    client = _get_client()

    response = client.models.generate_content(
        model=model,
        contents=USER_PROMPT_TEMPLATE.format(text=text),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
        ),
    )

    return response.text
