# build_vectorstore.py

from embeddings import init_embeddings
from vectorstore import create_vector_stores, create_vector_store_from_folder
import os

def main():
    """
    Main function to build vector stores from specified document paths and folders.
    """
    # Initialize embeddings
    embeddings = init_embeddings()

    # List of document paths to process
    doc_paths = [
        "docs/docs_v1.txt",
        "docs/docs_v2.txt",
        "docs/docs_v3.txt"
    ]

    # Create vector stores for individual documents
    create_vector_stores(doc_paths, embeddings)

    # Create vector store from the 'formatted_issues' folder
    formatted_issues_folder = "formatted_issues"
    if os.path.exists(formatted_issues_folder):
        create_vector_store_from_folder(formatted_issues_folder, embeddings)
    else:
        print(f"Folder {formatted_issues_folder} does not exist. Skipping.")

if __name__ == "__main__":
    main()
