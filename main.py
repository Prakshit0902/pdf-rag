from app.qa.ask import ask_question


def main():

    print("\nPDF RAG System Ready\n")

    while True:

        question = input("\nAsk Question: ")

        if question.lower() in ["exit", "quit"]:
            break

        result = ask_question(question)

        print("\n====================\n")

        print(result["answer"])

        print("\n====================\n")


if __name__ == "__main__":
    main()