import os
import json
import uuid

from app.parsing.parser import parse_pdf
from app.parsing.extract_images import extract_images_from_pdf
from app.ingestion.chunker import split_text_into_chunks
from app.ingestion.chunker import count_tokens
from app.parsing.render_pages import render_pdf_pages

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(BASE_DIR, "data", "cleaned_pdfs")
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images")
PAGE_RENDER_DIR = os.path.join(BASE_DIR, "data", "page_renders")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(PAGE_RENDER_DIR, exist_ok=True)


def build_chunks(
    documents,
    pdf_filename,
    image_map,
    page_render_map
):

    chunks = []

    chunk_index = 0

    for doc_idx, doc in enumerate(documents):
        text = doc.text
        semantic_chunks = split_text_into_chunks(text)

        # Use document index + 1 as page number since docs are already page-split
        doc_page = str(doc_idx + 1)

        # Try to get page from document metadata, fallback to doc index
        page = doc.metadata.get(
            "page_label",
            doc.metadata.get("page", doc_page)
        )
        if not page:
            page = doc_page

        page_images = image_map.get(str(page), [])
        page_render = page_render_map.get(str(page))
        has_visuals = bool(page_images) or bool(page_render)

        # If no text was extracted but visual assets exist, create a synthetic chunk
        # so this page is not entirely skipped during indexing.
        if not semantic_chunks and has_visuals:
            synthetic_text = f"Scanned page / image on page {page} of {pdf_filename}."
            semantic_chunks = [synthetic_text]

        total_chunks = len(semantic_chunks)

        for semantic_chunk in semantic_chunks:
            # Skip empty chunks
            cleaned_text = "".join(c for c in semantic_chunk if c.isalnum()).strip()
            if not cleaned_text:
                continue

            word_count = len(semantic_chunk.split())
            # Relax the chunk filtering: keep short chunks if they have visual elements,
            # otherwise filter out chunks with fewer than 5 words to reduce noise.
            if word_count < 5:
                if not has_visuals:
                    continue

            chunk = {
                "id": str(uuid.uuid4()),
                "source_file": pdf_filename,
                "chunk_index": chunk_index,
                "text": semantic_chunk,
                "page": page,
                "images": page_images,
                "page_render": page_render,
                "metadata": doc.metadata,
                "parent_doc_id": pdf_filename,
                "parent_chunk_index": chunk_index,
                "total_parent_chunks": total_chunks,
            }

            chunks.append(chunk)
            chunk_index += 1

            print(
                "TOKENS:",
                count_tokens(semantic_chunk)
            )

    return chunks


def process_all_pdfs():

    pdf_files = [
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".pdf")
    ]

    for pdf_file in pdf_files:

        print(f"\nProcessing: {pdf_file}")

        pdf_path = os.path.join(INPUT_DIR, pdf_file)

        # -------------------------
        # Extract Images
        # -------------------------

        pdf_image_dir = os.path.join(
            IMAGE_DIR,
            pdf_file.replace(".pdf", "")
        )

        image_map = extract_images_from_pdf(
            pdf_path,
            pdf_image_dir
        )

        total_images = sum(
            len(v)
            for v in image_map.values()
        )

        print(f"Extracted {total_images} images")
        
        pdf_render_dir = os.path.join(
            PAGE_RENDER_DIR,
            pdf_file.replace(".pdf", "")
        )
        
        page_render_map = render_pdf_pages(
            pdf_path,
            pdf_render_dir
        )
        
        print(f"Rendered {len(page_render_map)} pages into images") 

        # -------------------------
        # Parse PDF
        # -------------------------

        documents = parse_pdf(pdf_path)

        print(f"Parsed {len(documents)} document blocks")

        # -------------------------
        # Build Structured Chunks
        # -------------------------

        chunks = build_chunks(
            documents,
            pdf_file,
            image_map,
            page_render_map
        )

        # -------------------------
        # Save JSON
        # -------------------------

        output_path = os.path.join(
            PARSED_DIR,
            pdf_file.replace(".pdf", ".json")
        )

        with open(output_path, "w", encoding="utf-8") as f:

            json.dump(
                chunks,
                f,
                ensure_ascii=False,
                indent=2
            )

        print(f"Saved: {output_path}")


if __name__ == "__main__":
    process_all_pdfs()