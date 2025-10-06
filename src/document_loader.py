from PyPDF2 import PdfReader
import os
import chromadb
import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import CHROMA_HOST, CHROMA_PORT
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.config import Settings

chroma_client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT,
    ssl=False,
    settings=Settings(),
)

collection = chroma_client.get_or_create_collection(
    name='multimodal_segments',
    embedding_function=OpenCLIPEmbeddingFunction(),
    data_loader=ImageLoader()
)

def load_file_documents_txt(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def load_file_documents_pdf(file_path):
    reader = PdfReader(file_path)
    number_of_pages = len(reader.pages)
    content = ''
    for page_number in range(number_of_pages):
        page = reader.pages[page_number]
        content += page.extract_text()
    return content

def segment_file_content(file_content, chunk_size, overlap):
    segmented_content = []
    start = 0
    while start < len(file_content):
        end = start + chunk_size
        segmented_content.append(file_content[start:end])
        start = end - overlap
    return segmented_content

def store_data(documents_data, image_paths):
    if documents_data:
        all_documents = []
        all_metadatas = []
        all_ids = []
        
        for file_name, segments in documents_data.items():
            for i, segment in enumerate(segments):
                all_documents.append(segment)
                all_metadatas.append({
                    'file_name': file_name,
                    'segment_number': i + 1,
                    'total_segments': len(segments),
                    'file_type': file_name.split('.')[-1] if '.' in file_name else 'unknown',
                    'content_type': 'text'
                })
                all_ids.append(f'text_{file_name}_seg_{i+1}')
        
        collection.add(
            documents=all_documents,
            metadatas=all_metadatas,
            ids=all_ids
        )
        print(f'Added {len(all_documents)} text segments to collection')
    
    if image_paths:
        image_ids = []
        image_metadatas = []
        
        for image_path in image_paths:
            file_name = os.path.basename(image_path)
            image_ids.append(f'img_{file_name}')
            image_metadatas.append({
                'file_name': file_name,
                'file_type': 'image',
                'content_type': 'image',
                'full_path': image_path
            })
        
        collection.add(
            ids=image_ids,
            uris=image_paths,
            metadatas=image_metadatas
        )
        print(f'Added {len(image_paths)} images to collection')
    
        
def main():
    file_paths = []
    documents_data = {}
    image_paths = []
    desktop = '../'

    for root, dirs, files in os.walk(desktop):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in {'.pdf', '.txt', '.jpeg', '.jpg'}:
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    for file_path in file_paths:
        file_name = Path(file_path).name
        if file_path.endswith('.pdf'):
            file_content = load_file_documents_pdf(file_path)
            file_name = Path(file_path).name
            segmented_content = segment_file_content(file_content, 500, 400)
            documents_data[file_name] = segmented_content
            print(f'Processed PDF: {file_name}')
            
        elif file_path.endswith('.txt'):
            file_content = load_file_documents_txt(file_path)
            segmented_content = segment_file_content(file_content, 500, 400)
            documents_data[file_name] = segmented_content
            print(f'Processed TXT: {file_name}')
            
        elif file_path.lower().endswith(('.jpg', '.jpeg')):
            image_paths.append(file_path)
            print(f'Found image: {file_name}')
            
    store_data(documents_data, image_paths)


if __name__ == "__main__":
    main()


