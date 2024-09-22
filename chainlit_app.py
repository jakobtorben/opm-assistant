import chainlit as cl
from process_file import process_file
from rag_chain import create_conversational_rag_chain
import uuid

conversational_rag_chain = create_conversational_rag_chain()

@cl.on_chat_start
def start():
    cl.user_session.set("session_id", str(uuid.uuid4()))

@cl.on_message
async def main(message: cl.Message):
    session_id = cl.user_session.get("session_id")

    if message.elements:
        print("File has been uploaded ")
        for file in message.elements:
            print("Processing file: ", file)
            result = process_file(file)
            if result.add_to_context:
                message.content += f"\n\nContext from uploaded file: {result.content}"

    response = conversational_rag_chain.invoke(
        {"input": message.content},
        {"configurable": {"session_id": session_id}}
    )
    
    await cl.Message(content=response['answer']).send()