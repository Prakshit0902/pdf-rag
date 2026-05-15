import os
import json
import uuid

from app.parsing.parser import parse_pdf
from app.parsing.extract_images import extract_images_from_pdf
from app.ingestion.chunker import split_text_into_chunks
from app.ingestion.chunker import count_tokens
from app.parsing.render_pages import render_pdf_pages

INPUT_DIR = "data/cleaned_pdfs"
PARSED_DIR = "data/parsed"
IMAGE_DIR = "data/images"
PAGE_RENDER_DIR = "data/page_renders"

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

        semantic_chunks = split_text_into_chunks(
            text
        )

        total_chunks = len(semantic_chunks)

        # Use document index + 1 as page number since docs are already page-split
        doc_page = str(doc_idx + 1)

        for semantic_chunk in semantic_chunks:
            if len(semantic_chunk.split()) < 30:
                continue

            # Try to get page from document metadata, fallback to doc index
            page = doc.metadata.get(
                "page_label",
                doc.metadata.get("page", doc_page)
            )

            if not page:
                page = doc_page

            chunk = {
                "id": str(uuid.uuid4()),

                "source_file": pdf_filename,

                "chunk_index": chunk_index,

                "text": semantic_chunk,

                "page": page,

                "images": image_map.get(str(page), []) if page else [],

                "page_render": page_render_map.get(str(page)) if page else None,

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