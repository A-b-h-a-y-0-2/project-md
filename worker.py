from pymongo import MongoClient
from pypdf import PdfReader
from datetime import datetime   
import traceback
from dotenv import load_dotenv
import os
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
CHUNK_SIZE = 750

def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    jobs = db["processing_jobs"]
    documents = db['documents']
    job = jobs.find_one({"status":"queued"})
    if not job:
        print("No queued jobs found.")
        return

    print("Processing job:", job["_id"])
    
    jobs.update_one({"_id": job["_id"]}, {"$set":{"status":"processing","started_at": datetime.now()}})   
    
    try:
        doc = documents.find_one({"_id": job["document_id"]})
        process_document(doc, db)
        
        jobs.update_one(
            {"_id": job["_id"]},
            {"$set":{"status":"complete","completed_at": datetime.now()}}
        )
        print("Job completed successfully.")
    except Exception as e:
        error_msg = str(e) + "\n" + traceback.format_exc()
        jobs.update_one(
            {"_id": job["_id"]},
            {"$set":{"status":"failed","error_message": error_msg, "completed_at": datetime.now()}}
        )
        print("Job failed with error:", error_msg)
        
        

def process_document(doc, db):
    documents = db["documents"]
    chunks_collection = db['chunks']
    reader = PdfReader(doc["file_path"])
    
    full_txt = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        full_txt += text + "\n"
    chunks = chunk_text(full_txt)
    for chunk_index,chunk_text_val, char_start,char_end in chunks:
        chunk_doc = {
            "document_id": doc["_id"],
            "chunk_text": chunk_text_val,
            "chunk_index": chunk_index,
            "page_numbers": [],  # optional improvement later
            "char_start": char_start,
            "char_end": char_end,
            "created_at": datetime.now(),
            "metadata": {}
        }
        chunks_collection.insert_one(chunk_doc)

    documents.update_one(
        {"_id": doc["_id"]},
        {"$set":{"status":"complete"}}
    )
    
    print(f"Inserted {len(chunks)} chunks for document ID {doc['_id']}")

def chunk_text(text, size = CHUNK_SIZE):
    chunks = []
    start = 0
    index = 0
    
    while start<len(text):
        chunk = text[start: start+size]
        chunks.append((index,chunk, start,start + len(chunk)))
        start += len(chunk)
        index += 1

    return chunks

if __name__ == "__main__":
    main()