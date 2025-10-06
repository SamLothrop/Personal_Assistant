import requests
from src.document_loader import main as load_documents
from src.search import chat_with_documents

def check_chroma_server():
    try:
        response = requests.get("http://localhost:8000/api/v2/heartbeat", timeout=3)
        if response.status_code == 200:
            print("Chroma server is running.")
            return True
        else:
            print("Chroma server may not be healthy.")
    except Exception:
        print("Could not connect to Chroma server at localhost:8000")
    return False


def main():
    print("Starting Personal Assistant\n")

    if not check_chroma_server():
        print("Chroma not up")
        return

    print("\nLoading documents...\n")
    load_documents()

    print("\nChat mode started (type 'quit' to exit):\n")
    chat_with_documents()


if __name__ == "__main__":
    main()
