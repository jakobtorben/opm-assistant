__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


def parse_txt_files(directory):
    documents = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt') and not file.startswith('index'):
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()

                # Extract keyword name from filename
                keyword_name = os.path.splitext(file)[0].upper()
                # Remove the navigation panel
                content = re.sub(r'RUNSPEC\nGRID\nEDIT\nPROPS\nREGIONS\nSOLUTION\nSUMMARY\nSCHEDULE\n', '', content)
                # Remove duuplicate whitespace
                content = re.sub(r' {2,}', ' ', content)
                # Remove leading and trailing whitespace
                content = content.strip()
                doc = Document(page_content=content, metadata={'title': keyword_name, 'source': file_path})
                documents.append(doc)
    return documents

def main():
    txt_directory = "/home/jakob/code/opm-assistant/opm-reference-manual/txt_parts/chapters/subsections"
    documents = parse_txt_files(txt_directory)

    # Dump original documents to JSON
    with open('original_documents_cleaned.json', 'w') as f:
        json.dump([doc.dict() for doc in documents], f, indent=2)

    print(f"Original documents dumped to 'original_documents.json'")

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # Dump splits to JSON
    with open('split_documents_cleaned.json', 'w') as f:
        json.dump([split.dict() for split in splits], f, indent=2)

    print(f"Split documents dumped to 'split_documents.json'")

    # Create and persist vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_langchain_db",
        collection_name="KEYWORDS_cleaned"
    )

if __name__ == "__main__":
    main()