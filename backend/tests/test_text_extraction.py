import io

from app.services.text_extraction import extract_text


def _make_pdf_bytes(text: str) -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    import docx

    document = docx.Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def test_extract_text_from_pdf():
    data = _make_pdf_bytes("Cold Room Cleaning SOP - sanitizer weekly")
    text = extract_text(data, "application/pdf", "sop.pdf")
    assert text is not None
    assert "sanitizer" in text.lower()


def test_extract_text_from_docx():
    data = _make_docx_bytes(["Allergen Control Policy", "Covers peanut and tree nut handling."])
    text = extract_text(
        data,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "policy.docx",
    )
    assert text is not None
    assert "peanut" in text.lower()


def test_extract_text_from_plain_text_by_extension():
    text = extract_text(b"Wash hands before handling raw poultry.", None, "notes.txt")
    assert text == "Wash hands before handling raw poultry."


def test_extract_text_unsupported_type_returns_none():
    text = extract_text(b"\x89PNG\r\n\x1a\n...", "image/png", "photo.png")
    assert text is None


def test_extract_text_corrupt_pdf_returns_none_not_raises():
    text = extract_text(b"not actually a pdf", "application/pdf", "bad.pdf")
    assert text is None


def test_extract_text_truncates_long_content():
    from app.services.text_extraction import MAX_EXTRACTED_CHARS

    huge = "a" * (MAX_EXTRACTED_CHARS + 1000)
    text = extract_text(huge.encode(), None, "big.txt")
    assert text is not None
    assert len(text) == MAX_EXTRACTED_CHARS
