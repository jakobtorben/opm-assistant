import streamlit as st
import os
from dotenv import load_dotenv
from process_file import process_file
from rag_chain import create_conversational_rag_chain
import uuid
from process_file import plot_sgwfn_data

st.set_page_config(layout="centered", page_title="OPM Assistant", page_icon="opm_logo_compact.png")


# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'custom_context' not in st.session_state:
    st.session_state.custom_context = []
if 'context_added' not in st.session_state:
    st.session_state.context_added = False
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = set()
if 'data' not in st.session_state:
    st.session_state.data = []

def clear_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.custom_context = []
    st.session_state.context_added = False
    st.session_state.processed_files.clear()


def check_openai_api_key_exist():
    if 'OPENAI_API_KEY' not in os.environ:
        st.error('Please provide your OpenAI API key in the sidebar.')
        st.stop()


def is_api_key_valid(api_key):
    import openai
    client = openai.OpenAI(api_key=api_key)
    try:
        client.models.list()
    except openai.AuthenticationError as e:
        return False
    else:
        return True


with st.sidebar:
    st.image('opm_logo.png')
    
    # Add a button to clear the chat history and custom context
    if st.button("Clear Chat History and Context", on_click=clear_chat):
        st.success("Chat history and custom context cleared!")

    # Model selection
    model = st.selectbox(
        "Choose a model",
        ("gpt-4o-mini", "gpt-4o"),
        index=0
    )

    # set the API key

    # check if the API key is in the environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = st.text_input('Your OpenAI API Key:', type='password')
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key

    # check if the API key is not valid
    if api_key and not is_api_key_valid(api_key):
        st.error('Invalid OpenAI API key. Please provide a valid key.')
        st.stop()


    # File uploader
    uploaded_files = st.file_uploader("Upload a file", type=['data', 'inc', 'sch', 'pdf', 'txt'], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded_files:
        new_files_processed = False
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.processed_files:
                result = process_file(uploaded_file)
                if result.content:
                    st.session_state.custom_context.append(result.content)
                if result.data:
                    st.session_state.data.append(result.data)
                st.session_state.processed_files.add(uploaded_file.name)
                new_files_processed = True
        if new_files_processed:
            st.success("New file(s) processed successfully!")
        st.session_state.context_added = False

# Only create the conversational RAG chain if a valid API key is provided
if api_key and is_api_key_valid(api_key):
    conversational_rag_chain = create_conversational_rag_chain(model=model)
else:
    conversational_rag_chain = None


# Chat input
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Print the prompt for debugging
    print(f"User prompt: {prompt}")
    
    # Add custom context to the prompt only if it hasn't been added before
    if not st.session_state.context_added:
        custom_context = "\n".join(st.session_state.custom_context)
        prompt = f"{custom_context}\n\n{prompt}"
        st.session_state.context_added = True

    # Invoke the conversational RAG chain
    response = conversational_rag_chain.invoke(
        {"input": prompt},
        {"configurable": {"session_id": st.session_state.session_id}}
    )

    full_response = response['answer']
    context = response.get('context', [])

    # Print the response and context for debugging
    print(f"Assistant response: {full_response}")
    print(f"Context: {context}")

    # Store the response and context in session state
    message_index = len(st.session_state.messages)
    st.session_state[f"message_{message_index}"] = {
        "context": context
    }
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Check if this is an assistant message
        if message["role"] == "assistant":
            # Check if the message contains "SGOF" and "plot"
            if "SGWFN" in message["content"] and "plot" in message["content"]:
                # Retrieve the SGOF data
                recent_sgwfn_data = st.session_state.data[0]
                if recent_sgwfn_data:
                    fig = plot_sgwfn_data(recent_sgwfn_data)
                    st.pyplot(fig)
                else:
                    st.warning("No SGOF data available to plot.")
        
        # Check if this is an assistant message and has context
        if message["role"] == "assistant" and "context" in st.session_state.get(f"message_{i}", {}):
            context = st.session_state[f"message_{i}"]["context"]
            unique_docs = {doc.metadata.get('title', f'Document {j+1}'): doc for j, doc in enumerate(context)}
            
            # Create a horizontal layout for buttons
            cols = st.columns(len(unique_docs))
            for j, (title, doc) in enumerate(unique_docs.items()):
                with cols[j]:
                    if st.button(f"{title}", key=f"doc_button_{i}_{j}"):
                        # Clear previous selections
                        for k in range(len(unique_docs)):
                            if k != j:
                                st.session_state[f"show_doc_{i}_{k}"] = False
                        # Set current selection
                        st.session_state[f"show_doc_{i}_{j}"] = True

        # Display HTML content if the corresponding button was clicked
        if message["role"] == "assistant" and "context" in st.session_state.get(f"message_{i}", {}):
            for j, (title, doc) in enumerate(unique_docs.items()):
                if st.session_state.get(f"show_doc_{i}_{j}", False):
                    html_file_path = doc.metadata.get('source', '')
                  
                    if html_file_path:
                        # Ensure the path is relative to the current working directory
                        if not html_file_path.startswith('opm-reference-manual'):
                            # remove everything before 'opm-reference-manual'
                            html_file_path = 'opm-reference-manual' + html_file_path.split('opm-reference-manual')[1]
                        try:
                            with open(html_file_path, 'r', encoding='utf-8') as file:
                                html_content = file.read()
                            #st.components.v1.html(html_content, height=600, width=800, scrolling=True)
                            st.html(html_content)
                        except FileNotFoundError:
                            st.error(f"HTML file not found: {html_file_path}")
                    else:
                        st.error("Source file path not available for this document.")