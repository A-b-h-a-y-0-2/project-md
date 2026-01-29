from vector_store import VectorStore

def main():
    vs = VectorStore()
    while True:
        query = input("Enter your search query :").strip()
        if not query:
            break
        results = vs.search(query, top_k=2)
        print("Top results:")
        for doc, meta in zip(results["documents"][0],results["metadatas"][0]):
            print(f"[Doc{meta["document_id"]} - Chunk {meta["chunk_index"]}]: {doc}\n")
            print(doc[:300])
            print("-" *50)

if __name__ == "__main__":
    main()