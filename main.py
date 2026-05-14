from app.qa.ask import ask_question


def main():

    print("\nPDF RAG System Ready\n")

    while True:

        question = input("\nAsk Question: ")

        if question.lower() in ["exit", "quit"]:
            break

        result = ask_question(question)

        print("\n====================\n")
        print(
            f"\nRewritten Query: "
            f"{result['rewritten_question']}"
        )
        print(result["answer"])

        print("\n\n========== SOURCES ==========\n")

        for chunk in result["retrieved_chunks"]:

            print(
                f"""
        CHUNK: {chunk["chunk_id"]}

        FILE: {chunk["source_file"]}

        PAGE: {chunk["page"]}

        VECTOR: {chunk["vector_score"]}

        BM25: {chunk["bm25_score"]}

        RERANK: {chunk["rerank_score"]}

        PREVIEW:
        {chunk["preview"]}

        ----------------------------
        """
            )

        print("\n====================\n")


if __name__ == "__main__":
    main()