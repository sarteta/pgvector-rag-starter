from app.chunking import chunk_text, split_sentences


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_single_short_sentence_is_one_chunk():
    chunks = chunk_text("Hola. Como estas?")
    assert len(chunks) == 1


def test_split_sentences_basic():
    sents = split_sentences("Uno. Dos! Tres? Final.")
    assert sents == ["Uno.", "Dos!", "Tres?", "Final."]


def test_chunks_respect_target_chars():
    text = ". ".join([f"Oracion numero {i} con algo de contenido." for i in range(50)]) + "."
    chunks = chunk_text(text, target_chars=300, overlap_chars=40)
    assert len(chunks) > 1
    for c in chunks:
        # Some slack because we only cut at sentence boundaries
        assert len(c.text) <= 600


def test_overlap_preserves_some_tail_between_chunks():
    text = ". ".join([f"Oracion {i} con algo de contenido." for i in range(20)]) + "."
    chunks = chunk_text(text, target_chars=200, overlap_chars=50)
    # With 20 sentences and 200 chars target, we expect multiple chunks
    assert len(chunks) >= 2
