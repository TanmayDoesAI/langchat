# chain.py

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

def init_conversational_chain(llm, retriever):
    """
    Initialize the Conversational Retrieval Chain with memory and custom prompt.
    
    Args:
        llm: The language model to use.
        retriever: The retriever to fetch relevant documents.
    
    Returns:
        An instance of ConversationalRetrievalChain.
    """
    # Initialize conversation memory
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer"
    )
    
    # Define a custom prompt template
    custom_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are LangAssist, a knowledgeable assistant for the LangChain Python Library. "
            "Given the following context from the documentation, provide a helpful answer to the user's question.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
    )

    # Initialize the Conversational Retrieval Chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": custom_prompt},
        verbose=False
    )
    return qa_chain
