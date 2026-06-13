"""OCR ingestion slice — digital-first extraction with a graceful OCR fallback.

These tests never require the optional OCR backend (Tesseract); they assert the digital path works
and that a scanned/garbage file degrades gracefully instead of crashing the pipeline.
"""
import glob

from bid_package_agent.config import load_config
from bid_package_agent.ocr import ocr_available, extract_document_text


def test_ocr_available_returns_bool_without_raising():
    assert isinstance(ocr_available(), bool)


def test_digital_pdf_extracts_without_ocr():
    cfg = load_config()
    pdfs = glob.glob(str(cfg.reference_dir / "*.pdf"))
    assert pdfs, "expected at least one digital PDF in the Reference-Library"
    text, method = extract_document_text(pdfs[0])
    assert method == "digital" and len(text) > 40


def test_digital_docx_uses_digital_path():
    cfg = load_config()
    docs = glob.glob(str(cfg.exemplars_dir / "*.docx"))
    assert docs
    text, method = extract_document_text(docs[0])
    assert method == "digital" and text


def test_scanned_or_garbage_image_degrades_gracefully(tmp_path):
    fake = tmp_path / "scan.png"
    fake.write_bytes(b"not a real image")           # not valid image bytes
    text, method = extract_document_text(fake)        # must NOT raise
    assert method in {"ocr", "ocr-unavailable", "empty"}


def test_ocr_branch_runs_when_a_backend_is_present(monkeypatch, tmp_path):
    """Prove the image-only -> OCR routing: with a backend available, an image with no digital
    text layer is sent to OCR and its text comes back tagged 'ocr'. (Stubs the backend so the
    test needs no Tesseract binary; the digital path is proven separately on a real PDF.)"""
    import bid_package_agent.ocr as ocr
    img = tmp_path / "scanned-bid.png"
    img.write_bytes(b"\x89PNG\r\n")                  # content irrelevant — the OCR call is stubbed
    monkeypatch.setattr(ocr, "ocr_available", lambda: True)
    monkeypatch.setattr(ocr, "_ocr_text", lambda p: "OCR-EXTRACTED scope text from a scanned bid")
    text, method = ocr.extract_document_text(img)
    assert method == "ocr" and "OCR-EXTRACTED" in text
