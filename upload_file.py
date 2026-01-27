import os
import sys
import shutil
import hashlib
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)

load_dotenv()


MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
UPLOAD_DIR = os.getenv("UPLOAD_DIR")


def compute_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path,"rb") as f:
        for chunk in iter(lambda: f.read(8192),b""):
            sha256.update(chunk)
    return sha256.hexdigest()



def main():
    if len(sys.argv)<2:
        print("Usage: python upload_file.py <file_path>")
        return
    
    input_file_path = sys.argv[1]
    if not os.path.exists(input_file_path):
        print(f"File {input_file_path} does not exist.")
        return
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(input_file_path)
    destination_path = os.path.join(UPLOAD_DIR,filename)   
    shutil.copy2(input_file_path, destination_path)
    file_hash = compute_file_hash(destination_path)
    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["documents"]
    logger.info("Connected to MongoDB.")
    doc = {
        "user_id": "user_123",
        "filename": filename,
        "file_path": destination_path,
        "file_hash": file_hash,
        "upload_timestamp": datetime.now(),
        "status": "uploaded",
        "metadata": {}
    }
    logger.info("Inserting document metadata into MongoDB.")
    result = collection.insert_one(doc)
    document_id = result.inserted_id
    jobs = db["processing_jobs"]
    jobs.insert_one({
        "document_id": document_id,
        "status": "queued",
        "created_at": datetime.now(),
        "error_message": None,
        "started_at": None,
        "completed_at": None
    })
    logger.info("Created processing job for document ID %s", document_id)
    print("Job created for processing.")
    print("Inserted document ID:", result.inserted_id)
    print("File's hash:", file_hash)
    # print(jobs.find_one({"document_id": document_id}))
if __name__ == "__main__":
    main()
    
    
