# Install necessary libraries
import json
import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
import openai
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import re

# Load environment variables from .env file

load_dotenv()

# Access API keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

questionGenerationPromptHeadlines = """

We are an IT consulting company aiming to better understand our clients and potential clients to enhance our services and increase our chances of winning bids. We have a vector database containing summarized news articles about Samsung, including metadata such as authors, publication date, type, and URL.

Your task is to generate insightful questions to query this vector database. The objective is to extract relevant information that can help us understand industry trends, market needs, competitive landscape, and potential opportunities. Here are the details of the stored data format:

Data Format:

Page Content: "headline & summary"
Metadata:
Authors: authors
Eyebrow: eyebrow
Headline: headline
Published At: publishedAt
Subtype: subtype
Thumbnail: thumbnail
Type: type
URL: url

Example Data:
        "id": "IY3HU3XTNNM2NO4JMWNVUMDB7M",
        "canonical_url": "/technology/micron-set-get-6-billion-chip-grants-us-bloomberg-reports-2024-04-17/",
        "basic_headline": "Micron set to get $6.1 bln in chip grants from US",
        "title": "Micron set to get $6.1 bln in chip grants from US",
        "description": "Memory chip maker Micron Technology is set to receive $6.1 billion in grants from the U.S. Commerce Department to help pay for domestic chip factory projects, Democratic U.S. Senate Majority Leader Chuck Schumer said on Thursday.",
        "web": "Micron set to get $6.1 bln in chip grants from US",
        "headline_feature": null,
        "published_time": "2024-04-17T23:30:37.403Z",
        "content": "April 18 (Reuters) - Memory chip maker Micron Technology (MU.O)   is set to receive $6.1 billion in grants from the U.S. Commerce Department to help pay for domestic chip factory projects, Democratic U.S. Senate Majority Leader Chuck Schumer said on Thursday. The award, which is not yet finalized, will fund chipmaking facilities in New York and Idaho from the CHIPS & Science law, the New York senator said in a statement. \u201cThis monumental and historic federal investment will power and propel Micron to bring its transformative $100+ billion four-fab project in central New York to life, creating an estimated 50,000 jobs,\u201d he said. Micron plans to build a complex of chip plants in New York over the next 20 years, the senator added. The news caps off a string of Chips Act grants announced by the Biden administration in recent weeks as the United States seeks to reduce reliance on China and Taiwan and supercharge its own lagging chip production. The U.S. share of global semiconductor manufacturing capacity has fallen from 37% in 1990 to 12% in 2020, according to the Semiconductor Industry Association (SIA). Lawmakers have warned that U.S. dependence on chips manufactured in Taiwan by the world's top contract chip manufacturer, TSMC (2330.TW)  , is risky because China claims the self-governed island as its territory and has reserved the right to use force to retake it. Intel won $8.5 billion in grants last month while Taiwan's TSMC clinched $6.6 billion in April to build out its American production. Samsung followed this week with a $6.4 billion award to boost production in Texas. The historic Chips Act allocates $52.6 billion to support the sector. The Commerce Department is dedicating $28 billion for government subsidies for advanced chips manufacturing - although it has more than $70 billion in requests - and also has $75 billion in lending authority. New York Governor Kathy Hochul said in a statement that the largest private investment in American history is on its way to Central New York."

Instructions:
Generate 5 questions that would help us extract valuable insights from the vector database.
Focus on understanding industry trends, market dynamics, competitive strategies, and potential business opportunities.
Ensure the questions are specific, actionable, and relevant to an IT consulting firm's perspective.
Included below are the headlines of the articles that are in the database. Use this to help with question generation.

Headlines: {headlines}

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "What are the recent trends in Samsung's product launches and how do they align with market demands?"
      ],
      [
        "question": "How has Samsung's market positioning changed in response to competitive pressures from other tech companies?"
      ]
    )
  ]
"""

questionGenerationPrompt = """



We are an IT consulting company aiming to better understand our clients and potential clients to enhance our services and increase our chances of winning bids. We have a vector database containing summarized news articles about Samsung, including metadata such as authors, publication date, type, and URL.

Your task is to generate insightful questions to query this vector database. The objective is to extract relevant information that can help us understand industry trends, market needs, competitive landscape, and potential opportunities. Here are the details of the stored data format:

Data Format:

Page Content: "headline & summary"
Metadata:
Authors: authors
Eyebrow: eyebrow
Headline: headline
Published At: publishedAt
Subtype: subtype
Thumbnail: thumbnail
Type: type
URL: url

Example Data:
        "id": "IY3HU3XTNNM2NO4JMWNVUMDB7M",
        "canonical_url": "/technology/micron-set-get-6-billion-chip-grants-us-bloomberg-reports-2024-04-17/",
        "basic_headline": "Micron set to get $6.1 bln in chip grants from US",
        "title": "Micron set to get $6.1 bln in chip grants from US",
        "description": "Memory chip maker Micron Technology is set to receive $6.1 billion in grants from the U.S. Commerce Department to help pay for domestic chip factory projects, Democratic U.S. Senate Majority Leader Chuck Schumer said on Thursday.",
        "web": "Micron set to get $6.1 bln in chip grants from US",
        "headline_feature": null,
        "published_time": "2024-04-17T23:30:37.403Z",
        "content": "April 18 (Reuters) - Memory chip maker Micron Technology (MU.O)   is set to receive $6.1 billion in grants from the U.S. Commerce Department to help pay for domestic chip factory projects, Democratic U.S. Senate Majority Leader Chuck Schumer said on Thursday. The award, which is not yet finalized, will fund chipmaking facilities in New York and Idaho from the CHIPS & Science law, the New York senator said in a statement. \u201cThis monumental and historic federal investment will power and propel Micron to bring its transformative $100+ billion four-fab project in central New York to life, creating an estimated 50,000 jobs,\u201d he said. Micron plans to build a complex of chip plants in New York over the next 20 years, the senator added. The news caps off a string of Chips Act grants announced by the Biden administration in recent weeks as the United States seeks to reduce reliance on China and Taiwan and supercharge its own lagging chip production. The U.S. share of global semiconductor manufacturing capacity has fallen from 37% in 1990 to 12% in 2020, according to the Semiconductor Industry Association (SIA). Lawmakers have warned that U.S. dependence on chips manufactured in Taiwan by the world's top contract chip manufacturer, TSMC (2330.TW)  , is risky because China claims the self-governed island as its territory and has reserved the right to use force to retake it. Intel won $8.5 billion in grants last month while Taiwan's TSMC clinched $6.6 billion in April to build out its American production. Samsung followed this week with a $6.4 billion award to boost production in Texas. The historic Chips Act allocates $52.6 billion to support the sector. The Commerce Department is dedicating $28 billion for government subsidies for advanced chips manufacturing - although it has more than $70 billion in requests - and also has $75 billion in lending authority. New York Governor Kathy Hochul said in a statement that the largest private investment in American history is on its way to Central New York."

Instructions:
Generate 5 questions that would help us extract valuable insights from the vector database.
Focus on understanding industry trends, market dynamics, competitive strategies, and potential business opportunities.
Ensure the questions are specific, actionable, and relevant to an IT consulting firm's perspective.

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "What are the recent trends in Samsung's product launches and how do they align with market demands?"
      ],
      [
        "question": "How has Samsung's market positioning changed in response to competitive pressures from other tech companies?"
      ]
    )
  ]
"""
def retrieve_and_compile_documents(question, db_directory, k=5):
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
    
    return all_headlines

current_dir = os.path.dirname(__file__)
reuters_db_path = os.path.join(current_dir, 'chroma_db_reuters')
reuters_db_path = os.path.normpath(reuters_db_path)
headlines = get_all_headlines(reuters_db_path)
print(reuters_db_path)
print(headlines)

# FUNCTIONS FROM WORKDAY FILE

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

current_dir = os.path.dirname(os.path.abspath(__file__))
relative_path = os.path.join(current_dir, '../workday/chroma_db_jobs_new')
workday_db_path = os.path.normpath(relative_path)
titles = get_all_titles(workday_db_path)
# END WORKDAY FILE FUNCTIONS


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# Question generation with headlines
template = ChatPromptTemplate.from_template(questionGenerationPromptHeadlines)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="questions")
questions_llm_output_headlines = chainQuestionGeneration.invoke(input={headlines})

# Question generation without headlines
template = ChatPromptTemplate.from_template(questionGenerationPrompt)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="questions")
questions_llm_output = chainQuestionGeneration.invoke(input={})

json_str = questions_llm_output['questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions = [item['question'] for item in data['questions']]
json_str = questions_llm_output_headlines['questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions_headlines = [item['question'] for item in data['questions']]
for question in questions_headlines:
    questions.append(question)

# questions has all the questions. compile results for all questions
compiled_all_results = ""
db_directory = reuters_db_path
for i, question in enumerate(questions):
    compiled_all_results += f"Question {i+1}: {question}\n\n"
    compiled_all_results += retrieve_and_compile_documents(question, db_directory)
    compiled_all_results += "\n\n"

#print(compiled_all_results)

compiled_headlines = []
for line in compiled_all_results.split('\n'):
    if line.startswith("basic_headline:"):
        headline = line.split("basic_headline: ")[1]
        compiled_headlines.append(headline)

# Store the headlines in a set to ensure uniqueness
compiled_headlines = set(compiled_headlines)

# Print the total number of distinct headlines
print(f"Total headlines: {len(compiled_headlines)}")
print(f"Number of distinct headlines: {len(compiled_headlines)}")

generateInsightsPrompt = """
Task:

You are an advanced AI assistant working for an IT consulting company. The goal is to synthesize insights from the provided information about Samsung to help the company better understand their client and potential clients. These insights will be used to improve service offerings, win bids, and make informed strategic decisions.

Context:

You have been provided with a series of questions and corresponding documents retrieved from a vector database. Each document contains a summary and metadata about Samsung. Your task is to analyze these documents and generate coherent and actionable insights.

You are also provided with a compiled entry of questions and relevant documents related to Samsung's recruitment strategies and job analysis, extracted from a database of their current job openings, their descriptions. This is located under 'Cross Reference Info'

You are also provuded with the headlines of all news articles in the database.

Instructions:

Analyze the Information:

Review the summaries and metadata provided for each question.
Identify key themes, patterns, and trends.
Synthesize Insights:

Combine the information from multiple documents to form comprehensive insights.
Highlight any important observations, potential opportunities, and challenges for Samsung.
Generate Actionable Insights:

Provide specific recommendations for the IT consulting company based on the synthesized information.
Ensure the insights are actionable and relevant to the IT consulting company's goals of better serving Samsung and winning bids.

Format:

For each question, provide the following:

Question:
Synthesized Insights:
Actionable Recommendations:
Example Output:

Question 1:
What are the recent trends in Samsung's product launches and how do they align with market demands?

Synthesized Insights:
Based on the recent product launches, Samsung is focusing heavily on health-tracking features in their new wearables. This aligns with the growing consumer demand for health and fitness technologies. Additionally, Samsung is trying to outpace competitors like Apple by introducing unique features such as metabolic health tracking, which is not yet available in Apple products.

Actionable Recommendations:

Actionable Recommendation 1
Actionable Recommendation 2
Actionable Recommendation 3

Here is the questions and documents = {compiled_all_results}

Here is all the headlines from the news reuters database: {headlines}

Here is the 'Cross Reference Info': {cross_reference_info}:
"""

# Start Cross Reference
generateNewsRelatedJobQuestions = """

Task:

You are an advanced AI assistant working for an IT consulting company. The goal is to generate insightful questions that can be used to query a vector database containing job postings and recruitment information from Samsung. These questions should help the company better understand Samsung's hiring strategies, workforce trends, and the broader market context, which are relevant to the insights provided by the news articles.

Context:

You have been provided with summaries and metadata from news articles about Samsung's hiring and recruitment strategies. To enhance the insights, you need to generate questions that will be used to query a vector database containing job postings and recruitment information from Samsung.

Instructions:

Generate five questions that focus on gathering relevant job-related information from the job postings database. Ensure the questions are specific, actionable, and relevant to understanding Samsung's recruitment strategies and market trends in the context of the news articles.

You have been provided the list of questions that we are going to answer later, and the headlines of news articles in the database. To complement the response generation of these questions, you need to come up with questions to extract information from the aforementioned job database.
You are also provided a list of the job titles in that job database. The database includes job descriptions, and other imporant accompanying metadata: 'id', 'title', 'location', 'postedOn', 'startDate', 'jobReqId', 'jobPostingId', 'jobPostingSiteId', 'country', 'remoteType', 'externalUrl', 'questionnaireId'

Use all this information to come up with questions whose answers will supplement in answering the news data list of questions.

Questions we will answer later: {questions_to_answer}

News Headlines: {headlines}

Job Titles: {titles}

Format:

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "Place Question Here"
      ],
      [
        "question": "Place Question Here"
      ]
    )
  ]
"""

templateGenerateJobQuestions = ChatPromptTemplate.from_template(generateNewsRelatedJobQuestions)
chainJobQuestionGeneration = LLMChain(llm=llm, prompt=templateGenerateJobQuestions, output_key="cross_ref_questions")
questions_llm_output_cross_ref = chainJobQuestionGeneration.invoke(input={"titles": titles, "headlines": headlines, "questions_to_answer": questions})
json_str = questions_llm_output_cross_ref['cross_ref_questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions_cross_ref = [item['question'] for item in data['questions']]

# Get Docs for Q's:
compiled_all_results_cross_ref = ""
db_directory = workday_db_path
for i, question in enumerate(questions_cross_ref):
    compiled_all_results_cross_ref += f"Question {i+1}: {question}\n\n"
    compiled_all_results_cross_ref += retrieve_and_compile_workday_documents(question, db_directory)
    compiled_all_results_cross_ref += "\n\n"

print("cross ref")
print(compiled_all_results_cross_ref)
# ENd cross reference

template = ChatPromptTemplate.from_template(generateInsightsPrompt)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="insights")
response = chainQuestionGeneration.invoke(input={"compiled_all_results": compiled_all_results, "cross_reference_info": compiled_all_results_cross_ref, "headlines": headlines})
print(response["insights"])

current_dir = os.path.dirname(__file__)
relative_path = os.path.join(current_dir, '../../UI/insights_outputs')
output_directory = os.path.normpath(relative_path)

output_file_path = os.path.join(output_directory, "insights_reuters.md")

os.makedirs(output_directory, exist_ok=True)

with open(output_file_path, "w") as file:
    file.write(response["insights"])

print(f"Insights have been written to {output_file_path}")

def process_markdown(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    processed_lines = ["<!---\n\n"]  # Add `<!---` at the very top followed by a newline
    
    # Combine lines where question number and text are on different lines
    i = 0
    while i < len(lines):
        if re.match(r"### Question \d+:\n", lines[i]) and i + 1 < len(lines):
            combined_lines = re.sub(r"### Question (\d+):\n", r"### Question \1: ", lines[i]) + lines[i + 1]
            processed_lines.append(combined_lines)
            i += 2
        else:
            processed_lines.append(lines[i])
            i += 1
    
    with open(file_path, 'w') as file:
        file.writelines(processed_lines)

process_markdown(output_file_path)