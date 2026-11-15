from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

def call_llm(temperature: float) -> ChatGroq:

    return ChatGroq(api_key= os.environ["LLM_KEY"], model=os.environ["LLM_MODEL"], temperature=temperature)

