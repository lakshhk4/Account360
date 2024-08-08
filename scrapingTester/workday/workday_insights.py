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

# Directory
# ./chroma_db_jobs_new

# Load environment variables from .env file
load_dotenv()

# Access API keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

# Define prompts for question generation
questionGenerationPromptTitles = """
We are an IT consulting company aiming to better understand our clients and potential clients to enhance our services and increase our chances of winning bids. We have a vector database containing summarized job postings about Samsung jobs, including metadata such as job title, location, posting date, and job description.

Your task is to generate insightful questions to query this vector database. The objective is to extract relevant information that can help us understand industry trends, market needs, competitive landscape, and potential opportunities. Here are the details of the stored data format:

Data Format:

Page Content: "job description"
Metadata:
Title: title
Location: location
Posted On: postedOn
Start Date: startDate
Job Req Id: jobReqId
Job Posting Id: jobPostingId
Job Posting Site Id: jobPostingSiteId
Country: country
Remote Type: remoteType
External URL: externalUrl
Questionnaire Id: questionnaireId

Example Data:
        "id": "9fad3ee8c07110059142042189230000",
        "title": "Key Account Manager Healthcare - Netherlands",
        "jobDescription": "Position Summary\nSamsung Electronics Benelux is seeking an experienced Key Account Manager to join its Healthcare Division (Health & Medical Equipment - HME). Do you have what it takes to join Samsung? Let\u2019s build the future, apply now!\nRole and Responsibilities\nYour role\nIn this role, you will be responsible for creating and developing long-term relationships with customers and our partners in the Netherlands. Your focus is to maximize order intake, sales and customer satisfaction, whilst developing and optimizing the customer relationship in order to ensure the long-term business growth in the region. As a Key Account Manager, you will be responsible for our entire Healthcare portfolio, including Ultrasound, DR and Healthcare IT solutions.\nYour responsibilities\nFulfilment of targets (sales, margin, price realization, market share, NPS) \nIdentifies and builds strong and lasting business relationships with all key decision makers (clinical, technical, administrative/economic), key opinion leaders and society board members in all accounts \nChannel Management: Directly managing Distributors to develop a business plan and strategy that creates new business opportunities in existing and new accounts\nDeveloping a country/area business plan in line with corporate guidelines and objectives that maximizes potential and opportunity, for the current year and the foreseeable future\nContinuous monitoring of the competition, trends and market landscape and developing strategies to improve sales and increase market share\nMonitor market trends, competitor activity, and industry developments to identify opportunities and threats, and adjust sales strategies accordingly.\nSystematically analyzing and reporting of sales results, expectations, market, competition and trends for the optimal operational planning and/or optimal product portfolio decisions. \nResponsible for organizing and executing Marketing events in the Netherlands, including workshops, symposiums, courses, etcetera\nSupporting the creation of Marketing collaterals, including success stories, white papers, use cases and customer testimonials\nSkills and Qualifications\nYour skills and qualifications\n(Requirements)\nBachelor's degree in Business Administration, Sales, Marketing, or a related field\nSales & marketing experience in the area of ultrasound or medical imaging\nLeading complex sales & business development projects and driving growth, and holding a substantial turnover responsibility\nExperience in the radiology, gynaecology and/or obstetrics markets, both public and private\nDeep understanding of the public tender process and key influencer leverage skills\nExperiences in KOL (Key Opinion Leader) management and major clinical/medical society engagement\nExcellent communication and interpersonal skills, with the ability to build and maintain relationships with key stakeholders\nAnalytical and strategic thinking skills, with the ability to identify trends, analyze data, and develop effective sales strategies\nFluency in Dutch and English is required, French is a plus.\nYour competencies\n(Requirements)\nTeam player\nCustomer-focused and results-driven\nCan-do, hands-on mentality\nProactive attitude, bias for action\nAbility to prioritize\nOrganised\nPreferred qualifications\n(Advantages)\nClinical expertise in ultrasound and/or radiography\nClinical application specialist expertise\nSolution and product knowledge: understanding customer needs and our solutions\nExperience with working with multiple cultures. Open mind and respect towards cultural differences.\nVertical network at all levels of the organizations from C level to procurement. Strong understanding of their needs and business models and requirements. Knowledge of the partners active in a specific segment.\nAbout us\nOur story begins in 1969, when Samsung saw the light of day with the ambition to help people achieve the impossible. After more than 50 years, we are still innovating and creating boundless technology that helps people make the impossible possible. We remain driven by our purpose, which is why we put people and what they care about at the center of everything we create.\nWe do this by staying true to our global values.\nHuman experiences (We put people first, at the center of everything we do).\nProgressive Innovation (We are constantly finding new ways to improve the way people live by creating inventive products and services).\nRebellious Optimism (We challenge ourselves and the status quo to change the world).\nIntegrity & transparency (We always strive to do the right thing by being open and honest with our customers and partner ecosystem).\nSocial improvement (We believe that technology should benefit everyone. It should be accessible, sustainable and used for good).\nAre you the \nKey Account Manager Healthcare \nwe are looking for? If so, apply immediately and start your application process by clicking the apply button below. Let\u2019s kick-start your career!\n* Please visit Samsung membership to see Privacy Policy, which defaults according to your location, at: \nhttps://account.samsung.com/membership/policy/privacy\n. You can change Country/Language at the bottom of the page. If you are European Economic Resident, please click \nhere\n:\n \nhttps://europe-samsung.com/ghrp/PrivacyNoticeforEU.html"

Instructions:
Generate 5 questions that would help us extract valuable insights from the vector database.
Focus on understanding industry trends, market dynamics, competitive strategies, and potential business opportunities.
Ensure the questions are specific, actionable, and relevant to an IT consulting firm's perspective.
Included below are the titles of the job postings that are in the database. Use this to help with question generation.

Titles: {titles}

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "What are the recent trends in job postings for account management roles and how do they align with market demands?"
      ],
      [
        "question": "How do the responsibilities outlined in job postings for sales and marketing roles reflect current industry trends and customer needs?"
      ]
    )
  ]
"""

questionGenerationPrompt = """

We are an IT consulting company aiming to better understand our clients and potential clients to enhance our services and increase our chances of winning bids. We have a vector database containing summarized job postings about Samsung jobs, including metadata such as job title, location, posting date, and job description.

Your task is to generate insightful questions to query this vector database. The objective is to extract relevant information that can help us understand industry trends, market needs, competitive landscape, and potential opportunities. Here are the details of the stored data format:

Data Format:

Page Content: "job description"
Metadata:
Title: title
Location: location
Posted On: postedOn
Start Date: startDate
Job Req Id: jobReqId
Job Posting Id: jobPostingId
Job Posting Site Id: jobPostingSiteId
Country: country
Remote Type: remoteType
External URL: externalUrl
Questionnaire Id: questionnaireId

Example Data:
        "id": "9fad3ee8c07110059142042189230000",
        "title": "Key Account Manager Healthcare - Netherlands",
        "jobDescription": "Position Summary\nSamsung Electronics Benelux is seeking an experienced Key Account Manager to join its Healthcare Division (Health & Medical Equipment - HME). Do you have what it takes to join Samsung? Let\u2019s build the future, apply now!\nRole and Responsibilities\nYour role\nIn this role, you will be responsible for creating and developing long-term relationships with customers and our partners in the Netherlands. Your focus is to maximize order intake, sales and customer satisfaction, whilst developing and optimizing the customer relationship in order to ensure the long-term business growth in the region. As a Key Account Manager, you will be responsible for our entire Healthcare portfolio, including Ultrasound, DR and Healthcare IT solutions.\nYour responsibilities\nFulfilment of targets (sales, margin, price realization, market share, NPS) \nIdentifies and builds strong and lasting business relationships with all key decision makers (clinical, technical, administrative/economic), key opinion leaders and society board members in all accounts \nChannel Management: Directly managing Distributors to develop a business plan and strategy that creates new business opportunities in existing and new accounts\nDeveloping a country/area business plan in line with corporate guidelines and objectives that maximizes potential and opportunity, for the current year and the foreseeable future\nContinuous monitoring of the competition, trends and market landscape and developing strategies to improve sales and increase market share\nMonitor market trends, competitor activity, and industry developments to identify opportunities and threats, and adjust sales strategies accordingly.\nSystematically analyzing and reporting of sales results, expectations, market, competition and trends for the optimal operational planning and/or optimal product portfolio decisions. \nResponsible for organizing and executing Marketing events in the Netherlands, including workshops, symposiums, courses, etcetera\nSupporting the creation of Marketing collaterals, including success stories, white papers, use cases and customer testimonials\nSkills and Qualifications\nYour skills and qualifications\n(Requirements)\nBachelor's degree in Business Administration, Sales, Marketing, or a related field\nSales & marketing experience in the area of ultrasound or medical imaging\nLeading complex sales & business development projects and driving growth, and holding a substantial turnover responsibility\nExperience in the radiology, gynaecology and/or obstetrics markets, both public and private\nDeep understanding of the public tender process and key influencer leverage skills\nExperiences in KOL (Key Opinion Leader) management and major clinical/medical society engagement\nExcellent communication and interpersonal skills, with the ability to build and maintain relationships with key stakeholders\nAnalytical and strategic thinking skills, with the ability to identify trends, analyze data, and develop effective sales strategies\nFluency in Dutch and English is required, French is a plus.\nYour competencies\n(Requirements)\nTeam player\nCustomer-focused and results-driven\nCan-do, hands-on mentality\nProactive attitude, bias for action\nAbility to prioritize\nOrganised\nPreferred qualifications\n(Advantages)\nClinical expertise in ultrasound and/or radiography\nClinical application specialist expertise\nSolution and product knowledge: understanding customer needs and our solutions\nExperience with working with multiple cultures. Open mind and respect towards cultural differences.\nVertical network at all levels of the organizations from C level to procurement. Strong understanding of their needs and business models and requirements. Knowledge of the partners active in a specific segment.\nAbout us\nOur story begins in 1969, when Samsung saw the light of day with the ambition to help people achieve the impossible. After more than 50 years, we are still innovating and creating boundless technology that helps people make the impossible possible. We remain driven by our purpose, which is why we put people and what they care about at the center of everything we create.\nWe do this by staying true to our global values.\nHuman experiences (We put people first, at the center of everything we do).\nProgressive Innovation (We are constantly finding new ways to improve the way people live by creating inventive products and services).\nRebellious Optimism (We challenge ourselves and the status quo to change the world).\nIntegrity & transparency (We always strive to do the right thing by being open and honest with our customers and partner ecosystem).\nSocial improvement (We believe that technology should benefit everyone. It should be accessible, sustainable and used for good).\nAre you the \nKey Account Manager Healthcare \nwe are looking for? If so, apply immediately and start your application process by clicking the apply button below. Let\u2019s kick-start your career!\n* Please visit Samsung membership to see Privacy Policy, which defaults according to your location, at: \nhttps://account.samsung.com/membership/policy/privacy\n. You can change Country/Language at the bottom of the page. If you are European Economic Resident, please click \nhere\n:\n \nhttps://europe-samsung.com/ghrp/PrivacyNoticeforEU.html"

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
        "question": "What are the recent trends in job postings for account management roles and how do they align with market demands?"
      ],
      [
        "question": "How has the job market for IT roles changed in response to competitive pressures from other tech companies?"
      ]
    )
  ]

"""

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

# Not optimal. Tried to do imports. but dint work.
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

# Not optimal. Tried to do imports but dint work.
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

# workday db path
current_dir = os.path.dirname(__file__)
workday_db_path = os.path.join(current_dir,'chroma_db_jobs_new')
workday_db_path = os.path.normpath(workday_db_path)
#reuters db path
current_dir = os.path.dirname(os.path.abspath(__file__))
relative_path = os.path.join(current_dir, '../reuters/chroma_db_reuters')
reuters_db_path = os.path.normpath(relative_path)

headlines = get_all_headlines(reuters_db_path)
titles = get_all_titles(workday_db_path)
print(len(titles))
print(len(headlines))

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Question generation with titles
template = ChatPromptTemplate.from_template(questionGenerationPromptTitles)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="questions")
questions_llm_output_titles = chainQuestionGeneration.invoke(input={titles})

template = ChatPromptTemplate.from_template(questionGenerationPrompt)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="questions")
questions_llm_output = chainQuestionGeneration.invoke(input={})

json_str = questions_llm_output['questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions = [item['question'] for item in data['questions']]

json_str = questions_llm_output_titles['questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions_titles = [item['question'] for item in data['questions']]

for question in questions_titles:
    questions.append(question)

# questions has all the questions. compile results for all questions
compiled_all_results = ""
db_directory = workday_db_path
for i, question in enumerate(questions):
    compiled_all_results += f"Question {i+1}: {question}\n\n"
    compiled_all_results += retrieve_and_compile_workday_documents(question, db_directory)
    compiled_all_results += "\n\n"

# Extract and track retrieved document IDs
doc_ids = []
for line in compiled_all_results.split('\n'):
    if line.startswith("ID:"):
        doc_id = line.split("ID: ")[1]
        doc_ids.append(doc_id)

# Store the document IDs in a set to ensure uniqueness
unique_doc_ids = set(doc_ids)

# Print the total number of retrieved documents and the number of distinct documents
print(f"Total retrieved documents: {len(doc_ids)}")
print(f"Number of distinct documents: {len(unique_doc_ids)}")

generateInsightsPrompt = """
Task:

You are an advanced AI assistant working for an IT consulting company that has Samsung as their client or wants them to become one. The goal is to synthesize insights from the provided information about Samsung's job postings and recruitment process to help the company better understand their client's hiring strategies and potential workforce trends. These insights will be used to improve the IT consulting company's service offerings, win bids, and make informed strategic decisions.

Context:

You have been provided with a series of questions and corresponding documents retrieved from a vector database. Each document contains detailed job postings and metadata from Samsung's Workday job portal. Your task is to analyze these documents and generate coherent and actionable insights.

You are also provided with a compiled entry of questions and relevant documents related to Samsung's recruitment strategies and job market trends, extracted from recent news articles. This is located under 'Cross Reference Info'

You are also provided with the titles of all job postings in the database

Instructions:

Analyze the Information:

Review the job postings and metadata provided for each question.
Identify key themes, patterns, and trends in Samsung's recruitment strategies.
Synthesize Insights:

Combine the information from multiple documents to form comprehensive insights.
Highlight any important observations, potential opportunities, and challenges in Samsung's hiring process.
Generate Actionable Insights:

Provide specific recommendations for the IT consulting company based on the synthesized information.
Ensure the insights are actionable and relevant to the company's goals of better serving Samsung and winning bids.
Format:

For each question, provide the following:

Question:
Synthesized Insights:
Actionable Recommendations for the IT Consulting Company:
Example Output:

Question 1:
What are the current trends in Samsung's job postings for software engineers, and how do they align with industry demands?

Synthesized Insights:
Based on the recent job postings, Samsung is heavily recruiting software engineers with expertise in AI and machine learning. This aligns with the industry's growing focus on integrating advanced AI capabilities into products and services. Additionally, Samsung is offering remote work options, indicating a shift towards more flexible working conditions, which is in line with the broader industry trend.

Actionable Recommendations for the IT Consulting Company:

Develop Customized AI Solutions: Propose customized AI and machine learning solutions that align with Samsung's recruitment focus, showcasing how these solutions can enhance their product offerings.
Offer Remote Work Consulting: Provide consulting services to help Samsung optimize remote work policies and infrastructure, ensuring they can attract and retain top talent.
Create Training and Development Programs: Design and implement training programs to upskill Samsung's current workforce in AI and machine learning, ensuring their teams stay competitive and innovative.
Enhance Recruitment Platforms: Suggest improvements or develop platforms that can streamline Samsung's recruitment process, particularly for remote roles and specialized positions in AI and machine learning.

Here is the questions and relevant job documents = {compiled_all_results}

Here is also all titles from the db = {titles}

Here is the 'Cross Reference Info': {cross_reference_info}
"""

template = ChatPromptTemplate.from_template(generateInsightsPrompt)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="insights")
# Have a step where we query the other db. 5Q
# cross reference
generateJobRelevantQuestionsPrompt = """
Task:

You are an advanced AI assistant working for an IT consulting company. The goal is to generate insightful questions that can be used to query a vector database containing news articles and summaries about Samsung's hiring and recruitment strategies. These questions should help the company better understand Samsung's hiring strategies, workforce trends, and the broader market context.

Context:

You have been provided with job titles and corresponding documents retrieved from Samsung's Workday job portal. To enhance the insights, you need to generate questions that will be used to query a vector database containing news articles about Samsung's hiring and recruitment strategies.

Instructions:

Generate five questions that focus on gathering job-relevant information from the news database. Ensure the questions are specific, actionable, and relevant to understanding Samsung's recruitment strategies and market trends.
You are also provided the job titles, and headlines from the news database. Use that to help come up with your questions.

Here are the job titles: {job_titles}

Here are the headlines from the news database: {headlines}

Format:

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "What are the recent trends in Samsung's recruitment strategies"
      ],
      [
        "question": "How is Samsung addressing the talent gap in the tech industry as reported in recent news"
      ]
    )
  ]
"""
templateGenerateJobRelevantQuestions = ChatPromptTemplate.from_template(generateJobRelevantQuestionsPrompt)
chainJobRelevantQuestionGeneration = LLMChain(llm=llm, prompt=templateGenerateJobRelevantQuestions, output_key="cross_ref_questions")
questions_llm_output_cross_ref = chainJobRelevantQuestionGeneration.invoke(input={"job_titles": titles, "headlines": headlines})
json_str = questions_llm_output_cross_ref['cross_ref_questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions_cross_ref = [item['question'] for item in data['questions']]

# Get Docs for Q's:
compiled_all_results_cross_ref = ""
db_directory = reuters_db_path
for i, question in enumerate(questions_cross_ref):
    compiled_all_results_cross_ref += f"Question {i+1}: {question}\n\n"
    compiled_all_results_cross_ref += retrieve_and_compile_documents_reuters(question, db_directory)
    compiled_all_results_cross_ref += "\n\n"
# end cross ref
print("cross ref")
print(compiled_all_results_cross_ref)

response = chainQuestionGeneration.invoke(input={"compiled_all_results": compiled_all_results, "titles": titles, "cross_reference_info": compiled_all_results_cross_ref})
print(response["insights"])



current_dir = os.path.dirname(__file__)
relative_path = os.path.join(current_dir, '../../UI/insights_outputs')
output_directory = os.path.normpath(relative_path)
output_file_path = os.path.join(output_directory, "insights_workday.md")

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