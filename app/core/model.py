import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Uncomment to use Mistral.
# from langchain_mistralai import ChatMistralAI 

load_dotenv()

# --- OPTION A: GROQ (Default - fast + solid free tier) ---
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("ERRORE: Manca la GROQ_API_KEY nel file .env")

llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.3-70b-versatile"
)

# --- OPTION B: MISTRAL AI (Fallback) ---
# To use this:
# 1. pip install langchain-mistralai
# 2. Add MISTRAL_API_KEY to .env
# 3. Uncomment below:

# if not os.environ.get("MISTRAL_API_KEY"):
#     raise ValueError("ERRORE: Manca la MISTRAL_API_KEY nel file .env")

# llm = ChatMistralAI(
#     model="mistral-large-latest",  # Recommended for complex routing/planning logic
#     # model="open-mixtral-8x22b",  # Strong open-source alternative
#     temperature=0
# )
