__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.retrievers import MultiQueryRetriever
from langchain.schema import BaseRetriever, Document
from typing import List
from pydantic import Field

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def create_conversational_rag_chain(model, api_key, session_id):
    # Construct QA prompt from system prompt and chat history
    system_prompt = (
        "You are an assistant for question-answering tasks to support reservoir engineers for reservoir simulation. "
        "Use the following pieces of retrieved context to answer "
        "the question."
        "\n\n"
        "{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Contextualize question with chat history
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=api_key)

    # Create the KEYWORDS vector store
    keywords_vector_store = Chroma(
        collection_name="KEYWORDS",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )

    # Create the combined vector store
    combined_collection_name = f"COMBINED_{session_id}"
    combined_vector_store = Chroma(
        collection_name=combined_collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_combined_db",
    )

    # Create a custom retriever that combines results from both vector stores
    class CombinedRetriever(BaseRetriever):
        keywords_retriever: BaseRetriever = Field(..., description="Retriever for keywords")
        combined_retriever: BaseRetriever = Field(..., description="Retriever for combined search")

        class Config:
            arbitrary_types_allowed = True

        def get_relevant_documents(self, query: str) -> List[Document]:
            keywords_docs = self.keywords_retriever.invoke(query)
            combined_docs = self.combined_retriever.invoke(query)

            # Combine and deduplicate the results
            all_docs = keywords_docs + combined_docs
            unique_docs = list({doc.page_content: doc for doc in all_docs}.values())

            return unique_docs

        async def aget_relevant_documents(self, query: str) -> List[Document]:
            keywords_docs = await self.keywords_retriever.ainvoke(query)
            combined_docs = await self.combined_retriever.ainvoke(query)

            # Combine and deduplicate the results
            all_docs = keywords_docs + combined_docs
            unique_docs = list({doc.page_content: doc for doc in all_docs}.values())

            return unique_docs

    keywords_retriever = keywords_vector_store.as_retriever()
    combined_retriever = combined_vector_store.as_retriever()

    # Create the combined retriever
    combined_retriever = CombinedRetriever(
        keywords_retriever=keywords_retriever,
        combined_retriever=combined_retriever
    )

    # Create the MultiQueryRetriever using the combined retriever
    retriever = MultiQueryRetriever.from_llm(
        retriever=combined_retriever,
        llm=ChatOpenAI(model=model, temperature=0, api_key=api_key)
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # Create a conversational chain with message history
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    return conversational_rag_chain