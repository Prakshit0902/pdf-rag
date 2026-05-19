import fitz


class PDFType:
    SELECTABLE_TEXT = "selectable_text"
    SCANNED = "scanned"
    MIXED = "mixed"


def detect_pdf_type(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        text_pages = 0

        for page in doc:
            text = page.get_text().strip()
            if text:
                text_pages += 1

        doc.close()

        ratio = text_pages / max(total_pages, 1)

        if ratio > 0.7:
            return PDFType.SELECTABLE_TEXT
        elif ratio > 0.2:
            return PDFType.MIXED
        else:
            return PDFType.SCANNED

    except Exception:
        return PDFType.SCANNED
