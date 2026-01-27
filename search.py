from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

def main():
    client  = MongoClient(MONGO_URI)
    try:
        client.admin.command('ping')
        print("Connected to MongoDB successfully.")
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
        return
    db = client[DB_NAME]
    # db['chunks'].create_index([("chunk_text", "text")])

    chunks = db['chunks']
    documents = db['documents']
    
    query = input("Enter the search query: ").strip()
    
    if not query:
        print("Empty query. Exiting.")
        return
    
    results = chunks.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}, "chunk_text": 1, "document_id": 1}
    ).sort([("score", {"$meta": "textScore"})]).limit(10)
    
    print("\nTop matching chunks:\n")
    
    for r in results:
        doc = documents.find_one({"_id": r["document_id"]})

        if not doc:
            print("⚠️ Orphan chunk found (no parent document)")
            continue

        print(f"Document: {doc['filename']} (ID: {doc['_id']})")
        print(f"Score: {r['score']:.2f}")
        print(f"Chunk Text:\n{r['chunk_text']}\n")
        print("-" * 80)
        
if __name__ == "__main__":
    main()