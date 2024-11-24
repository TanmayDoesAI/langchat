# retriever.py

from langchain.schema import BaseRetriever
from typing import List
from pydantic import BaseModel

class CombinedRetriever(BaseRetriever):
    """
    A retriever that combines multiple retrievers and returns the top K relevant documents.
    """
    retrievers: List[BaseRetriever]
    k: int = 5

    def _get_relevant_documents(self, query: str):
        """
        Retrieve relevant documents by querying all combined retrievers.

        Args:
            query: The search query string.

        Returns:
            A list of relevant documents.
        """
        all_docs = []
        for retriever in self.retrievers:
            # Correctly invoke the retriever with the query string
            docs = retriever.get_relevant_documents(query)
            all_docs.extend(docs)
        # Return the top K documents
        return all_docs[:self.k]

    async def _aget_relevant_documents(self, query: str):
        """
        Asynchronously retrieve relevant documents by querying all combined retrievers.

        Args:
            query: The search query string.

        Returns:
            A list of relevant documents.
        """
        all_docs = []
        for retriever in self.retrievers:
            # Correctly invoke the retriever with the query string
            docs = await retriever.aget_relevant_documents(query)
            all_docs.extend(docs)
        # Return the top K documents
        return all_docs[:self.k]

def create_combined_retriever(vector_stores, search_kwargs={"k": 3}):
    """
    Create a CombinedRetriever from multiple vector stores.

    Args:
        vector_stores: A dictionary of vector stores.
        search_kwargs: Keyword arguments for the retrievers (e.g., number of documents).

    Returns:
        An instance of CombinedRetriever.
    """
    retrievers = [
        vs.as_retriever(search_kwargs=search_kwargs)
        for vs in vector_stores.values()
    ]

    combined_retriever = CombinedRetriever(
        retrievers=retrievers,
        k=search_kwargs.get("k", 3)
    )
    return combined_retriever
