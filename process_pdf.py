from pymongo import MongoClient
from pypdf import PdfReader
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

CHUNK_SIZE = 750

def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    documents = db['documents']
    chunks_collection = db['chunks']
    
    doc = documents.find_one({"status":"uploaded"})
    
    if not doc:
        print("No uploaded documents found.")
        return
    
    print("Processing document:", doc['filename'])
    
    reader = PdfReader(doc["file_path"])
    
    full_txt = ""
    page_map = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        full_txt += text + "\n"
        page_map.extend([i+1] *len(text))
        
    chunks = chunk_text(full_txt)
    
    for chunk_index,chunk_text_val, char_start,char_end in chunks:
        chunk_doc = {
            "document_id": doc["_id"],
            "chunk_text": chunk_text_val,
            "chunk_index": chunk_index,
            "page_numbers": [],  # optional improvement later
            "char_start": char_start,
            "char_end": char_end,
            "metadata": {}
        }

        chunks_collection.insert_one(chunk_doc)

    documents.update_one(
        {"_id": doc["_id"]},
        {"$set":{"status":"complete"}}
    )
    print(f"Inserted {len(chunks)} chunks for document ID {doc['_id']}")
    print("Processing complete.")

def chunk_text(text, size = 800):
    chunks = []
    start = 0
    index = 0
    
    while start <len(text):
        chunk = text[start:start+size]
        chunks.append((index,chunk, start, start+len(chunk)))
        start += size
        index+=1
        
    return chunks


if __name__ == "__main__":
    main()