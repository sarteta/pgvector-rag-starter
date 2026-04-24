"""Text chunking.

Naive sentence-boundary chunker with overlap. Good enough for docs under
~10k words. For long PDFs, swap in a proper chunker (e.g. semantic chunking
or LangChain's RecursiveCharacterTextSplitter).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    start: int
    end: int


_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])")


def split_sentences(text: str) -> list[str]:
    parts = _SENT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, *, target_chars: int = 600, overlap_chars: int = 80) -> list[Chunk]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    start = 0
    cursor = 0

    for sent in sentences:
        if buf and buf_len + len(sent) + 1 > target_chars:
            chunk_text_ = " ".join(buf)
            chunks.append(Chunk(text=chunk_text_, start=start, end=cursor))
            # Rebuild buffer with overlap from the end of the previous chunk
            if overlap_chars > 0 and len(chunk_text_) > overlap_chars:
                tail = chunk_text_[-overlap_chars:]
                buf = [tail]
                buf_len = len(tail)
                start = cursor - len(tail)
            else:
                buf = []
                buf_len = 0
                start = cursor
        buf.append(sent)
        buf_len += len(sent) + 1
        cursor += len(sent) + 1

    if buf:
        chunks.append(Chunk(text=" ".join(buf), start=start, end=cursor))

    return chunks
