import streamlit as st
from rag_chain import create_conversational_rag_chain
import uuid

st.title("OPM Assistant")

conversational_rag_chain = create_conversational_rag_chain()

# Function to start a new chat
def start_new_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

# Initialize session_id
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add a "New Chat" button
if st.button("Start New Chat"):
    start_new_chat()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("How can I help you?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = conversational_rag_chain.invoke(
            {"input": prompt},
            {"configurable": {"session_id": st.session_state.session_id}}
        )
        full_response = response['answer']
        message_placeholder.markdown(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})