import os
import hashlib
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import Docx2txtLoader, UnstructuredPowerPointLoader, UnstructuredExcelLoader, PyPDFLoader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

# Function to generate a unique ID for a document
def generate_document_id(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# Function to check for existing document IDs in the vector database
def get_existing_document_ids(vectordb):
    existing_ids = set()
    for doc in vectordb.get()["metadatas"]:
        existing_ids.add(doc['id'])
    return existing_ids

# Function to load documents from various formats
def load_documents_from_directory(directory):
    documents = []

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if filename.endswith('.docx'):
            documents.extend(load_docx(file_path))
        elif filename.endswith('.pdf'):
            documents.extend(load_pdf(file_path))
        elif filename.endswith('.xlsx'):
            documents.extend(load_xlsx(file_path))
        elif filename.endswith('.txt'):
            documents.extend(load_txt(file_path))
        #elif filename.endswith('.pptx'):
        #    documents.extend(load_pptx(file_path))
    
    return documents

# Function to load DOCX files
def load_docx(file_path):
    loader = Docx2txtLoader(file_path)
    documents = loader.load()
    return [Document(page_content=doc.page_content, metadata={'id': generate_document_id(doc.page_content), 'source': file_path}) for doc in documents]

# Function to load PDF files
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load_and_split()
    return [Document(page_content=doc.page_content, metadata={'id': generate_document_id(doc.page_content), 'source': file_path}) for doc in documents]

# Function to load XLSX files
def load_xlsx(file_path):
    loader = UnstructuredExcelLoader(file_path, mode="elements")
    documents = loader.load()
    return [Document(page_content=doc.page_content, metadata={'id': generate_document_id(doc.page_content), 'source': file_path}) for doc in documents]

# Function to load TXT files
def load_txt(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return [Document(page_content=content, metadata={'id': generate_document_id(content), 'source': file_path})]

# Function to load PPTX files
def load_pptx(file_path):
    loader = UnstructuredPowerPointLoader(file_path)
    documents = loader.load()
    return [Document(page_content=doc.page_content, metadata={'id': generate_document_id(doc.page_content), 'source': file_path}) for doc in documents]

# Function to create and populate the ChromaDB
def create_chroma_db(directory, db_directory):
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    existing_ids = get_existing_document_ids(vectordb)
    documents = load_documents_from_directory(directory)

    # Filter out documents with existing IDs
    new_documents = [doc for doc in documents if doc.metadata['id'] not in existing_ids]

    # Add new documents to the vector store
    if new_documents:
        vectordb.add_documents(new_documents)
        vectordb.persist()
        print(f"Added {len(new_documents)} new documents to the ChromaDB.")
    else:
        print("No new documents to add.")
    
    print("ChromaDB has been successfully created and populated with the documents.")

# Directory containing the documents
documents_directory = "/Users/lakshhkhatri/Desktop/WiproProject/Mock project Data/Samsung Health Project Mock Data"
# Directory to store the ChromaDB
chroma_db_directory = "internalDocs"

# Create and populate the ChromaDB
create_chroma_db(documents_directory, chroma_db_directory)
