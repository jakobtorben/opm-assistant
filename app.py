import chainlit as cl
from rag_chain import create_conversational_rag_chain
import uuid

conversational_rag_chain = create_conversational_rag_chain()

@cl.on_chat_start
def start():
    cl.user_session.set("session_id", str(uuid.uuid4()))

@cl.on_message
async def main(message: cl.Message):
    session_id = cl.user_session.get("session_id")
    
    response = conversational_rag_chain.invoke(
        {"input": message.content},
        {"configurable": {"session_id": session_id}}
    )
    
    await cl.Message(content=response['answer']).send()