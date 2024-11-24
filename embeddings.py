# embeddings.py

from langchain_huggingface import HuggingFaceEmbeddings
import torch

def init_embeddings():
    """
    Initialize the HuggingFace embeddings model.
    
    Returns:
        An instance of HuggingFaceEmbeddings.
    """
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    }
    encode_kwargs = {'normalize_embeddings': False}
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    
    return embeddings
