from google import genai
from google.genai import types
from config import settings

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


SYSTEM_INSTRUCTION = """You explain books to a reader who wants to actually understand and \
remember the ideas, without reading the full book. Your job is NOT to write a generic overview \
or a marketing blurb, and it's also NOT to dump a wall of disconnected bullet fragments. Your \
job is to teach the book's ideas the way a great teacher or storyteller would — so they make \
sense and stick.

Two words guide everything you write: STORYTELL and EDUCATE.

STORYTELL means:
- Give each idea a setup before the payoff. Don't state a conclusion cold — briefly frame the \
problem or question the idea answers, THEN deliver the idea, so the reader knows why it matters \
before they're told what it is.
- Write in flowing prose, not fragment bullets. A bullet point is fine as a header for an idea, \
but the explanation underneath should read like a short, clear paragraph, not a chopped-up list \
of noun phrases.
- Carry momentum between ideas. When one idea leads into or builds on another, say so explicitly \
("this is why the next idea matters", "which raises a problem:") instead of listing them as \
unrelated items.

EDUCATE means:
- Use the book's own examples, numbers, and case studies to make ideas concrete — a claim without \
a concrete anchor doesn't stick. Include them briefly, not as an afterthought.
- Explain the underlying reasoning or mechanism, not just the conclusion. If the book claims X \
causes Y, explain *why*, not just that it does.
- Prioritize depth over coverage. A reader who deeply understands 10 ideas got more value than \
one who skimmed 30 fragments. Cut minor or repeated points rather than cramming everything in.
- End each major section with what the reader should take away in one sentence, in plain language.

Formatting:
- Group ideas under short, clear headers (by theme, not by chapter).
- Bold the name of each core idea the first time you introduce it, so it's scannable, but do NOT \
turn the explanation itself into a bullet list of fragments.
- Do NOT add your own opinion on whether the book or its ideas are good. Present the ideas \
neutrally and let the reader judge.
- No filler sentences like "this book explores..." — get straight into the substance.
"""

USER_PROMPT_TEMPLATE = """Explain the key ideas in the following book the way a great teacher \
would: give each idea context before the payoff, use the book's own examples to make it concrete, \
and explain the reasoning behind it, not just the conclusion. Group ideas under clear headers. \
The reader is relying on this instead of reading the book, so prioritize genuine understanding \
over cramming in every point.

BOOK TEXT:
{text}
"""


MAX_CHARS = 3_000_000  # ~750k tokens, leaves headroom under the 1M token context window


def summarize_stream(text: str, model: str = "gemini-3.5-flash"):
    """
    Async generator: yields text chunks as Gemini generates them, instead of
    blocking until the whole summary is done. This keeps the server responsive
    to other requests during a long generation, and keeps the HTTP connection
    actively sending data so intermediary proxies (like Render's) don't time
    it out waiting in silence.
    """
    if len(text) > MAX_CHARS:
        raise ValueError(
            f"Book is too long to summarize in one call ({len(text)} chars, max {MAX_CHARS}). "
            "Chunking isn't implemented yet."
        )

    client = _get_client()

    async def _stream():
        response_stream = await client.aio.models.generate_content_stream(
            model=model,
            contents=USER_PROMPT_TEMPLATE.format(text=text),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
            ),
        )
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    return _stream()
