# ____________VERSÃO ___________________
import logging
import os
import traceback

import streamlit as st
from dotenv import load_dotenv

from llm.client_gemini import FinanceAgent

# ------------------ Configuração básica ------------------

logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(page_title="Assistente de Gastos", page_icon="💰", layout="centered")

MAX_HISTORY = 6  # número máximo de mensagens no chat

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
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


BASE_DIR = os.path.dirname(__file__)
local_css(os.path.join(BASE_DIR, "styles.css"))

# ------------------ Header ------------------

st.markdown(
    '<h1 class="main-title">Agente de Gestão Financeira 💰</h1>', unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-text">Controle suas finanças com inteligência.</p>', unsafe_allow_html=True
)
st.divider()

USER_AVATAR = "assets/user.png"#"https://cdn-icons-png.flaticon.com/512/6833/6833605.png"
AI_AVATAR = "assets/bot.png" #"https://cdn-icons-png.flaticon.com/512/4712/4712035.png"
# ------------------ Histórico ------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    current_avatar = USER_AVATAR if message["role"] == "user" else AI_AVATAR
    with st.chat_message(message["role"], avatar=current_avatar):
        st.markdown(message["content"])

# ------------------ Input ------------------

if prompt := st.chat_input("Qual a dúvida sobre seus gastos?"):
    # Usuário 🧑‍💻
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Assistente "🤖"
    with st.chat_message("assistant", avatar=AI_AVATAR):
        with st.spinner("Consultando inteligência financeira..."):
            try:
                response_text = agent.ask_question(prompt)
                st.markdown(response_text)

                st.session_state.messages.append({"role": "assistant", "content": response_text})

                # 🔥 Limita histórico
                st.session_state.messages = st.session_state.messages[-MAX_HISTORY:]



            except Exception as e:
                # 1. Log detalhado para o desenvolvedor (no terminal)
                error_trace = traceback.format_exc()
                logger.error(f"Erro detectado: {error_trace}")

                error_msg = str(e).upper() # Normaliza para facilitar a busca

                # 2. Tratamento específico por tipo de erro
                if "429" in error_msg or "QUOTA_EXCEEDED" in error_msg:
                    st.error("🚀 **Limite atingido:** Muitas perguntas em pouco tempo. Aguarde 1 minuto.")

                elif "503" in error_msg or "UNAVAILABLE" in error_msg:
                    st.warning("☁️ **Serviço instável:** O servidor da IA está sobrecarregado. Tente de novo agora.")

                elif "AUTHENTICATION" in error_msg or "API_KEY" in error_msg:
                    st.error("🔑 **Erro de Chave:** Problema na autenticação com a API. Verifique as credenciais.")

                elif "SAFETY" in error_msg:
                    st.info("🛡️ **Filtro de Conteúdo:** A IA não pôde responder por políticas de segurança.")

                elif "CONNECTION" in error_msg.lower():
                    st.error("🌐 **Erro de Conexão:** Verifique sua internet.")

                else:
                    # Exibe um resumo do erro real para ajudar no debug rápido
                    st.error(f"💥 **Erro inesperado:** {type(e).__name__}")
                    st.info(f"Detalhe: {str(e)[:100]}...") # Mostra os primeiros 100 caracteres do erro
