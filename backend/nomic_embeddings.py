from langchain_community.embeddings import HuggingFaceBgeEmbeddings

class EmbeddingsModel:
    def __init__(self):
        model_name = "nomic-ai/nomic-embed-text-v1"
        model_kwargs = {
            'device': 'cpu',
            'trust_remote_code': True
        }
        encode_kwargs = {'normalize_embeddings': True}
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
            query_instruction="search_query:",
            embed_instruction="search_document:"
        )

    def get_embeddings(self, text):
        """
        Returns the embeddings for the given text.

        :param text: The input text to get embeddings for.
        :return: The embeddings as a numpy array.
        """
        return self.embeddings.embed_query(text)

# Example usage:
# embeddings_model = EmbeddingsModel()
# embeddings = embeddings_model.get_embeddings("Your input text here")