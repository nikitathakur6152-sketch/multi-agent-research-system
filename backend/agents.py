from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.rate_limiters import InMemoryRateLimiter
from tools import web_search, scrape_url
import os
from dotenv import load_dotenv
load_dotenv()
#model setup
# Override MISTRAL_MODEL in .env if your Mistral account uses a different model.
# The shared 14B model limit shown for this organization is 0.50 requests/second.
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.45,
    check_every_n_seconds=0.1,
    max_bucket_size=1,
)
llm = ChatMistralAI(
    model=os.getenv("MISTRAL_MODEL", "ministral-14b-2512"),
    temperature=0,
    rate_limiter=rate_limiter,
    timeout=60,
    max_retries=1,
)
# first agent
def build_search_agent():
   return create_agent(
       model=llm,
         tools=[web_search]
   )
#second agent
def build_reader_agent():
   return create_agent(
       model=llm,
         tools=[scrape_url]
   )


#writer chain
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

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

#critic_chain 

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
