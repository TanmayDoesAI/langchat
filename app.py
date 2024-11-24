# app.py

import gradio as gr
from embeddings import init_embeddings
from vectorstore import load_all_vector_stores
from retriever import create_combined_retriever
from chain import init_conversational_chain
from langchain_groq import ChatGroq  # Custom LLM class
from dotenv import load_dotenv
import os
import sys

# Disable parallelism warnings from tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def init_llm():
    """
    Initialize the Language Model (LLM) using the ChatGroq class.
    Loads environment variables from a .env file.
    """
    load_dotenv()
    llm = ChatGroq()
    return llm

def setup():
    """
    Set up the QA chain by initializing embeddings, loading vector stores,
    creating a combined retriever, and initializing the conversational chain.
    """
    embeddings = init_embeddings()
    
    # Check if vector stores exist
    if not os.path.exists("vector_stores") or not os.listdir("vector_stores"):
        print("Vector stores not found. Please run 'build_vectorstore.py' first.")
        sys.exit(1)
    
    # Load all vector stores
    vector_stores = load_all_vector_stores(embeddings)
    
    # Create a combined retriever from all vector stores
    retriever = create_combined_retriever(vector_stores)
    
    # Initialize the LLM
    llm = init_llm()
    
    # Initialize the conversational QA chain
    qa_chain = init_conversational_chain(llm, retriever)
    return qa_chain

# Set up the QA chain
qa_chain = setup()

def format_source_doc(doc):
    """
    Format a source document for display.
    
    Args:
        doc: A document object containing page_content and metadata.
    
    Returns:
        A dictionary with a preview, full content, and source.
    """
    preview = doc.page_content[:150] + "..."  # Short preview
    source = doc.metadata.get('source', 'Unknown')
    return {
        "preview": preview,
        "full_content": doc.page_content,
        "source": source
    }

def get_chat_history_tuples(history_messages):
    """
    Convert the chat history from a list of message dictionaries to a list of tuples.
    
    Args:
        history_messages: List of message dictionaries with 'role' and 'content'.
    
    Returns:
        List of tuples in the form (user_message, assistant_message).
    """
    chat_history_tuples = []
    user_msg = None
    assistant_msg = None
    for msg in history_messages:
        if msg['role'] == 'user':
            if user_msg is not None:
                # Append previous user message without assistant response
                chat_history_tuples.append((user_msg, assistant_msg))
            user_msg = msg['content']
            assistant_msg = None
        elif msg['role'] == 'assistant':
            assistant_msg = msg['content']
            chat_history_tuples.append((user_msg, assistant_msg))
            user_msg = None
            assistant_msg = None
    # Append any remaining user message
    if user_msg is not None:
        chat_history_tuples.append((user_msg, assistant_msg))
    return chat_history_tuples

def chatbot(message, history):
    """
    Handle the chatbot interaction by invoking the QA chain and formatting the response.
    
    Args:
        message: The user's message.
        history: The chat history.
    
    Returns:
        A tuple containing the assistant's answer and the list of source documents.
    """
    # Convert history to list of tuples
    if history is None:
        history = []
    chat_history = get_chat_history_tuples(history)
    
    # Invoke the QA chain with the formatted history
    response = qa_chain.invoke({
        "question": message,
        "chat_history": chat_history
    })
    
    # Format the response as a message dictionary
    answer = {
        "role": "assistant",
        "content": response["answer"]
    }
    
    # Format source documents
    source_docs = [format_source_doc(doc) for doc in response["source_documents"]]
    
    return answer, source_docs

def show_popup(source_doc):
    """
    Show a popup with the full content of the selected source document.
    
    Args:
        source_doc: The selected source document.
    
    Returns:
        An update object for the Gradio Textbox component.
    """
    return gr.update(
        value=f"Source: {source_doc['source']}\n\n{source_doc['full_content']}",
        visible=True
    )

# Define the Gradio Blocks interface
with gr.Blocks(css="""
    .source-box { margin: 5px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
    .source-box:hover { background-color: #f5f5f5; cursor: pointer; }
""") as demo:
    gr.Markdown("# Lang-Chat Chatbot")
    
    with gr.Row():
        with gr.Column(scale=7):
            # Chat history component
            chatbot_component = gr.Chatbot(
                label="Chat History",
                height=500,
                bubble_full_width=False,
                type="messages"
            )

            with gr.Row():
                # Input textbox for user messages
                msg = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask me anything about LangChain...",
                    scale=8
                )
                # Submit button
                submit = gr.Button("Send", scale=1)

        with gr.Column(scale=3):
            gr.Markdown("### Source Documents")
            # Dropdown to select source documents
            source_dropdown = gr.Dropdown(
                label="Select a Source Document",
                interactive=True
            )
            # Textbox to display full content of the selected document
            popup = gr.Textbox(
                label="Document Details",
                interactive=False,
                visible=False,
                lines=10
            )
            # Hidden state to store source data
            source_data_state = gr.State()

    def process_message(message, history):
        """
        Process the user's message, update chat history, and prepare source document options.
        
        Args:
            message: The user's message.
            history: The current chat history.
        
        Returns:
            Updated chat history, updated source dropdown options, and updated source data state.
        """
        if history is None:
            history = []
        answer, sources = chatbot(message, history)
        
        # Append the new user message and assistant response to history
        history.append({"role": "user", "content": message})
        history.append(answer)
        
        # Prepare options for the dropdown
        source_options = []
        for idx, source in enumerate(sources):
            option_label = f"{idx+1}. {source['source']} - {source['preview'][:30]}..."
            source_options.append(option_label)
        
        # Store sources in state
        source_data_state = sources
        
        return history, gr.update(choices=source_options, value=None), source_data_state

    # Define the submit action for both the textbox and the button
    msg.submit(
        process_message,
        [msg, chatbot_component],
        [chatbot_component, source_dropdown, source_data_state]
    )
    submit.click(
        process_message,
        [msg, chatbot_component],
        [chatbot_component, source_dropdown, source_data_state]
    )

    def show_popup(selected_option, source_data_state):
        """
        Display the full content of the selected source document in a popup.
        
        Args:
            selected_option: The selected option from the dropdown.
            source_data_state: The list of source documents.
        
        Returns:
            An update object for the popup textbox.
        """
        if selected_option is None:
            return gr.update(visible=False)
        sources = source_data_state
        # Extract index from selected_option
        idx = int(selected_option.split('.')[0]) - 1
        source = sources[idx]
        full_content = f"Source: {source['source']}\n\n{source['full_content']}"
        return gr.update(value=full_content, visible=True)

    # Define the change action for the dropdown
    source_dropdown.change(show_popup, inputs=[source_dropdown, source_data_state], outputs=popup)

# Launch the Gradio interface
demo.launch()
