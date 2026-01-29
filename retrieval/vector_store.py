import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.config import Settings

class VectorStore:
    def __init__(self,persist_dir:str = "chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name="chunks")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def add_chunks(self,chunks):
        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        embeddings = self.model.encode(texts).tolist()
        self.collection.add(
            documents = texts,
            embeddings=embeddings,
            metadatas = metadatas,
            ids=ids
        )     
    def search(self,query,top_k=5):
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results
        