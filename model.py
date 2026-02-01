import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Scommentare per utilizzo di Mistral
# from langchain_mistralai import ChatMistralAI 

load_dotenv()

# --- OPZIONE A: GROQ (Default - Veloce + buon Free Tier) ---
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("ERRORE: Manca la GROQ_API_KEY nel file .env")

llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.3-70b-versatile"
)

# --- OPZIONE B: MISTRAL AI (Fallback) ---
# Per usare questo:
# 1. pip install langchain-mistralai
# 2. MISTRAL_API_KEY nel file .env
# 3. scommentare sotto:

# if not os.environ.get("MISTRAL_API_KEY"):
#     raise ValueError("ERRORE: Manca la MISTRAL_API_KEY nel file .env")

# llm = ChatMistralAI(
#     model="mistral-large-latest",  # Consigliato per logica complessa (Router/Planner)
#     # model="open-mixtral-8x22b",  # Alternativa open source molto forte ed economica
#     temperature=0
# )