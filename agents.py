from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY")
)


# 1st Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools = [web_search]
    )
    
# 2nd Agent
def build_reader_agent():
    return create_agent(
        model = llm,
        tools = [scrape_url]
    )


# Prompt used by pipeline + UI to force the reader agent to scrape a real URL
def build_reader_prompt(topic: str, search_results: str) -> str:
    return (
        "You are the Reader Agent. Your job is to pick ONE most relevant URL from the "
        "search results and scrape it using the scrape_url tool.\n\n"
        "Rules:\n"
        "1. You MUST call the scrape_url tool with a real URL taken from the Search Results below.\n"
        "2. Prefer an official docs page, reputable news article, or primary source over aggregators.\n"
        "3. Do not ask the user for more information. Do not refuse. Use the URLs already provided.\n"
        "4. After scraping, summarize the deepest useful content you obtained.\n\n"
        f"Topic: {topic}\n\n"
        "Search Results:\n"
        f"{search_results}\n"
    )
    

# writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.
     
     Topic: {topic}
     
     Research Gathered:
     {research}
     
     Structure the report as:
     - Introduction
     - Key Findings (minimum 3 well-explained points)
     - Conclusion
     - Sources (list all URLs found in the research)
     
     Be Detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

# critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
     
     Report: {report}
     
     Respond in this exact format:
     
     Score: x/10
     
     Strengths: 
     - ...
     - ...
     
     One line verdict:
     ...
     """),
])

critic_chain = critic_prompt | llm | StrOutputParser()