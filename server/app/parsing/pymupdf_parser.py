import fitz
from llama_index.core import Document


def parse_with_pymupdf(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            pages.append(Document(
                text=text,
                metadata={
                    "page": str(page_num),
                    "page_label": str(page_num),
                    "file_path": pdf_path,
                    "source": "pymupdf",
                }
            ))
    doc.close()
    return pages
