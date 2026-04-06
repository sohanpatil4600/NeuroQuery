import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm(model_type=None):
    """
    Returns an LLM instance. 
    Prioritizes Groq if GROQ_API_KEY is available, otherwise falls back to OpenAI.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Check for direct override via env
    preferred = os.getenv("PREFERRED_LLM", "groq").lower()
    
    if preferred == "openai" and openai_key:
        print("[LLM-FACTORY] Using OpenAI (Preferred)")
        return ChatOpenAI(model="gpt-4o", openai_api_key=openai_key)
    
    if groq_key and groq_key != "your_groq_key":
        print("[LLM-FACTORY] Using Groq (High Speed)")
        return ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key)
    
    if openai_key:
        print("[LLM-FACTORY] Falling back to OpenAI")
        return ChatOpenAI(model="gpt-4o", openai_api_key=openai_key)
    
    print("[LLM-FACTORY] WARNING: No LLM API keys found!")
    return None
