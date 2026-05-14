import os
import json
import uuid

from app.parsing.parser import parse_pdf
from app.parsing.extract_images import extract_images_from_pdf
from app.ingestion.chunker import split_text_into_chunks
from app.ingestion.chunker import count_tokens

INPUT_DIR = "data/cleaned_pdfs"
PARSED_DIR = "data/parsed"
IMAGE_DIR = "data/images"

os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)


def build_chunks(
    documents,
    pdf_filename,
    image_paths
):

    chunks = []

    chunk_index = 0

    for doc in documents:

        text = doc.text

        semantic_chunks = split_text_into_chunks(
            text
        )

        for semantic_chunk in semantic_chunks:
            if len(semantic_chunk.split()) < 30:
                continue

            chunk = {
                "id": str(uuid.uuid4()),

                "source_file": pdf_filename,

                "chunk_index": chunk_index,

                "text": semantic_chunk,

                "page": doc.metadata.get(
                    "page_label",
                    None
                ),

                "images": image_paths,

                "metadata": doc.metadata,
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

        image_paths = extract_images_from_pdf(
            pdf_path,
            pdf_image_dir
        )

        print(f"Extracted {len(image_paths)} images")

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
            image_paths
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