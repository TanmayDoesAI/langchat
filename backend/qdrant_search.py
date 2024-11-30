# qdrant_search.py

from typing import List, Dict
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from qdrant_client import QdrantClient

class QdrantSearch:
    def __init__(self, qdrant_url: str, api_key: str, embeddings):
        self.embeddings=embeddings
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=api_key,
        )

    def query_qdrant(self, query: str, collection_name: str, limit: int = 5) -> List:
        """Retrieve relevant documents from Qdrant."""
        query_vector = self.embeddings.get_embeddings(query)
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return results

    def query_multiple_collections(self, query: str, collection_names: List[str], limit: int = 5) -> List[Dict]:
        """Query multiple Qdrant collections and return combined top results."""
        all_results = []
        
        for collection_name in collection_names:
            results = self.query_qdrant(query, collection_name, limit)
            for result in results:
                all_results.append({
                    'text': result.payload['text'],
                    'source': result.payload['source'],
                    'score': result.score
                })
        
        return sorted(all_results, key=lambda x: x['score'], reverse=True)[:limit]
