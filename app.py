# Correct Version is sqlchain.py

import streamlit as st
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.chains import TransformChain
from langchain.chains import SequentialChain
from langchain.memory import ConversationBufferMemory

# Load environment variables from .env file
load_dotenv()

# Access API keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

# Setup Database
engine = create_engine("sqlite:///crm.db")
db = SQLDatabase(engine=engine)

# Setup Vector DB
loader = CSVLoader(file_path='it_consulting_crm_data_long_descriptions.csv', source_column="CustomerName")
data = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
docs = text_splitter.split_documents(data)

embedding = OpenAIEmbeddings()
vectordb = Chroma.from_documents(documents=docs, embedding=embedding)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# SQL Query Generator Chain
prompt_sqlLLM = """System: You are an agent designed to interact with a SQL database.
... (rest of your prompt) ...
User Question: {question}
Chat History: {chat_history}"""
template = ChatPromptTemplate.from_template(prompt_sqlLLM)
chainSQLquery = LLMChain(llm=llm, prompt=template, output_key="sqlQuery")

# Run Database Chain
def runDBQuery(inputs):
    sqlQuery = inputs["sqlQuery"]
    dbResult = db.run(sqlQuery)
    return {"dbResult": dbResult}
runDBQuery_chain = TransformChain(input_variables=["sqlQuery"], output_variables=["dbResult"], transform=runDBQuery)

# Retrieve Context Chain
def retreiveContext(inputs):
    question = inputs["question"]
    dbResult = inputs["dbResult"]
    queryVectorDB = question + ".." + dbResult
    vectordbResult = vectordb.similarity_search(queryVectorDB, k=3)
    return {"vectordbResult": vectordbResult}
retretiveContext_chain = TransformChain(input_variables=["question", "dbResult"], output_variables=["vectordbResult"], transform=retreiveContext)

# RAG Chain
rag_prompt = """Use the following pieces of information ... (rest of your prompt) ..."""
templateRAG = ChatPromptTemplate.from_template(rag_prompt)
chainRAG = LLMChain(llm=llm, prompt=templateRAG, output_key="answer")

# Memory Unit
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Overall Chain
overall_chain = SequentialChain(chains=[chainSQLquery, runDBQuery_chain, retretiveContext_chain, chainRAG], input_variables=["question"], verbose=True, memory=memory)

# Streamlit UI
st.title("LangChain + Streamlit Conversational UI")
question = st.text_input("Enter your question:")
if st.button("Ask"):
    if question:
        result = overall_chain({"question": question})
        st.write(result["answer"])
