import os
import json

from app.parsing.parser import parse_pdf
from app.parsing.extract_images import extract_images_from_pdf


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(BASE_DIR, "data", "cleaned_pdfs")
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images")


os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)


def process_all_pdfs():

    pdf_files = [
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".pdf")
    ]

    for pdf_file in pdf_files:

        pdf_path = os.path.join(INPUT_DIR, pdf_file)

        print(f"\nProcessing: {pdf_file}")

        # -------------------------
        # Parse PDF
        # -------------------------

        documents = parse_pdf(pdf_path)

        combined_text = "\n\n".join(
            [doc.text for doc in documents]
        )

        parsed_output_path = os.path.join(
            PARSED_DIR,
            pdf_file.replace(".pdf", ".md")
        )

        with open(parsed_output_path, "w", encoding="utf-8") as f:
            f.write(combined_text)

        print(f"Saved markdown: {parsed_output_path}")

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


if __name__ == "__main__":
    process_all_pdfs()