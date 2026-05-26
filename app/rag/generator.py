"""
LLM answer generator using the OpenAI chat completions API.

Receives a user query and a retrieved context block, builds a strict RAG
prompt, and returns the model's answer as a plain string.
"""

from __future__ import annotations

from openai import OpenAI

from app.config import settings

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_SYSTEM_PROMPT = (
    "You are a precise and helpful assistant. "
    "Answer the user's question using ONLY the information provided in the context below. "
    "If the context does not contain enough information to answer, say so clearly in Persian. "
    "You MUST always respond exclusively in Persian (Farsi), regardless of the language of the question or context. "
    "Never use any language other than Persian in your response. "
    "Keep the answer concise, structured, and accurate."
)

_USER_TEMPLATE = """\
Context:
─────────────────────────────────
{context}
─────────────────────────────────

Question: {query}

Answer:"""


class Generator:
    def __init__(self) -> None:
        if settings.MOCK_LLM:
            self._client = None
            return
        base_url = settings.LLM_BASE_URL or _GEMINI_BASE_URL
        api_key = settings.OPENAI_API_KEY or "ollama"
        if not settings.LLM_BASE_URL and not settings.OPENAI_API_KEY:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add your Gemini API key or set LLM_BASE_URL for Ollama."
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, query: str, context: str) -> tuple[str, int]:
        """Return (answer, estimated_tokens) grounded in *context* for *query*."""
        if settings.MOCK_LLM:
            answer = f"[MOCK MODE] Retrieved context for '{query}':\n\n{context}"
            return answer, int(len(answer.split()) * 1.3)

        user_prompt = _USER_TEMPLATE.format(context=context, query=query)

        response = self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        answer = response.choices[0].message.content
        tokens = int(
            (len(query.split()) + len(context.split()) + len(answer.split())) * 1.3
        )
        return answer, tokens
