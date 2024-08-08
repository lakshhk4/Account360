import os
import hashlib
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import Docx2txtLoader, UnstructuredPowerPointLoader, PyPDFLoader, UnstructuredExcelLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from dotenv import load_dotenv

load_dotenv()

# Load environment variables from .env file
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

print("running..")

# Function to generate a unique ID for a document
def generate_document_id(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        document = Document(page_content=content, metadata={'id': generate_document_id(content), 'source': file_path})
        return [document]
    except Exception as e:
        print(f"Error loading TXT file {file_path}: {e}")
        return []

def load_pdf(file_path):
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Concatenate all pages into a single Document
        full_content = "\n".join(doc.page_content for doc in documents)
        combined_document = Document(page_content=full_content, metadata={'id': generate_document_id(full_content), 'source': file_path})
        
        return [combined_document]
    except Exception as e:
        print(f"Error loading PDF file {file_path}: {e}")
        return []

def load_docx(file_path):
    try:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        return [Document(page_content=doc.page_content, metadata={'id': generate_document_id(doc.page_content), 'source': file_path}) for doc in documents]
    except Exception as e:
        print(f"Error loading DOCX file {file_path}: {e}")
        return []

def load_pptx(file_path):
    try:
        loader = UnstructuredPowerPointLoader(file_path)
        documents = loader.load()
        return [Document(page_content=doc.page_content, metadata={'id': generate_document_id(doc.page_content), 'source': file_path}) for doc in documents]
    except Exception as e:
        print(f"Error loading PPTX file {file_path}: {e}")
        return []

def load_csv(file_path):
    try:
        loader = CSVLoader(file_path)
        documents = loader.load()
        
        # Concatenate all rows into a single Document
        full_content = "\n".join(doc.page_content for doc in documents)
        combined_document = Document(page_content=full_content, metadata={'id': generate_document_id(full_content), 'source': file_path})
        
        return [combined_document]
    except Exception as e:
        print(f"Error loading CSV file {file_path}: {e}")
        return []

# Function to load documents from a directory and its subdirectories
def load_documents_from_directory(directory):
    documents = []
    loaded_files = set()

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if file_path in loaded_files:
                continue
            if filename.endswith('.docx'):
                documents.extend(load_docx(file_path))
            elif filename.endswith('.pptx'):
                #documents.extend(load_pptx(file_path))
                pass
            elif filename.endswith('.pdf'):
                documents.extend(load_pdf(file_path))
            elif filename.endswith('.txt'):
                documents.extend(load_txt(file_path))
            elif filename.endswith('.csv'):
                documents.extend(load_csv(file_path))
            # Commenting out Excel loader for now
            # elif filename.endswith('.xlsx'):
            #     documents.extend(load_excel(file_path))

            loaded_files.add(file_path)
    
    return documents

# Function to create and populate the ChromaDB
def create_chroma_db(directory, db_directory):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    # Load documents from the directory
    documents = load_documents_from_directory(directory)
    
    # Get existing document IDs to avoid re-adding documents
    existing_ids = get_existing_document_ids(vectordb)
    
    # Filter out documents that already exist in the vector store
    new_documents = [doc for doc in documents if doc.metadata['id'] not in existing_ids]
    
    # Add new documents to the vector store
    if new_documents:
        vectordb.add_documents(new_documents)
        vectordb.persist()
        print(f"Added {len(new_documents)} new documents to the ChromaDB.")
    else:
        print("No new documents to add.")
    
    print("ChromaDB has been successfully created and populated with the documents.")

# Function to check for existing document IDs in the vector database
def get_existing_document_ids(vectordb):
    existing_ids = set()
    for doc in vectordb.get()["metadatas"]:
        existing_ids.add(doc['id'])
    return existing_ids

# Directory containing the documents
documents_directory = "/Users/lakshhkhatri/Desktop/WiproProject/Mock project Data/Samsung Health Project Mock Data"
db_directory = "./chroma_db_internal_data"

# Function to retrieve documents using MMR search
def retrieve_and_compile_documents_internal(question, db_directory, k=5):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)

    # Retrieve documents from the vector database
    retrieved_documents = vectordb.max_marginal_relevance_search(question, k=k)
    
    # Compile and print the results
    compiled_results = f"Question: {question}\n\n"
    
    for j, doc in enumerate(retrieved_documents):
        compiled_results += f"Document {j+1}:\n"
        compiled_results += f"Source: {doc.metadata.get('source')}\n"
        compiled_results += f"Content: {doc.page_content}\n\n"
    
    # Print the compiled results
    print(compiled_results)

# Create the ChromaDB
#create_chroma_db(documents_directory, db_directory)

#print(get_existing_document_ids(Chroma(persist_directory=db_directory, embedding_function=OpenAIEmbeddings())))

def get_unique_files(db_directory):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    print("\nEmbedding keys:", vectordb.get().keys())
    print("\nNumber of embedded docs:", len(vectordb.get()["ids"]))

    # Print the list of source files
    file_list = []

    for x in range(len(vectordb.get()["ids"])):
        doc = vectordb.get()["metadatas"][x]
        source = doc["id"]  # Using 'canonical_url' instead of 'url'
        file_list.append(source)

    # Set only stores a value once even if it is inserted more than once.
    list_set = set(file_list)
    unique_list = list(list_set)

    print("\nList of unique files in db:\n")
    for unique_file in unique_list:
        print(unique_file)


#print(retrieve_and_print_documents_for_question("meetings", db_directory, k=5))