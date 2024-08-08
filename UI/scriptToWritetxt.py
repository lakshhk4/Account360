import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.utilities import SQLDatabase
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain, TransformChain, SequentialChain
from langchain.memory import ConversationBufferMemory
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Access api keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def get_all_headlines(db_directory):

    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    # Retrieve all headlines
    headlines = []
    for x in range(len(vectordb.get()["ids"])):
        doc = vectordb.get()["metadatas"][x]
        headline = doc["basic_headline"]  # Assuming 'basic_headline' contains the headline
        headlines.append(headline)

    # Concatenate all headlines into a single string
    all_headlines = "\n".join(headlines)
    return all_headlines

def get_all_titles(db_directory):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    # Retrieve all titles
    titles = []
    for x in range(len(vectordb.get()["ids"])):
        doc = vectordb.get()["metadatas"][x]
        title = doc.get("title", "Unknown Title")
        titles.append(title)

    # Concatenate all titles into a single string
    all_titles = "\n".join(titles)
    
    return all_titles

def write_headlines_to_file(file_path, headlines):
    with open(file_path, 'w') as file:
        file.write("Headlines:\n")
        file.write(headlines)

def write_titles_to_file(file_path, titles):
    with open(file_path, 'w') as file:
        file.write("Titles:\n")
        file.write(titles)


reuters_db_path = '/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/reuters/chroma_db_reuters'
jobs_db_path = '/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/workday/chroma_db_jobs_new'

# Get headlines and titles
headlines = get_all_headlines('/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/reuters/chroma_db_reuters')

# Write the outputs to two separate text files
headlines_file_path = 'headlines_output.txt'
titles_file_path = 'titles_output.txt'
write_headlines_to_file(headlines_file_path, headlines)
titles = get_all_titles(jobs_db_path)
write_titles_to_file(titles_file_path, titles)

print("Data written to files successfully.")