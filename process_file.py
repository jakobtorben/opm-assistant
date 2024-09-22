from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import matplotlib.pyplot as plt

class FileProcessResult:
    def __init__(self, add_to_context=False, content='', data=None):
        self.add_to_context = add_to_context
        self.content = content
        self.data = data

def process_file(file):
    file_extension = file.name.split('.')[-1].lower()
    file_name = file.name.lower()

    if file_extension in ['data', 'dbg', 'sch']:
        content = file.read().decode('utf-8')  # Read as text
        if file_extension == 'data':
            return FileProcessResult(add_to_context=True, content=content)

    elif file_extension == 'pdf':
        # Use PyPDFLoader to load the PDF
        loader = PyPDFLoader(file)
        pages = loader.load()

        # Split the text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(pages)

        # Combine all text chunks into a single string
        content = "\n".join([doc.page_content for doc in texts])

        # Return the content without adding to the context
        return FileProcessResult(add_to_context=False, content=content)

    elif file_name == "tables.inc":
        # Split the content into tables
        file_content = file.read().decode('utf-8')
        tables = file_content.split('/')[:-1]  # Exclude the last empty element
        
        all_data = []
        for table in tables:
            lines = table.strip().split('\n')
            header = lines[0].strip('-- ').split()
            data = [line.split() for line in lines[2:] if line and not line.startswith('SGWFN')]
            table_data = {col: [float(row[i]) for row in data] for i, col in enumerate(header)}
            all_data.append(table_data)
            
        return FileProcessResult(add_to_context=False, data=all_data)
        
    return FileProcessResult(add_to_context=False)


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
