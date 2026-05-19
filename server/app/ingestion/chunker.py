import tiktoken


ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str):

    return len(
        ENCODING.encode(text)
    )


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap_tokens: int = 150,
):
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_tokens = count_tokens(para)

        if para_tokens > chunk_size:
            words = para.split()
            temp = []
            for word in words:
                temp.append(word)
                temp_text = " ".join(temp)
                if count_tokens(temp_text) >= chunk_size:
                    chunks.append(temp_text)
                    temp = []
            if temp:
                chunks.append(" ".join(temp))
            continue

        if current_tokens + para_tokens > chunk_size:
            chunk_text = "\n".join(current_chunk)
            chunks.append(chunk_text)

            encoded = ENCODING.encode(chunk_text)
            overlap_encoded = encoded[-overlap_tokens:]
            overlap_text = ENCODING.decode(overlap_encoded)

            current_chunk = [overlap_text, para]
            current_tokens = len(overlap_encoded) + para_tokens
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks