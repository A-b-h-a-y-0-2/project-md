from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')
db = client["document_system"]
collection = db['documents']
doc = {
    "user_id": "user_456",
    "filename": "python_test.pdf",
    "file_path": "data/uploads/python_test.pdf",
    "file_hash": "hash_from_python_123",
    "upload_timestamp": datetime.now(),
    "status": "uploaded",
    "metadata": {
        "title": "Python Test Document",
        "author": "Abhay",
    }
}

result = collection.insert_one(doc)
print("Inserted ID: ", result.inserted_id)

fetched_doc = collection.find_one({"_id": result.inserted_id})
print("fetched from DB: ", fetched_doc)