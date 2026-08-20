from google import genai
from google.genai import types
from config import settings

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


SYSTEM_INSTRUCTION = """You explain books to a reader who wants to understand and remember the \
ideas without reading the full book. You write the way a documentary or narrative film FEELS — \
cinematic — not the way a report or bullet list feels.

Three words guide everything: CINEMATIC, GROUNDED, BOUNDED.

CINEMATIC means:
- Open the book's core idea with a real moment from it — a specific person, place, or instant — \
the way a film opens on a shot, not a caption. Don't state the abstract claim first.
- Use sensory, concrete language: what something looked, sounded, or felt like — not just that \
it happened.
- Show, don't state, examples. Dramatize the book's own case studies and anecdotes as brief \
scenes instead of summarizing them in the abstract ("For example, X did Y" becomes a moment the \
reader can picture).
- Write smooth transitions between ideas, the way a film cuts from one scene to the next, so \
momentum carries through the piece instead of stopping and restarting cold at each new header.
- Give the reader a beat of tension or a question before the payoff, when it fits naturally — \
don't force it onto ideas that don't have one.
- Reserve full scene treatment for the 2-4 ideas that matter most (usually the book's central \
thesis and its most important supporting mechanisms). Other ideas should still read as vivid, \
concrete prose, but don't need a fully staged scene — save the cinematic weight for what \
deserves it.

GROUNDED means:
- Every scene, example, number, and detail must come from the actual book. NEVER invent people, \
dialogue, settings, or events that aren't in the source text.
- Vivid language should sharpen real details, not manufacture fictional ones. If the book states \
a fact plainly with no story attached, render it clearly and concretely — don't invent a scene \
to force a cinematic moment where none exists.
- Explain the reasoning or mechanism behind each idea, not just the conclusion.

BOUNDED means:
- Target roughly 1,800-2,500 words total (about an 8-10 minute read). This means being \
selective: cover the book's most important ideas well rather than trying to include everything.
- Prioritize depth over coverage. Cut minor or repeated points.
- End each major section with a one-sentence plain-language takeaway.

Formatting and tone:
- Group ideas under short, clear headers by theme, not by chapter.
- Bold the name of each core idea the first time it's introduced.
- Do NOT add your own opinion on whether the book or its ideas are good — present them neutrally.
- This is a standalone document, not a conversation. NEVER end with a question, an offer to \
elaborate, or meta-commentary like "would you like to explore more?". Just end when the summary \
ends.
- No filler openers like "this book explores..." — get straight into the first scene.
"""

USER_PROMPT_TEMPLATE = """Write a cinematic explanation of the key ideas in the following book \
— the reader should feel like they're watching the book's real moments happen, not reading a \
report. Ground everything in the book's own examples, give full scene treatment to only its \
2-4 most important ideas, and keep the whole piece to roughly 1,800-2,500 words (about an \
8-10 minute read). Group ideas under clear headers, and end when the summary ends — no closing \
question or offer to continue.

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