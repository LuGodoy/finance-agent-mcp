#____________VERSÃO ___________________
import streamlit as st
import os
from dotenv import load_dotenv
from llm.client_gemini import FinanceAgent

import logging

# ------------------ Configuração básica ------------------

logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(
    page_title="Gestor de Gastos",
    page_icon="💰"
)

MAX_HISTORY = 3  # número máximo de mensagens no chat

# ------------------ Cache do Agente ------------------

@st.cache_resource
def get_finance_agent():
    #api_key = os.getenv("GROQ_API_KEY", "")
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.error("Chave da API do GEMINI não encontrada")
        st.stop()
    return FinanceAgent(api_key)

agent = get_finance_agent()

# ------------------ CSS ------------------

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

BASE_DIR = os.path.dirname(__file__)
local_css(os.path.join(BASE_DIR, "styles.css"))

# ------------------ Header ------------------

st.markdown(
    '<h1 class="main-title">Agente de Gestão Financeira Familiar 💰</h1>',
    unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-text">Controle suas finanças com inteligência.</p>',
    unsafe_allow_html=True
)
st.divider()

# ------------------ Histórico ------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------------------ Input ------------------

if prompt := st.chat_input("Qual a dúvida sobre seus gastos?"):

    # Usuário
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistente
    with st.chat_message("assistant"):
        with st.spinner("Consultando inteligência financeira..."):
            try:
                response_text = agent.ask_question(prompt)
                st.markdown(response_text)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text}
                )

                # 🔥 Limita histórico
                st.session_state.messages = st.session_state.messages[-MAX_HISTORY:]

            except Exception as e:
                logger.error(e)

                error_msg = str(e)

                if "429" in error_msg:
                    st.error(
                        "Limite de requisições atingido. Aguarde alguns segundos."
                    )

                elif "503" in error_msg or "UNAVAILABLE" in error_msg:
                    st.warning(
                        "Serviço de IA temporariamente indisponível. Tente novamente em instantes."
                    )

                else:
                    st.error(
                        "Erro na aplicação. Tente novamente."
                    )

