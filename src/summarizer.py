"""Text summarization module using LLM API."""

from openai import OpenAI

# Approximate max tokens for context (leave room for prompt)
MAX_CHUNK_CHARS = 12000

SYSTEM_PROMPT = """You are a professional assistant that creates concise, well-structured summaries of video transcripts.
Your summaries should:
1. Capture the main topics and key points
2. Preserve important details, arguments, and conclusions
3. Be well-organized with clear structure
4. Be written in Chinese only, within 500 characters
5. Include section headings if the content covers multiple topics"""

SUMMARY_PROMPT = """Please provide a comprehensive summary of the following video transcript.
Include:
- Main topic/theme
- Key points and arguments
- Important details or examples
- Conclusions or takeaways

Transcript:
{text}"""

MERGE_PROMPT = """The following are summaries of different parts of a long video.
Please merge them into a single coherent summary that captures all key points without redundancy.

Part summaries:
{summaries}"""


def summarize_text(transcript: str, config: dict) -> str:
    """Summarize a transcript using LLM API.

    Args:
        transcript: The transcript text to summarize.
        config: LLM API configuration.

    Returns:
        Summary text.
    """
    llm_config = config.get("llm", {})
    base_url = llm_config.get("base_url", "https://api.openai.com/v1")
    api_key = llm_config.get("api_key", "")
    model = llm_config.get("model", "gpt-4o")

    if not api_key:
        raise ValueError("LLM API key not configured. Please set it in config.yaml.")

    client = OpenAI(base_url=base_url, api_key=api_key)

    # If transcript is short enough, summarize directly
    if len(transcript) <= MAX_CHUNK_CHARS:
        print("[Summary] Generating summary...")
        return _call_llm(client, model, SUMMARY_PROMPT.format(text=transcript))

    # For long transcripts, split and summarize in parts
    print("[Summary] Transcript is long, summarizing in parts...")
    chunks = _split_text(transcript, MAX_CHUNK_CHARS)
    print(f"[Summary] Split into {len(chunks)} parts")

    part_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"[Summary] Summarizing part {i + 1}/{len(chunks)}...")
        summary = _call_llm(client, model, SUMMARY_PROMPT.format(text=chunk))
        part_summaries.append(summary)

    # Merge partial summaries
    print("[Summary] Merging partial summaries...")
    merged = "\n\n---\n\n".join(
        f"Part {i+1}:\n{s}" for i, s in enumerate(part_summaries)
    )
    final_summary = _call_llm(client, model, MERGE_PROMPT.format(summaries=merged))

    print("[Summary] Done.")
    return final_summary


def _call_llm(client: OpenAI, model: str, user_prompt: str) -> str:
    """Call LLM API with given prompt."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def _split_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks, preferring to break at paragraph boundaries."""
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n" + para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]
