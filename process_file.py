from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


class FileProcessResult:
    def __init__(self, add_to_context=False, content=''):
        self.add_to_context = add_to_context
        self.content = content

def process_file(file):
    global additional_context

    file_extension = file.name.split('.')[-1].lower()

    if file_extension in ['data', 'dbg', 'inc', 'sch']:
        with open(file.path, "r") as f:
            content = f.read()

        if file_extension == 'data':
            return FileProcessResult(add_to_context=True, content=content)

    elif file_extension == 'pdf':
        # Use PyPDFLoader to load the PDF
        loader = PyPDFLoader(file.path)
        pages = loader.load()

        # Split the text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(pages)

        # Combine all text chunks into a single string
        content = "\n".join([doc.page_content for doc in texts])

        # Return the content without adding to the context
        return FileProcessResult(add_to_context=False, content=content)

    return FileProcessResult(add_to_context=False)