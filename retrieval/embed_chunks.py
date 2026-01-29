from pymongo import MongoClient
from vector_store import VectorStore
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

def main():
    client = MongoClient(MONGO_URI)
    database = client[DB_NAME]
    chunks = list(database.chunks.find({}))
    
    if not chunks:
        print("No chunks found in the database.")
        return

    vs = VectorStore()
    formatted_chunks = []
    for c in chunks:
        formatted_chunks.append({
            "id": str(c["_id"]),
            "text": c["chunk_text"],
            "metadata":{
                "document_id": str(c["document_id"]),
                "chunk_index": c["chunk_index"]
            }
        }) 
    vs.add_chunks(formatted_chunks)
    print(f"Embedded and added {len(formatted_chunks)} chunks to the vector store.")
    
if __name__ == "__main__":
    main()
   