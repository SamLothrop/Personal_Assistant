from src.document_loader import chroma_client, collection


def query_collection(query_text, n_results=3, content_type=None):
    where_clause = None
    if content_type:
        where_clause = {"content_type": content_type}
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances', 'uris'],
        where=where_clause
    )
    
    return results

def chat_with_documents():
    print("Commands:")
    print("  - '<query>' - search everything")
    print("  - 'text: <query>' - text only")
    print("  - 'images: <query>' - images only")
    print("  - 'help' - show this help")
    print("  - 'quit' - exit")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        elif user_input.lower() == 'help':
            print("\nAvailable commands:")
            print("  - Regular search: 'machine learning algorithms'")
            print("  - Text only: 'text: python programming'") 
            print("  - Images only: 'images: flowchart diagram'")

            continue
        
        content_type = None
        query_text = user_input
        
        if user_input.lower().startswith('text:'):
            content_type = 'text'
            query_text = user_input[5:].strip()
        elif user_input.lower().startswith('images:'):
            content_type = 'image'
            query_text = user_input[7:].strip()
        
        if not query_text:
            print("Please provide a search query.")
            continue

        results = query_collection(query_text, n_results=5, content_type=content_type)
        
        if not results['ids'][0]:
            print("No results found.")
            continue
        
        text_results = []
        image_results = []
        
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            if metadata.get('content_type') == 'text':
                text_results.append(i)
            else:
                image_results.append(i)
        
        print(f"\nFound {len(results['ids'][0])} results:")
        if text_results:
            print(f"{len(text_results)} text document(s)")
        if image_results:
            print(f"{len(image_results)} image(s)")
        
        if text_results:
            for i in text_results:
                display_text_result(results, i)

        if image_results:
            for i in image_results:
                display_image_result(results, i)

def display_text_result(results, index):
    metadata = results['metadatas'][0][index]
    doc_content = results['documents'][0][index] if results['documents'][0][index] else ""
    distance = results['distances'][0][index]
    
    print(f"\n{metadata.get('file_name', 'Unknown')}")
    print(f"     Segment {metadata.get('segment_number', 'N/A')}/{metadata.get('total_segments', 'N/A')}")
    print(f"     Relevance: {(1-distance):.3f}")
    print(f"     Preview: {doc_content[:150]}{'...' if len(doc_content) > 150 else ''}")

def display_image_result(results, index):
    metadata = results['metadatas'][0][index]
    distance = results['distances'][0][index]
    image_path = results['uris'][0][index] if results['uris'] and results['uris'][0][index] else "N/A"
    
    print(f"\n  {metadata.get('file_name', 'Unknown')}")
    print(f"     Relevance: {(1-distance):.3f}")
    print(f"     Path: {image_path}")
        
if __name__ == "__main__":
    chat_with_documents()