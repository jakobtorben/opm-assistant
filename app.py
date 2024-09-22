import streamlit as st
from process_file import process_file
from rag_chain import create_conversational_rag_chain
import uuid

conversational_rag_chain = create_conversational_rag_chain()


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

# File uploader
uploaded_files = st.file_uploader("Upload a file", type=['data', 'dbg', 'inc', 'sch', 'pdf'], accept_multiple_files=True, label_visibility="collapsed")
if uploaded_files:
    new_files_processed = False
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.processed_files:
            result = process_file(uploaded_file)
            if result.content:
                st.session_state.custom_context.append(result.content)
            st.session_state.processed_files.add(uploaded_file.name)
            new_files_processed = True
    if new_files_processed:
        st.success("New file(s) processed successfully!")
    st.session_state.context_added = False
    
# Chat input
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

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
        message_placeholder.markdown(full_response)

        # Print the response and context for debugging
        print(f"Assistant response: {full_response}")
        print(f"Context: {response.get('context', 'No context available')}")
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add a button to clear the chat history and custom context
if st.button("Clear Chat History and Context"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.custom_context = []
    st.session_state.context_added = False
    st.session_state.processed_files.clear()
    st.success("Chat history and custom context cleared!")