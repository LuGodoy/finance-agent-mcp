import os

from dotenv import load_dotenv
from google import genai

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

# 2. Pega a chave da variável de ambiente
api_key = os.getenv("GEMINI_API_KEY")

# 3. Passa explicitamente para o Client
client = genai.Client(api_key=api_key)

for model in client.models.list():
    # Usamos "or []" para garantir que, se for None, vire uma lista vazia
    # E verificamos se supported_actions existe antes de iterar
    actions = model.supported_actions or []

    if "generateContent" in actions:
        print(f"ID: {model.name}")
