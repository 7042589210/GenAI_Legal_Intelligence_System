import os
import sys

# Ensure backend directory is in the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.ingestion import extract_text_from_file
from backend.clause_analysis import parse_clauses_and_metadata
from backend.vectorstore import build_and_save_vector_store

def ingest_knowledge_base():
    kb_dir = os.path.join(project_root, "knowledge_base")
    print(f"Ingesting knowledge base from directory: {kb_dir}")
    
    all_chunks = []
    
    for filename in os.listdir(kb_dir):
        if filename.endswith(".txt"):
            kb_path = os.path.join(kb_dir, filename)
            print(f"Reading: {filename}")
            
            # 1. Read text
            raw_text = extract_text_from_file(kb_path)
            
            # 2. Extract clauses and chunk
            pages_data = [{"text": raw_text, "page": 1}]
            chunks = parse_clauses_and_metadata(pages_data, filename)
            all_chunks.extend(chunks)
    
    # 3. Add to vector store
    print(f"Found {len(all_chunks)} knowledge base items. Saving to Chroma...")
    if all_chunks:
        build_and_save_vector_store(all_chunks)
        print("Knowledge base successfully ingested into Vector DB!")
    else:
        print("No chunks found to ingest.")

if __name__ == "__main__":
    ingest_knowledge_base()
