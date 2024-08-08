# generate questions with project files
# generate questions without project file names

# Single chain
import json
import os
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
import openai
from langchain.chat_models import ChatOpenAI
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


current_dir = os.path.dirname(__file__)
relative_path = os.path.join(current_dir, 'chroma_db_internal_data')
db_directory = os.path.normpath(relative_path)

def get_all_filenames(db_directory):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)
    
    # Retrieve all filenames
    filenames = []
    for x in range(len(vectordb.get()["ids"])):
        doc = vectordb.get()["metadatas"][x]
        full_path = doc.get("source", "Unknown Filename")
        filename = os.path.basename(full_path)
        filenames.append(filename)
    
    all_filenames = "\n".join(filenames)
    return all_filenames
file_names = get_all_filenames(db_directory)

questionGenerationPromptFileNames = """

We are an IT consulting company aiming to better understand our clients and potential clients to enhance our services and increase our chances of winning bids. We have a vector database containing various internal project documents related to the Samsung Health project. These documents include emails, meeting notes, project plans, testing documents, and design documents. The project involves developing and integrating enhanced health tracking features, such as sleep monitoring, heart rate analysis, stress detection, and activity recognition, into the Samsung Health app and Galaxy Watch. The goal is to improve user engagement and provide personalized health insights while ensuring robust data security and privacy.

Your task is to generate insightful questions to query this vector database. The objective is to extract relevant information that can help us understand project outcomes, client needs, potential improvements, and future opportunities. Here are the details of the stored data format:

Data Format:

Page Content: "document content"
Metadata:
- ID: Unique identifier for the document
- Source: File path of the document

Example Data:
        "id": "DOC123",
        "source": "/path/to/document.txt",
        "content": "The document discusses the integration of various health monitoring features into Samsung's wearable devices. It highlights the successful completion of the project and the improved device functionality and user satisfaction."

Instructions:
Generate 5 questions that would help us extract valuable insights from the vector database.
Focus on understanding project outcomes, client feedback, areas for improvement, and potential future opportunities.
Ensure the questions are specific, actionable, and relevant to an IT consulting firm's perspective.
Included below are the filenames of the documents that are in the database. Use this to help with question generation.

File Names = {filenames}

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "What were the key outcomes of the Samsung Health Integration project, and how did they meet client expectations?"
      ],
      [
        "question": "What feedback did the client provide on the project, and what areas were identified for improvement?"
      ],
      [
        "question": "How did the integration of health tracking features impact user engagement and satisfaction?"
      ],
      [
        "question": "What challenges were encountered during the project, and how were they addressed?"
      ],
      [
        "question": "What future opportunities can be identified from the project's outcomes and client feedback?"
      ]
    )
  ]

"""

questionGenerationPrompt = """

We are an IT consulting company aiming to better understand our clients and potential clients to enhance our services and increase our chances of winning bids. We have a vector database containing various internal project documents related to the Samsung Health project. These documents include emails, meeting notes, project plans, testing documents, and design documents. The project involves developing and integrating enhanced health tracking features, such as sleep monitoring, heart rate analysis, stress detection, and activity recognition, into the Samsung Health app and Galaxy Watch. The goal is to improve user engagement and provide personalized health insights while ensuring robust data security and privacy.

Your task is to generate insightful questions to query this vector database. The objective is to extract relevant information that can help us understand project outcomes, client needs, potential improvements, and future opportunities. Here are the details of the stored data format:

Data Format:

Page Content: "document content"
Metadata:
- ID: Unique identifier for the document
- Source: File path of the document

Example Data:
        "id": "DOC123",
        "source": "/path/to/document.txt",
        "content": "The document discusses the integration of various health monitoring features into Samsung's wearable devices. It highlights the successful completion of the project and the improved device functionality and user satisfaction."

Instructions:
Generate 5 questions that would help us extract valuable insights from the vector database.
Focus on understanding project outcomes, client feedback, areas for improvement, and potential future opportunities.
Ensure the questions are specific, actionable, and relevant to an IT consulting firm's perspective.

Please generate questions in a plain JSON format (I've put [] instead of curly braces in examples. I've also put () where it should actually be []) that can be indexed into and actually asked to the Chroma DB by another chain.
Output should look exactly like below format, except the bracket replacements given. [] to curly, and () to []

Example output:
  [
    "questions": (
      [
        "question": "What were the key outcomes of the Samsung Health Integration project, and how did they meet client expectations?"
      ],
      [
        "question": "What feedback did the client provide on the project, and what areas were identified for improvement?"
      ],
      [
        "question": "How did the integration of health tracking features impact user engagement and satisfaction?"
      ],
      [
        "question": "What challenges were encountered during the project, and how were they addressed?"
      ],
      [
        "question": "What future opportunities can be identified from the project's outcomes and client feedback?"
      ]
    )
  ]

"""

def retrieve_and_compile_documents_internal(question, db_directory, k=5):
    # Initialize the vector database
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(persist_directory=db_directory, embedding_function=embedding)

    # Retrieve documents from the vector database
    retrieved_documents = vectordb.max_marginal_relevance_search(question, k=k)
    
    # Compile and print the results
    compiled_results = "\n"
    
    for j, doc in enumerate(retrieved_documents):
        compiled_results += f"Document {j+1}:\n"
        compiled_results += f"Source: {doc.metadata.get('source')}\n"
        compiled_results += f"Content: {doc.page_content}\n\n"
    
    # Print the compiled results
    return compiled_results

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# Question generation with filenames
template = ChatPromptTemplate.from_template(questionGenerationPromptFileNames)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="questions")
questions_llm_output_filenames = chainQuestionGeneration.invoke(input={file_names})

# Question generation without filenames
template = ChatPromptTemplate.from_template(questionGenerationPrompt)
chainQuestionGeneration = LLMChain(llm=llm, prompt=template, output_key="questions")
questions_llm_output = chainQuestionGeneration.invoke(input={})

json_str = questions_llm_output['questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions = [item['question'] for item in data['questions']]
json_str = questions_llm_output_filenames['questions'].replace('```json', '').replace('```', '').strip()
data = json.loads(json_str)
questions_headlines = [item['question'] for item in data['questions']]
for question in questions_headlines:
    questions.append(question)

print(questions)
compiled_all_results = ""
for i, question in enumerate(questions):
    compiled_all_results += f"Question {i+1}: {question}\n\n"
    compiled_all_results += retrieve_and_compile_documents_internal(question, db_directory)
    compiled_all_results += "\n\n"

print("compiled results")
print(compiled_all_results)
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


generateInsightsPrompt = """"

Task:

You are an advanced AI assistant working for an IT consulting company. The goal is to synthesize insights from the provided information about the Samsung Health project to help the company better understand their client and potential future projects. These insights will be used to improve service offerings, win bids, and make informed strategic decisions.

Project Context:

The project involves developing and integrating enhanced health tracking features, such as sleep monitoring, heart rate analysis, stress detection, and activity recognition, into the Samsung Health app and Galaxy Watch. The goal is to improve user engagement and provide personalized health insights while ensuring robust data security and privacy.

Data Format:

The vector database contains various internal project documents, such as emails, meeting notes, project plans, testing documents, and design documents. Each document includes metadata such as the document type, project name, author, date, status, and source (file path).

Instructions:

1. **Analyze the Information**:
   - Review the content and metadata provided for each document.
   - Identify key themes, patterns, and trends related to the project.

2. **Synthesize Insights**:
   - Combine the information from multiple documents to form comprehensive insights.
   - Highlight any important observations, potential opportunities, and challenges faced during the project.

3. **Generate Actionable Recommendations**:
   - Provide specific recommendations for the IT consulting company based on the synthesized information.
   - Ensure the insights are actionable and relevant to the company's goals of better serving Samsung and winning future bids.

Format:

For each question, provide the following:

1. **Question**:
2. **Synthesized Insights**:
3. **Actionable Recommendations**:

Example Output:

**Question 1**:
What were the key outcomes of the Samsung Health project, and how did they meet client expectations?

**Synthesized Insights**:
The project successfully integrated advanced health tracking features into the Samsung Health app and Galaxy Watch, resulting in improved user engagement and satisfaction. The sleep monitoring and heart rate analysis features were particularly well-received, with users reporting more accurate and helpful health insights.

**Actionable Recommendations**:
1. Continue to enhance and refine health tracking features based on user feedback.
2. Explore additional health metrics that could be integrated into future updates.
3. Ensure ongoing improvements to data security and privacy to maintain user trust.

Provide your response in a structured format, with clear and concise insights and recommendations based on the provided project data.

Here is the compiled project information:
{compiled_all_results}

Here are all the document filenames:
{filenames}

"""

template = ChatPromptTemplate.from_template(generateInsightsPrompt)
chainInsightGeneration = LLMChain(llm=llm, prompt=template, output_key="insights")
response = chainInsightGeneration.invoke(input={"compiled_all_results": compiled_all_results, "filenames": file_names})
print(response["insights"])

current_dir = os.path.dirname(__file__)
relative_path = os.path.join(current_dir, '../UI/insights_outputs')
output_directory = os.path.normpath(relative_path)

output_file_path = os.path.join(output_directory, "insights_internal.md")

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