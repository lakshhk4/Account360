import json
import os
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
from collections import Counter

# Load environment variables from .env file
load_dotenv()

# Access API keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

# Function to check for existing document IDs in the vector database
def get_existing_document_ids(vectordb):
    existing_ids = set()
    for doc in vectordb.get()["metadatas"]:
        existing_ids.add(doc['id'])
    return existing_ids

# Function to create and populate the ChromaDB
def create_chroma_db(file_path, db_directory):
    print("Initializing the vector database...")
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    print(f"Loading job data from {file_path}...")
    # Load job data from JSON file
    with open(file_path, 'r') as file:
        job_data = json.load(file)
    
    print("Retrieving existing document IDs to avoid duplicates...")
    # Get existing document IDs to avoid re-adding documents
    existing_ids = get_existing_document_ids(vectordb)
    
    print("Converting job data to Langchain Document objects...")
    # Convert job data to Langchain Document objects
    documents = []
    for i, job in enumerate(job_data):
        job_info = job['jobPostingInfo']
        if job_info['id'] not in existing_ids:
            metadata = {
                'id': job_info.get('id', ''),
                'title': job_info.get('title', ''),
                'location': job_info.get('location', ''),
                'postedOn': job_info.get('postedOn', ''),
                'startDate': job_info.get('startDate', ''),
                'jobReqId': job_info.get('jobReqId', ''),
                'jobPostingId': job_info.get('jobPostingId', ''),
                'jobPostingSiteId': job_info.get('jobPostingSiteId', ''),
                'country': job_info.get('country', {}).get('descriptor', ''),
                'remoteType': job_info.get('remoteType', ''),
                'externalUrl': job_info.get('externalUrl', ''),
                'questionnaireId': job_info.get('questionnaireId', ''),
            }
            
            document = Document(
                page_content=job_info.get('jobDescription', ''),
                metadata=metadata
            )
            documents.append(document)
            print(f"Added job document with ID {job_info['id']}")
        else:
            print(f"Duplicate job document with ID {job_info['id']} not added.")
    
    # Add new documents to the vector store
    if documents:
        print(f"Adding {len(documents)} new documents to the ChromaDB...")
        vectordb.add_documents(documents)
        vectordb.persist()
        print(f"Successfully added {len(documents)} new documents to the ChromaDB.")
    else:
        print("No new documents to add.")
    
    print("ChromaDB creation and population with job data completed.")

# Function to retrieve documents for a given question and print their summaries and headlines
def retrieve_and_print_documents_for_question(question, db_directory, k=5):
    print(f"Retrieving documents for the question: {question}...")
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)

    # Retrieve documents from the vector database
    retrieved_documents = vectordb.max_marginal_relevance_search(question, k=k)
    
    # Compile and print the results
    compiled_results = f"Question: {question}\n\n"
    
    for j, doc in enumerate(retrieved_documents):
        compiled_results += f"Document {j+1}:\n"
        compiled_results += f"Title: {doc.metadata.get('title')}\n"
        compiled_results += f"Summary: {doc.page_content}\n\n"
    
    # Print the compiled results
    print(compiled_results)

# Function to check for duplicates in the original data
def check_for_duplicates(file_path):
    print(f"Checking for duplicates in {file_path}...")
    with open(file_path, 'r') as file:
        job_data = json.load(file)

    unique_jobs = set(job['jobPostingInfo']['id'] for job in job_data)
    print(f"Original jobs: {len(job_data)}, Unique jobs: {len(unique_jobs)}")
    
    id_counts = Counter(job['jobPostingInfo']['id'] for job in job_data)
    duplicate_ids = {job_id: count for job_id, count in id_counts.items() if count > 1}

    print(f"Duplicate job IDs and their counts:")
    for job_id, count in duplicate_ids.items():
        print(f"{job_id}: {count}")
    
    print("\nSample duplicated jobs:")
    sample_duplicates = [job for job in job_data if id_counts[job['jobPostingInfo']['id']] > 1]
    for i, job in enumerate(sample_duplicates[:10]):  # Print a sample of 10 duplicates
        print(f"Sample {i+1}:")
        print(f"id: {job['jobPostingInfo']['id']}")
        print(f"Title: {job['jobPostingInfo']['title']}")
        print()
    
    print(f"Total jobs: {len(job_data)}")
    print(f"Total unique jobs: {len(set(job['jobPostingInfo']['id'] for job in job_data))}")
    print(f"Number of duplicate jobs: {len(job_data) - len(set(job['jobPostingInfo']['id'] for job in job_data))}")

# Function to get unique files (IDs) from the vector database and check for duplicates
def get_unique_files(db_directory):
    print(f"Getting unique files from the vector database at {db_directory}...")
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    print("\nEmbedding keys:", vectordb.get().keys())
    total_docs = len(vectordb.get()["ids"])
    print("\nNumber of embedded docs:", total_docs)

    # Print the list of source files
    file_list = []

    for x in range(total_docs):
        doc = vectordb.get()["metadatas"][x]
        source = doc["id"]  # Using 'id' as the unique identifier
        file_list.append(source)

    # Count occurrences of each file ID
    url_counts = Counter(file_list)
    unique_list = list(set(file_list))
    duplicate_urls = {url: count for url, count in url_counts.items() if count > 1}

    print(f"\nTotal unique documents: {len(unique_list)}")
    print(f"Number of duplicate documents: {total_docs - len(unique_list)}\n")

    if duplicate_urls:
        print("Duplicate IDs and their counts:")
        for url, count in duplicate_urls.items():
            print(f"{url}: {count}")

    print("\nList of unique files in db:\n")
    for unique_file in unique_list:
        print(unique_file)


# Example usage (comment out if running in script form)
#create_chroma_db('cleaned_job_details.json', './chroma_db_jobs_new')
#retrieve_and_print_documents_for_question("Java Jobs", './chroma_db_jobs_new')
#check_for_duplicates('cleaned_job_details.json')
get_unique_files('./chroma_db_jobs_new')
