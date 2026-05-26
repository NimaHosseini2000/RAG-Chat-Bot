"""Chat router — POST /chat"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_conn
from app.dependencies import get_generator, get_retriever
from app.rag.generator import Generator
from app.rag.retriever import Retriever
from app.schemas import ChatRequest, ChatResponse
from app.session_store import add_tokens, append_message

router = APIRouter(tags=["Chat"])

_NO_CONTEXT_MSG = "اطلاعات کافی در پایگاه دانش برای پاسخ به سوال شما یافت نشد."
_TOKEN_LIMIT_MSG = "محدودیت توکن به پایان رسیده است. لطفاً با مدیر سیستم تماس بگیرید."


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    retriever: Retriever = Depends(get_retriever),
    generator: Generator = Depends(get_generator),
) -> ChatResponse:
    # Check token budget before calling the LLM
    with get_conn() as conn:
        admin = conn.execute(
            "SELECT token_limit, tokens_used FROM admins WHERE id = 1"
        ).fetchone()
    if admin and admin["tokens_used"] >= admin["token_limit"]:
        return ChatResponse(answer=_TOKEN_LIMIT_MSG, sources=[], urls=[], tokens_used=0)

    try:
        context, sources, urls = retriever.retrieve(request.query, top_k=request.top_k)

        if not context.strip():
            if request.session_id:
                append_message(request.session_id, "user", request.query)
                append_message(request.session_id, "bot", _NO_CONTEXT_MSG)
            return ChatResponse(answer=_NO_CONTEXT_MSG, sources=[], urls=[], tokens_used=0)

        answer, tokens = generator.generate(request.query, context)

        if request.session_id:
            append_message(request.session_id, "user", request.query)
            append_message(request.session_id, "bot", answer, sources=sources, urls=urls)
            add_tokens(request.session_id, tokens)
            with get_conn() as conn:
                conn.execute(
                    "UPDATE admins SET tokens_used = tokens_used + ? WHERE id = 1",
                    (tokens,),
                )
                conn.execute(
                    "UPDATE sessions SET tokens_used = tokens_used + ? WHERE id = ?",
                    (tokens, request.session_id),
                )

        return ChatResponse(answer=answer, sources=sources, urls=urls, tokens_used=tokens)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
