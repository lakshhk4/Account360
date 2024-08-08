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
import subprocess
import sys

# Load environment variables from .env file
load_dotenv()

# Access api keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def retrieve_and_compile_workday_documents(question, db_directory, k=5):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)

    # Retrieve documents from the vector database
    retrieved_documents = vectordb.max_marginal_relevance_search(question, k=k)
    
    # Compile the results into a large string
    compiled_results = "\n"
    
    for j, doc in enumerate(retrieved_documents):
        compiled_results += f"Job Document {j+1}:\n"
        compiled_results += f"ID: {doc.metadata.get('id')}\n"
        compiled_results += f"Title: {doc.metadata.get('title')}\n"
        compiled_results += f"Location: {doc.metadata.get('location')}\n"
        compiled_results += f"Posted On: {doc.metadata.get('postedOn')}\n"
        compiled_results += f"Start Date: {doc.metadata.get('startDate')}\n"
        compiled_results += f"Job Req ID: {doc.metadata.get('jobReqId')}\n"
        compiled_results += f"Job Posting ID: {doc.metadata.get('jobPostingId')}\n"
        compiled_results += f"Job Posting Site ID: {doc.metadata.get('jobPostingSiteId')}\n"
        compiled_results += f"Country: {doc.metadata.get('country')}\n"
        compiled_results += f"Remote Type: {doc.metadata.get('remoteType')}\n"
        compiled_results += f"External URL: {doc.metadata.get('externalUrl')}\n"
        compiled_results += f"Questionnaire ID: {doc.metadata.get('questionnaireId')}\n"
        compiled_results += f"Job Description: {doc.page_content}\n\n"
    
    return compiled_results

def retrieve_and_compile_documents_reuters(question, db_directory, k=5):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)

    # Retrieve documents from the vector database
    retrieved_documents = vectordb.max_marginal_relevance_search(question, k=k)
    
    # Compile the results into a large string
    compiled_results = "\n"
    
    for j, doc in enumerate(retrieved_documents):
        compiled_results += f"Document {j+1}:\n"
        compiled_results += f"basic_headline: {doc.metadata.get('basic_headline')}\n"
        compiled_results += f"title: {doc.metadata.get('title')}\n"
        compiled_results += f"description: {doc.metadata.get('description')}\n"
        compiled_results += f"web: {doc.metadata.get('web')}\n"
        compiled_results += f"published_time: {doc.metadata.get('published_time')}\n"
        compiled_results += f"content: {doc.page_content}\n\n"
    
    return compiled_results

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

# context
    # insights 1, 2, 3
    # answer q
    # get info from all 3.
    # know which info would be more reliable.
    # answer
    # memory

# question is inputted

# all 2-3 databases are queried

def query_news(inputs):
    question = inputs["question"]
    compiled_results_news = ""
    compiled_results_news += retrieve_and_compile_documents_reuters(question,"/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/reuters/chroma_db_reuters",k=5)
    return {"news_docs": compiled_results_news}

def query_jobs(inputs):
    question = inputs["question"]
    compiled_results_job = ""
    compiled_results_job += retrieve_and_compile_workday_documents(question,"/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/workday/chroma_db_jobs_new",k=5)
    return {"job_docs": compiled_results_job}

# answer question. using content and queried results

run_query_news = TransformChain(input_variables=["question"], output_variables=["news_docs"], transform=query_news)
run_query_jobs = TransformChain(input_variables=["question"], output_variables=["job_docs"], transform=query_jobs)


with open("/Users/lakshhkhatri/Desktop/WiproProject/UI/insights_outputs/insights_reuters.md") as source:
    llm_news_insights = source.read()

with open("/Users/lakshhkhatri/Desktop/WiproProject/UI/insights_outputs/insights_workday.md") as source:
    llm_jobs_insights = source.read()

with open("/Users/lakshhkhatri/Desktop/WiproProject/UI/insights_outputs/insights_internal.md") as source:
    llm_internal_insights = source.read()

#headlines = get_all_headlines('/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/reuters/chroma_db_reuters')
#titles = get_all_titles("/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/workday/chroma_db_jobs_new")


# Faster method for testing to populate headlines and titles
def read_from_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

headlines = read_from_file('headlines_output.txt')
titles = read_from_file('titles_output.txt')

promptBuilder = f"""
Welcome to the Samsung Account Intelligence Dashboard! You are the QnA bot of this dashboard.

The entire tool is designed to provide comprehensive insights and actionable intelligence on Samsung's business environment by analyzing news articles and job postings. Our goal is to empower users with up-to-date information to make informed decisions and stay ahead in the competitive landscape.

You are an advanced AI assistant working for an IT consulting company that has Samsung as their client or aims to acquire them as a client. Your mission is to serve as a QnA bot that helps gather insights and answer follow-up questions on pre-LLM-generated insights.

Instructions to the Chatbot:

The insights gathered include:
- Key news highlights affecting Samsung from Reuters sources.
- Trends and patterns in job postings related to Samsung, including hiring spikes, new roles, and emerging skill requirements.
- Internal insights on a project the IT company is doing for Samsung, including analysis of emails, meeting notes, and design plans for developing advanced health tracking features for the Samsung Health app and Galaxy Watch

When a user asks a follow-up question, consider the context provided by the initial insights.

You will automatically be provided relevant documents from the news and jobs databases that pertain to the specific question asked by the user. Use these documents to generate a coherent and detailed response that addresses the user's query.

For every question asked, you will receive 5 documents from both the news and jobs databases. However, for questions requiring aggregation or quantification across the entire database (e.g., "How many ML jobs does Samsung have open?"), use the "All headlines from the News Database" and "All job titles from the Jobs Database" sections provided below. Do not rely on the top 5 retrieved documents for these types of questions.

Ultimately, you are receiving all this information to help answer the input question. Remember that you only receive the top 5 documents pertaining to the question from the databases, so never use that information for aggregation type questions. For those, use the headlines and titles.

Example Chats:

**Example 1: Aggregation Question**

**User:** How many ML jobs does Samsung currently have posted?

**AI:** There are x ML jobs currently posted by Samsung.

*Explanation: The AI should use the "All job titles from the Jobs Databasec" to count the number of jobs related to 'ML' (Machine Learning) and provide the total count.*

**Example 2: Specific Query About a News Article**

**User:** What are the recent developments in Samsung's semiconductor division?

**AI:** According to the latest news, Samsung's semiconductor division has announced a significant increase in investment for their new fabrication plant in Texas. Additionally, there have been reports of strategic partnerships with several tech firms to enhance their semiconductor manufacturing capabilities.

*Explanation: The AI should use the top 5 documents retrieved from the news database to provide detailed and relevant information about the specific query.*

**Example 3: Specific Job Query**

**User:** What new roles is Samsung hiring for in the AI department?

**AI:** Samsung is currently hiring for several new roles in the AI department, including AI Research Scientist, Machine Learning Engineer, and AI Product Manager. These positions are primarily located in their Seoul and Silicon Valley offices, with a focus on developing advanced AI technologies and solutions.

*Explanation: The AI should use the top 5 documents retrieved from the jobs database to provide detailed information about the specific roles Samsung is hiring for in the AI department.*

Inputs:
Pre-Generated LLM insights on Latest Samsung News: {llm_news_insights}
Pre-Generated LLM insights on Latest Samsung Jobs: {llm_jobs_insights}
Pre-Generated LLM insights on Latest Samsung Internal Project Data: {llm_internal_insights}
All headlines from the News Database: {headlines}
All job titles from the Jobs Database: {titles}

"""

prompt = promptBuilder + "\n" + """
Actual Question: {question}

Chat History: {chat_history}

Use the chat history in mind to better understand the actual question

KEEP IN MIND THAT BELOW ARE ONLY 5 of numerous results from the databases. These are the top 5 results of a similarity search with the 'actual question'. For any question that requires aggregation or quantification across the entire database, like "how many ML jobs does samsung have open?", use the "All headlines from the News Database" and "All job titles from the Jobs Database" fields provided above.

5 Documents retrieved from News DB pertaining to the question: {news_docs}
5 Documents retrieved from Jobs DB pertaining to the question: {job_docs}
"""

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

template = ChatPromptTemplate.from_template(prompt)
chain_qa = LLMChain(llm=llm, prompt = template, output_key = "answer")
overall_chain = SequentialChain(
    chains = [run_query_news, run_query_jobs, chain_qa],
    input_variables = ["question"],
    verbose = True,
    memory = memory
)



#print(overall_chain.invoke("What is the CHIPS act?"))
#print(overall_chain.invoke("How many ML jobs does Samsung currently have posted?"))

#print(overall_chain.invoke("Tell me the title of each of them?"))

# Set the page configuration
st.set_page_config(layout="wide")
st.title("Account Intelligence Dashboard")

# Read and apply custom CSS
with open("design.css") as source:
    st.markdown(f"<style>{source.read()}</style>", unsafe_allow_html=True)

# Load LLM output from file
with open("/Users/lakshhkhatri/Desktop/WiproProject/UI/insights_outputs/insights_reuters.md") as source:
    llm_news_insights = source.read()

with open("/Users/lakshhkhatri/Desktop/WiproProject/UI/insights_outputs/insights_workday.md") as source:
    llm_jobs_insights = source.read()

# Initialize session state for overall_chain and chat history if not already done
if "overall_chain" not in st.session_state:
    st.session_state.overall_chain = overall_chain

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Create the main layout with columns
main_col, chat_col = st.columns([5, 2])

with main_col:
    col1, col2 = st.columns(2)
    with col1:
        st.header("News Insight")
        st.markdown(f"<div class='stScrollable'>{llm_news_insights}</div>", unsafe_allow_html=True)
    with col2:
        st.header("Jobs Insight")
        st.markdown(f"<div class='stScrollable'>{llm_jobs_insights}</div>", unsafe_allow_html=True)
    st.markdown("<div class='stContainer'></div>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.header("Internal Data Insights")
        st.markdown(f"<div class='stScrollable'>{llm_internal_insights}</div>", unsafe_allow_html=True)
    with col4:
        st.header("CRM Insights")
        st.write("CRM Insights content goes here")

    if st.button("Generate Insights"):
        #scripts = ["/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/workday/workday_insights.py", "/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/reuters/reuters_insights.py", "/Users/lakshhkhatri/Desktop/WiproProject/Mock project Data/internal_data_insights.py"]
        #scripts = ["/Users/lakshhkhatri/Desktop/WiproProject/UI /testingButton.py"]
        #scripts = ["/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/reuters/reuters_insights.py","/Users/lakshhkhatri/Desktop/WiproProject/scrapingTester/workday/workday_insights.py"]
        scripts = ["/Users/lakshhkhatri/Desktop/WiproProject/Mock project Data/internal_data_insights.py"]
        print("runnign from ui ")
        for script in scripts:
            result = subprocess.run([sys.executable, script], capture_output=True, text=True)
            st.write(result.stdout)
            if result.stderr:
                st.write(f"Error in {script}:", result.stderr)
        
        #with open("newsOutput.md") as source:
        #    llm_news_insights = source.read()

        #with open("/Users/lakshhkhatri/Desktop/WiproProject/UI /insights_outputs/insights_workday.md") as source:
        #    llm_jobs_insights = source.read()

        st.experimental_rerun()

with chat_col:
    with st.container(border=True, height=700):
        st.header("Chat Window")

        # Use st.chat_input for user input
        user_input = st.chat_input("Type your message here...")

        # If the user presses Enter
        if user_input:
            # Append user's message to chat history
            st.session_state.chat_history.append(HumanMessage(content=user_input))
            
            # Get response from the assistant
            response = st.session_state.overall_chain.invoke({"question": user_input})["answer"]
            
            # Append assistant's response to chat history
            st.session_state.chat_history.append(AIMessage(content=response))

        # Display the chat history in a scrollable container
        
        st.markdown("<div class='stChatContainer'>", unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            role = "User" if isinstance(message, HumanMessage) else "Assistant"
            with st.chat_message(role):
                st.markdown(f"**{role}:** {message.content}")
        
        st.markdown("</div>", unsafe_allow_html=True)

