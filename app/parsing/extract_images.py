import fitz
import os


def extract_images_from_pdf(pdf_path: str, output_dir: str):
    """
    Extract all embedded images from PDF.
    """

    os.makedirs(output_dir, exist_ok=True)

    pdf = fitz.open(pdf_path)

    image_paths = []

    for page_index in range(len(pdf)):

        page = pdf[page_index]

        images = page.get_images(full=True)

        for image_index, img in enumerate(images):

            xref = img[0]

            base_image = pdf.extract_image(xref)

            image_bytes = base_image["image"]

            image_ext = base_image["ext"]

            image_name = (
                f"page_{page_index+1}_img_{image_index+1}.{image_ext}"
            )

            image_path = os.path.join(
                output_dir,
                image_name
            )

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            image_paths.append(image_path)

    return image_paths