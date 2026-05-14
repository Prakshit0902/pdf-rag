from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from dotenv import load_dotenv

import os

load_dotenv()


parser = LlamaParse(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    result_type="markdown",
    verbose=True,
)


def parse_pdf(pdf_path: str):
    """
    Parse a PDF into structured markdown documents.
    """

    file_extractor = {
        ".pdf": parser
    }

    documents = SimpleDirectoryReader(
        input_files=[pdf_path],
        file_extractor=file_extractor
    ).load_data()

    return documents