# Install necessary libraries
import json
import os
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from collections import Counter
from dotenv import load_dotenv

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
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    # Load Reuters data from JSON file
    with open(file_path, 'r') as file:
        reuters_data = json.load(file)
    
    # Get existing document IDs to avoid re-adding documents
    existing_ids = get_existing_document_ids(vectordb)
    
    # Convert Reuters data to Langchain Document objects
    documents = []
    for article in reuters_data:
        if article['id'] not in existing_ids:
            document = Document(
                page_content=article['content'],
                metadata={
                    'id': article['id'],
                    'canonical_url': article['canonical_url'],
                    'basic_headline': article['basic_headline'],
                    'title': article['title'],
                    'description': article['description'],
                    'web': article['web'],
                    'published_time': article['published_time']
                }
            )
            documents.append(document)
    
    # Add new documents to the vector store
    if documents:
        vectordb.add_documents(documents)
        vectordb.persist()
        print(f"Added {len(documents)} new documents to the ChromaDB.")
    else:
        print("No new documents to add.")
    
    print("ChromaDB has been successfully created and populated with the Reuters data.")

# Function to retrieve documents for a given question and print their summaries and headlines
def retrieve_and_print_documents_for_question(question, db_directory, k=5):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)

    # Retrieve documents from the vector database
    retrieved_documents = vectordb.max_marginal_relevance_search(question, k=k)
    
    # Compile and print the results
    compiled_results = f"Question: {question}\n\n"
    
    for j, doc in enumerate(retrieved_documents):
        compiled_results += f"Document {j+1}:\n"
        compiled_results += f"Headline: {doc.metadata.get('basic_headline')}\n"
        compiled_results += f"Summary: {doc.page_content}\n\n"
    
    # Print the compiled results
    print(compiled_results)

# Function to check for duplicates in the original data
def check_for_duplicates(file_path):
    with open(file_path, 'r') as file:
        reuters_data = json.load(file)

    unique_articles = set(article['id'] for article in reuters_data)
    print(f"Original articles: {len(reuters_data)}, Unique articles: {len(unique_articles)}")
    
    url_counts = Counter(article['id'] for article in reuters_data)
    duplicate_urls = {url: count for url, count in url_counts.items() if count > 1}

    print(f"Duplicate URLs and their counts:")
    for url, count in duplicate_urls.items():
        print(f"{url}: {count}")
    
    print("\nSample duplicated articles:")
    sample_duplicates = [article for article in reuters_data if url_counts[article['id']] > 1]
    for i, article in enumerate(sample_duplicates[:10]):  # Print a sample of 10 duplicates
        print(f"Sample {i+1}:")
        print(f"id: {article['id']}")
        print(f"Summary: {article['summary']}")
        print()
    
    print(f"Total articles: {len(reuters_data)}")
    print(f"Total unique articles: {len(set(article['id'] for article in reuters_data))}")
    print(f"Number of duplicate articles: {len(reuters_data) - len(set(article['id'] for article in reuters_data))}")

# Function to get unique files (URLs) from the vector database
# Function to get unique files (URLs) from the vector database and check for duplicates
def get_unique_files(db_directory):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    print("\nEmbedding keys:", vectordb.get().keys())
    print("\nNumber of embedded docs:", len(vectordb.get()["ids"]))

    # Print the list of source files
    file_list = []
    duplicates = []

    for x in range(len(vectordb.get()["ids"])):
        doc = vectordb.get()["metadatas"][x]
        source = doc["canonical_url"]  # Using 'canonical_url' instead of 'url'
        if source in file_list:
            duplicates.append(source)
        file_list.append(source)

    # Set only stores a value once even if it is inserted more than once.
    list_set = set(file_list)
    unique_list = list(list_set)

    print("\nList of unique files in db:\n")
    for unique_file in unique_list:
        print(unique_file)
    
    if duplicates:
        print("\nDuplicates found:\n")
        for duplicate in duplicates:
            print(duplicate)
    else:
        print("\nNo duplicates found.")

# Example usage:
# db_directory = "path_to_your_db_directory"
# get_unique_files(db_directory)


# Example usage (comment out if running in script form)
#create_chroma_db('updated_articles.json', './chroma_db_reuters')
#retrieve_and_print_documents_for_question("NVIDIA news", './chroma_db_reuters')
# check_for_duplicates('updated_articles.json')
get_unique_files('./chroma_db_reuters')
#get_existing_document_ids("./chroma_db_reuters")