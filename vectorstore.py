# vectorstore.py

import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

def load_and_split_document(file_path, chunk_size=1000, chunk_overlap=150):
    """
    Load a document from a file and split it into chunks.
    
    Args:
        file_path: Path to the text file.
        chunk_size: The maximum size of each chunk.
        chunk_overlap: The overlap between chunks.
    
    Returns:
        A list of document chunks.
    """
    loader = TextLoader(
        file_path,
        encoding='utf-8',
        autodetect_encoding=True
    )
    
    try:
        documents = loader.load()
    except RuntimeError:
        # Fallback to a different encoding if autodetection fails
        loader = TextLoader(
            file_path,
            encoding='latin-1',
            autodetect_encoding=False
        )
        documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    return chunks

def create_vector_stores(doc_paths, embeddings):
    """
    Create vector stores from a list of document paths.
    
    Args:
        doc_paths: List of paths to document files.
        embeddings: The embeddings model to use.
    
    Returns:
        A dictionary of vector stores.
    """
    vector_stores = {}
    os.makedirs("vector_stores", exist_ok=True)
    
    for doc_path in doc_paths:
        store_name = os.path.basename(doc_path).split('.')[0]
        chunks = load_and_split_document(doc_path)
        print(f"Processing {store_name}: {len(chunks)} chunks created")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(f"vector_stores/{store_name}")
        vector_stores[store_name] = vectorstore
    
    return vector_stores

def create_vector_store_from_folder(folder_path, embeddings):
    """
    Create a single vector store from all text files in a folder.
    
    Args:
        folder_path: Path to the folder containing text files.
        embeddings: The embeddings model to use.
    
    Returns:
        A dictionary containing the created vector store.
    """
    vector_stores = {}
    os.makedirs("vector_stores", exist_ok=True)
    all_chunks = []
    file_names = []
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            chunks = load_and_split_document(file_path)
            all_chunks.extend(chunks)
            file_names.append(filename)
    
    print(f"Processing {folder_path}: {len(all_chunks)} chunks created from {len(file_names)} files")
    vectorstore = FAISS.from_documents(all_chunks, embeddings)
    store_name = os.path.basename(folder_path.rstrip('/'))
    vectorstore.save_local(f"vector_stores/{store_name}")
    vector_stores[store_name] = vectorstore
    
    return vector_stores

def load_all_vector_stores(embeddings):
    """
    Load all vector stores from the 'vector_stores' directory.
    
    Args:
        embeddings: The embeddings model to use.
    
    Returns:
        A dictionary of loaded vector stores.
    """
    vector_stores = {}
    store_dir = "vector_stores"
    
    for store_name in os.listdir(store_dir):
        store_path = os.path.join(store_dir, store_name)
        if os.path.isdir(store_path):
            vector_stores[store_name] = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
    return vector_stores
