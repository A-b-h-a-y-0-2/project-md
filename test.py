from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

print("Chunks count:", db.chunks.count_documents({}))
print(db.chunks.find_one())
print(list(db.chunks.list_indexes()))

chunk = db.chunks.find_one()
print(chunk["chunk_text"][:200])
print(db.chunks.count_documents({}))
print(list(db.chunks.list_indexes()))
print(db.chunks.find_one())
