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
import re
from PyPDF2.errors import PdfReadError

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


# Your existing functions
def load_file_documents_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading TXT file {file_path}: {e}")
        return ""

def load_file_documents_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content += text
        return content
    except PdfReadError:
        print(f"Skipping unreadable PDF: {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def segment_file_content(file_content, chunk_size=1000, overlap=200):

    file_content = ' '.join(file_content.split())
    
    sentences = re.split(r'(?<=[.!?])\s+', file_content)
    
    segmented_content = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > chunk_size and current_chunk:
            segmented_content.append(current_chunk.strip())
            
            if len(current_chunk) > overlap:
                overlap_start = len(current_chunk) - overlap
                overlap_text = current_chunk[overlap_start:]
                sentence_start = overlap_text.find('. ')
                if sentence_start != -1:
                    overlap_text = overlap_text[sentence_start + 2:]
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    if current_chunk.strip():
        segmented_content.append(current_chunk.strip())
    
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

    targets = [
    os.path.join("OneDrive", "Desktop"),
    os.path.join("OneDrive", "Documents"),
    "Downloads"
]

    home_dir = os.path.expanduser("~")

    for folder in targets:
        target_path = os.path.join(home_dir, folder)
        if os.path.exists(target_path):
            try:
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        _, ext = os.path.splitext(file)
                        if ext.lower() in {'.pdf', '.txt', '.jpeg', '.jpg'}:
                            full_path = os.path.join(root, file)
                            file_paths.append(full_path)
            except PermissionError:
                print(f"Skipping {target_path} — permission denied.")
                
    for file_path in file_paths:
        file_name = Path(file_path).name
        if file_path.endswith('.pdf'):
            file_content = load_file_documents_pdf(file_path)
            file_name = Path(file_path).name
            segmented_content = segment_file_content(file_content, 500, 400)
            documents_data[file_name] = segmented_content
            print(f'Processed PDF: {file_path}')
            
        elif file_path.endswith('.txt'):
            file_content = load_file_documents_txt(file_path)
            segmented_content = segment_file_content(file_content, 500, 400)
            documents_data[file_name] = segmented_content
            print(f'Processed TXT: {file_path}')
            
        elif file_path.lower().endswith(('.jpg', '.jpeg')):
            image_paths.append(file_path)
            print(f'Found image: {file_path}')
            
    store_data(documents_data, image_paths)


if __name__ == "__main__":
    main()


