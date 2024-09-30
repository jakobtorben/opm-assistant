import streamlit as st
import os
from dotenv import load_dotenv
from process_file import process_file
from rag_chain import create_conversational_rag_chain
import uuid
from process_file import plot_sgwfn_data

st.set_page_config(layout="centered", page_title="OPM Assistant", page_icon="opm_logo_compact.png")
KEYWORDS_TO_SHOW = 4

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
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

def clear_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.custom_context = []
    st.session_state.context_added = False
    st.session_state.processed_files.clear()
    st.session_state.data = []
    st.session_state["uploaded_files"] = []
    st.session_state["file_uploader_key"] += 1


def is_api_key_valid(api_key):
    import openai
    client = openai.OpenAI(api_key=api_key)
    try:
        client.models.list()
    except openai.AuthenticationError as e:
        return False
    else:
        return True

def render_html_file(html_file_path):
    # Ensure the path is relative to the current working directory
    if not html_file_path.startswith('opm-reference-manual'):
        # remove everything before 'opm-reference-manual'
        html_file_path = 'opm-reference-manual' + html_file_path.split('opm-reference-manual')[1]
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        st.html(html_content)
    except FileNotFoundError:
        st.error(f"HTML file not found: {html_file_path}")

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
    # check if the API key is in the environment variables (for local testing)
    load_dotenv()
    st.session_state.api_key = os.getenv("OPENAI_API_KEY")
    if not st.session_state.api_key:
        st.session_state.api_key = st.text_input('Your OpenAI API Key:', type='password')

    # check if the API key valid
    if st.session_state.api_key and not is_api_key_valid(st.session_state.api_key):
        st.error('Invalid OpenAI API key. Please provide a valid key.')
        st.stop()


    # File uploader
    uploaded_files = st.file_uploader("Upload a file",
                                      type=['data', 'dbg', 'inc', 'sch', 'pdf', 'txt'],
                                      accept_multiple_files=True,
                                      label_visibility="collapsed",
                                      key=st.session_state["file_uploader_key"])
    if uploaded_files:
        new_files_processed = False
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.processed_files:
                result = process_file(uploaded_file, st.session_state.session_id)
                if result.content:
                    st.session_state.custom_context.append(result.content)
                if result.data:
                    st.session_state.data.append(result.data)
                st.session_state.processed_files.add(uploaded_file.name)
                new_files_processed = True
        if new_files_processed:
            st.success("New file(s) processed successfully!")
        st.session_state.context_added = False

# Display the entire chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # Check if this is an assistant message
    if message["role"] == "assistant":
        # Check if the message contains "SGWFN" and "plot"
        if "SGWFN" in message["content"] and "plot" in message["content"]:
            # Retrieve the SGWFN data
            recent_sgwfn_data = st.session_state.data[0]
            if recent_sgwfn_data:
                fig = plot_sgwfn_data(recent_sgwfn_data)
                st.pyplot(fig)
            else:
                st.warning("No SGWFN data available to plot.")

    # Check if this is an assistant message and has context
    if message["role"] == "assistant" and "context" in st.session_state.get(f"message_{i}", {}):
        context = st.session_state[f"message_{i}"]["context"]
        keyword_docs = [doc for doc in context if 'opm-reference-manual' in doc.metadata.get('source', '')]

        if keyword_docs:
            unique_docs = {doc.metadata.get('title', f'Document {j+1}'): doc for j, doc in enumerate(keyword_docs[:KEYWORDS_TO_SHOW])}

            # Create a horizontal layout for buttons
            cols = st.columns(len(unique_docs))
            for j, (title, doc) in enumerate(unique_docs.items()):
                with cols[j]:
                    if st.button(f"{title}", key=f"doc_button_{i}_{j}"):
                        # Clear previous selections
                        for k in range(len(unique_docs)):
                            if k != j:
                                st.session_state[f"show_doc_{i}_{k}"] = False
                        # Toggle the visibility state for this document
                        current_state = st.session_state.get(f"show_doc_{i}_{j}", False)
                        st.session_state[f"show_doc_{i}_{j}"] = not current_state

            for j, (title, doc) in enumerate(unique_docs.items()):
                if st.session_state.get(f"show_doc_{i}_{j}", False):
                    file_path = doc.metadata.get('source', '')
                    html_file_path = file_path.replace('.txt', '.html')
                    html_file_path = html_file_path.replace('txt_parts', 'html_parts')
                    render_html_file(html_file_path)

# Chat input
if prompt := st.chat_input("How can I help you?"):
    if not st.session_state.api_key:
        st.info("Please add your OpenAI API key in the sidebar to continue.")
        st.stop()

    conversational_rag_chain = create_conversational_rag_chain(model=model, api_key=st.session_state.api_key)

    # Display the user's message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add the message to the session state
    message = {"role": "user", "content": prompt}
    st.session_state.messages.append(message)

    # Print the prompt for debugging
    print(f"User prompt: {prompt}")

    # Add custom context to the prompt only if it hasn't been added before
    if not st.session_state.context_added:
        custom_context = "\n".join(st.session_state.custom_context)
        prompt = f"{custom_context}\n\n{prompt}"
        st.session_state.context_added = True

    # Display the assistant's response with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        context = []
        
        for chunk in conversational_rag_chain.stream({
            "input": prompt,
            "configurable": {"session_id": st.session_state.session_id}
        }, config={"configurable": {"session_id": st.session_state.session_id}}):
            if 'answer' in chunk:
                full_response += chunk['answer']
                message_placeholder.markdown(full_response + "▌")
            if 'context' in chunk:
                context.extend(chunk['context'])
        
        message_placeholder.markdown(full_response)

    # Store the response and context in session state
    message_index = len(st.session_state.messages)
    st.session_state[f"message_{message_index}"] = {
        "context": context
    }
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Print the response and context for debugging
    print(f"Assistant response: {full_response}")
    print(f"Context: {context}")

    # update site
    st.rerun()
