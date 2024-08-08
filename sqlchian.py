# SQL Chain with Stream lit UI
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

# Load environment variables from .env file
load_dotenv()

# Access api keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

# Load the CSV data
df = pd.read_csv("it_consulting_crm_data_long_descriptions.csv")

# Display the CSV data
st.title("LangChain + Streamlit Conversational UI")
st.write("### CRM Data")
st.dataframe(df)

# Initialize the overall_chain only once and store it in session state
if "overall_chain" not in st.session_state:

    # Create SQL DB
    engine = create_engine("sqlite:///crm.db")
    df.to_sql("crm", engine, if_exists='replace', index=False)
    db = SQLDatabase(engine=engine)

    # Vector DB persistence
    chroma_db_dir = 'chroma_db'
    os.makedirs(chroma_db_dir, exist_ok=True)
    embedding = OpenAIEmbeddings()
    # Check if ChromaDB already exists
    if os.listdir(chroma_db_dir):
        vectordb = Chroma(persist_directory=chroma_db_dir, embedding_function=embedding)
    else:
        loader = CSVLoader(file_path='it_consulting_crm_data_long_descriptions.csv', source_column="CustomerName")
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        docs = text_splitter.split_documents(data)
        vectordb = Chroma.from_documents(documents=docs, embedding=embedding, persist_directory=chroma_db_dir)
        vectordb.persist()

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # Building Chains
    prompt_sqlLLM = """
    System: You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct SQL query to run, then look at the results of the query and return the answer.
    Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.

    You MUST double check your query before returning it.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    If the question is related to the database, but doesn't require a SQL query, and can be answered by an LLM and RAG.
    We have a RAG database with the csv data of the database, but we are using a SQL database as the RAG semantic query wouldn't work with stuff that
    need aggregated querying, and all. So in this case, return a SQL query that can be run, but just outputs the table name.

    The source in our RAG db, is the customer name, so the query should always select the customerName as one of the columns.

    If you are trying to find a project or detail using text matching, make sure to not full in the Exact Match or Case Sensitivity issues.

    If the question does not seem related to the database, just return "I don't know" as the answer.

    Below we also attach the chat history. Keep that in mind, along with original question to come up with a relevant query to answer the question.

    Here is the database schema:
    table: [('crm',)]
    crm table details: [(0, 'CustomerName', 'TEXT', 0, None, 0), (1, 'Sector', 'TEXT', 0, None, 0), (2, 'Theme', 'TEXT', 0, None, 0), (3, 'CompanySize', 'TEXT', 0, None, 0), (4, 'ContactName', 'TEXT', 0, None, 0), (5, 'ProjectName', 'TEXT', 0, None, 0), (6, 'ProjectStatus', 'TEXT', 0, None, 0), (7, 'ProjectDescription', 'TEXT', 0, None, 0)]

    Here are some general examples of user inputs and their corresponding SQL queries:

    User input: List all artists.
    SQL query: SELECT * FROM Artist;

    User input: How many employees are there?
    SQL query: SELECT COUNT(*) FROM Employee;

    User input: How many tracks are there in the album with ID 5?
    SQL query: SELECT COUNT(*) FROM Track WHERE AlbumId = 5;

    User input: List all tracks in the 'Rock' genre.
    SQL query: SELECT * FROM Track WHERE GenreId = (SELECT GenreId FROM Genre WHERE Name = 'Rock');

    User input: Which albums are from the year 2000?
    SQL query: SELECT * FROM Album WHERE YEAR(ReleaseDate) = 2000;

    Your output should be a single SQL query that can be run. No prepending it with 'SQL query: '.
    User Question: {question}
    Chat History: {chat_history}
    """
    template = ChatPromptTemplate.from_template(prompt_sqlLLM)
    chainSQLquery = LLMChain(llm=llm, prompt=template, output_key="sqlQuery")

    # Run Database chain
    def runDBQuery(inputs):
        sqlQuery = inputs["sqlQuery"]
        dbResult = db.run(sqlQuery)
        return {"dbResult": dbResult}
    runDBQuery_chain = TransformChain(input_variables=["sqlQuery"], output_variables=["dbResult"], transform=runDBQuery)

    # Retrieve Context Chain
    def retrieveContext(inputs):
        question = inputs["question"]
        dbResult = inputs["dbResult"]
        queryVectorDB = question + ".." + dbResult
        vectordbResult = vectordb.similarity_search(queryVectorDB, k=7)
        return {"vectordbResult": vectordbResult}
    retrieveContext_chain = TransformChain(input_variables=["question", "dbResult"], output_variables=["vectordbResult"], transform=retrieveContext)

    # Rag Chain
    rag_prompt = """
    Use the following pieces of information (SQL database result by another LLM based on the same question you are receiving, and RAG result of the database result & question concatenated) to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. 
    Keep the answers concise. Keep in mind that the SQL result, if any, would be the result of a SQL query aggregated over the entire table, and can thereby be more appropriate to use in related questions that are aggregate based. 

    Also, keep in mind that there may be follow up questions. For them, refer to chat history to answer correctly.

    In your response, do not ever make it seem like we ran a SQL query to get the answer.
    SQL Result: {dbResult}
    Context: {vectordbResult}
    Question: {question}
    Chat History: {chat_history}
    Helpful Answer:
    """
    templateRAG = ChatPromptTemplate.from_template(rag_prompt)
    chainRAG = LLMChain(llm=llm, prompt=templateRAG, output_key="answer")

    # Memory Unit
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    overall_chain = SequentialChain(
        chains=[chainSQLquery, runDBQuery_chain, retrieveContext_chain, chainRAG],
        input_variables=["question"],
        verbose=True,
        memory=memory
    )

    st.session_state.overall_chain = overall_chain


def run_chain(question):
    result = st.session_state.overall_chain.invoke({"question": question})
    return result["answer"], result["chat_history"]

# Initialize session state for chat history if it doesn't exist
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Input box for user to type their question
user_input = st.chat_input("Type your message here...")

# If the user presses Enter
if user_input:
    # Append user's message to chat history
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    
    # Get response from the assistant
    response, chat_history = run_chain(user_input)
    
    # Append assistant's response to chat history
    st.session_state.chat_history.append(AIMessage(content=response))

# Display the chat history
for message in st.session_state.chat_history:
    role = "User" if isinstance(message, HumanMessage) else "Assistant"
    with st.chat_message(role):
        st.markdown(f"**{role}:** {message.content}")
