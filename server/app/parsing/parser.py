import os

import fitz
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from dotenv import load_dotenv

from app.parsing.detector import detect_pdf_type, PDFType
from app.parsing.pymupdf_parser import parse_with_pymupdf

load_dotenv()

RESULT_TYPE = "text"


def has_selectable_text(pdf_path: str) -> bool:
    try:
        doc = fitz.open(pdf_path)
        text_found = any(page.get_text().strip() for page in doc)
        doc.close()
        return text_found
    except Exception:
        return False


def _llama_parse(pdf_path: str):
    disable_ocr = has_selectable_text(pdf_path)

    parser = LlamaParse(
        api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
        result_type=RESULT_TYPE,
        disable_ocr=disable_ocr,
        verbose=True,
    )

    file_extractor = {".pdf": parser}
    documents = SimpleDirectoryReader(
        input_files=[pdf_path],
        file_extractor=file_extractor,
    ).load_data()

    return documents


def parse_pdf(pdf_path: str):
    pdf_type = detect_pdf_type(pdf_path)
    basename = os.path.basename(pdf_path)

    if pdf_type == PDFType.SELECTABLE_TEXT:
        print(f"[{basename}] Selectable text -> PyMuPDF (fast)")
        result = parse_with_pymupdf(pdf_path)
        print(f"[{basename}] PyMuPDF extracted {len(result)} pages")
        return result

    print(f"[{basename}] {pdf_type} -> LlamaParse")
    result = _llama_parse(pdf_path)
    print(f"[{basename}] LlamaParse returned {len(result)} docs")
    return result