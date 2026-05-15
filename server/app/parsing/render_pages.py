import os

from pdf2image import convert_from_path


def render_pdf_pages(
    pdf_path: str,
    output_dir: str
):

    os.makedirs(output_dir, exist_ok=True)

    pages = convert_from_path(
        pdf_path,
        dpi=200
    )

    page_map = {}

    for index, page in enumerate(pages):

        page_num = index + 1

        image_path = os.path.join(
            output_dir,
            f"page_{page_num}.png"
        )

        page.save(
            image_path,
            "PNG"
        )

        page_map[str(page_num)] = image_path

    return page_map