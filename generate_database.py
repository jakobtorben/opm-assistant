__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_community.document_loaders import BSHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
import json

from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")



def parse_html_files(directory):
    documents = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html') and not file.startswith('index'):
                file_path = os.path.join(root, file)
                loader = BSHTMLLoader(file_path)
                docs = loader.load()

                # Extract keyword name from filename
                keyword_name = os.path.splitext(file)[0].upper()

                # Update metadata and remove title for each document
                for doc in docs:
                    doc.metadata['title'] = keyword_name
                    # Remove the title and empty lines from the beginning of the content
                    doc.page_content = '\n'.join(line for line in doc.page_content.split('\n') if line.strip() and 'OPEN POROUS MEDIA' not in line)

                documents.extend(docs)
    return documents

def main():
    html_directory = "/home/jakob/code/opm-reference-manual/html_parts/chapters/subsections"
    documents = parse_html_files(html_directory)

    # Dump original documents to JSON
    with open('original_documents.json', 'w') as f:
        json.dump([doc.dict() for doc in documents], f, indent=2)

    print(f"Original documents dumped to 'original_documents.json'")

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # Dump splits to JSON
    with open('split_documents.json', 'w') as f:
        json.dump([split.dict() for split in splits], f, indent=2)

    print(f"Split documents dumped to 'split_documents.json'")

    # Create and persist vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vector_store = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_langchain_db",
        collection_name="KEYWORDS"
    )

if __name__ == "__main__":
    main()