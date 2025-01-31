import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("ERRORE: Manca la GROQ_API_KEY nel file .env")

llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")