__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import matplotlib.pyplot as plt
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import streamlit as st

# Define word count limits
MAX_CONTEXT_WORDS = 10000  # for most files
MAX_DATA_CONTEXT_WORDS = 10000  # for .data files (input decks)
MAX_DATABASE_WORDS = 30000  # for database storage

class FileProcessResult:
    def __init__(self, add_to_context=False, content='', data=None):
        self.add_to_context = add_to_context
        self.content = content
        self.data = data

def count_words(text):
    return len(text.split())

def add_to_database(content, file_name, session_id):
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=st.session_state.api_key)

    # Create a combined collection name
    collection_name = f"COMBINED_{session_id}"

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_combined_db",
    )

    # Split the content into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(content)

    # Add chunks to the database
    vector_store.add_texts(chunks, metadatas=[{"source": file_name, "session_id": session_id} for _ in chunks])

    return len(chunks)

def process_text_file(content, file_extension, file_name, session_id):

    word_count = count_words(content)

    # Special handling for tables.inc
    if file_name == "tables.inc":
        # Split the content into tables
        tables = content.split('/')[:-1]  # Exclude the last empty element

        all_data = []
        for table in tables:
            lines = table.strip().split('\n')
            header = lines[0].strip('-- ').split()
            data = [line.split() for line in lines[2:] if line and not line.startswith('SGWFN')]
            table_data = {col: [float(row[i]) for row in data] for i, col in enumerate(header)}
            all_data.append(table_data)
        return FileProcessResult(add_to_context=False, data=all_data)

    # Add to context if file is small enough
    max_words = MAX_DATA_CONTEXT_WORDS if file_extension == 'data' else MAX_CONTEXT_WORDS
    if word_count <= max_words:
        print(f"File with {word_count} words added to context")
        return FileProcessResult(add_to_context=True, content=content)
    #elif word_count <= MAX_DATABASE_WORDS:
    #    chunks_added = add_to_database(content, file_name, session_id)
    #    print(f"File with {word_count} words added to database in {chunks_added} chunks for retrieval")
    #    return FileProcessResult(add_to_context=False, content=f"File {file_name} added to database for retrieval")
    else:
        truncated_content = ' '.join(content.split()[:max_words])
        #chunks_added = add_to_database(truncated_content, file_name, session_id)
        #print(f"File truncated to {MAX_DATABASE_WORDS} words and added to database in {chunks_added} chunks")
        print(f"File with {word_count} words added to context")
        return FileProcessResult(add_to_context=True, content=truncated_content)

def add_pdf_to_database(pages, session_id, file_name):
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=st.session_state.api_key)

    # Create a combined collection name
    collection_name = f"COMBINED_{session_id}"

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_combined_db",
    )

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(pages)

    # Add chunks to the database with metadata
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [{"source": file_name, "session_id": session_id, "page": chunk.metadata["page"]} for chunk in chunks]
    vector_store.add_texts(texts, metadatas=metadatas)

    return len(chunks)

def process_pdf_file(file, session_id):
    # Create a temporary file to save the uploaded PDF
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file.getvalue())
        temp_file_path = temp_file.name

    try:
        # Use PyPDFLoader to load the PDF
        loader = PyPDFLoader(temp_file_path)
        pages = loader.load()

        # Combine all page contents into a single string
        content = "\n".join([page.page_content for page in pages])
        word_count = count_words(content)

        # Check word count and handle accordingly
        if word_count <= MAX_CONTEXT_WORDS:
            print(f"PDF content with {word_count} words added to context")
            return FileProcessResult(add_to_context=True, content=content)
        #elif word_count <= MAX_DATABASE_WORDS:
        #    chunks_added = add_pdf_to_database(pages, session_id, file.name)
        #    print(f"PDF content with {word_count} words added to database in {chunks_added} chunks for retrieval")
        #    return FileProcessResult(add_to_context=False, content=f"PDF file {file.name} added to database for retrieval")
        else:
            average_words_per_page = word_count / len(pages)
            truncated_pages = pages[:int(MAX_CONTEXT_WORDS // average_words_per_page)]
            #chunks_added = add_pdf_to_database(truncated_pages, session_id, file.name)
            #print(f"PDF content truncated to {MAX_DATABASE_WORDS} words and added to database in {chunks_added} chunks")
            #return FileProcessResult(add_to_context=False, content=f"PDF file {file.name} truncated and added to database for retrieval")
            truncated_content = "\n".join([page.page_content for page in truncated_pages])
            print(f"PDF content truncated to {MAX_CONTEXT_WORDS} words and added to context")
            return FileProcessResult(add_to_context=True, content=truncated_content)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def process_file(file, session_id):
    file_extension = file.name.split('.')[-1].lower()
    file_name = file.name.lower()

    # Read file content
    content = file.read()

    # Decode content if it's a text file
    if file_extension in ['data', 'dbg', 'sch', 'inc', 'txt']:
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError:
            return FileProcessResult(add_to_context=True, content=f"File {file_name} could not be decoded")

        return process_text_file(content, file_extension, file_name, session_id)

    elif file_extension == 'pdf':
        return process_pdf_file(file, session_id)
    else:
        return FileProcessResult(add_to_context=True, content=f"Unsupported file type: {file_extension}")

def plot_sgwfn_data(dataframes):
    if not dataframes:
        return plt.figure()  # Return an empty figure if no data

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle('SGWFN Data')

    data = dataframes[0]  # We'll only plot the first dataset

    # Determine the correct column names
    sg_col = next((col for col in data.keys() if col.lower().startswith('s')), None)
    krg_col = next((col for col in data.keys() if col.lower().startswith('krg')), None)
    krw_col = next((col for col in data.keys() if col.lower().startswith('krw')), None)
    pcgw_col = next((col for col in data.keys() if col.lower().startswith('pc')), None)

    if sg_col and krg_col and krw_col and pcgw_col:
        ax.plot(data[sg_col], data[krg_col], label='KRG')
        ax.plot(data[sg_col], data[krw_col], label='KRW')
        ax.set_xlabel(sg_col)
        ax.set_ylabel('Relative Permeability')

        ax2 = ax.twinx()
        ax2.plot(data[sg_col], data[pcgw_col], 'r--', label='PCGW')
        ax2.set_ylabel('Capillary Pressure')

        # Combine legends from both axes
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    else:
        ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center')

    plt.tight_layout()
    return fig
