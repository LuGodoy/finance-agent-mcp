import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


# logger = logging.getLogger(__name__)
def sanitize_identifier(name: str) -> str:
    if not name:
        return ""
    return name.replace("`", "")

# 2. Variáveis limpas exportadas para todo o projeto
DB_NAME = sanitize_identifier(os.getenv("DB_NAME", ""))
TABLE_NAME = sanitize_identifier(os.getenv("TABLE_NAME", ""))

load_dotenv(dotenv_path=".env")

def validate_env():
    """Verifica se todas as variáveis obrigatórias estão presentes."""
    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME", "TABLE_NAME"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(f"Erro: Variáveis de ambiente ausentes no .env: {', '.join(missing)}")

# Chamamos a validação assim que o módulo é importado
validate_env()

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME"),
}


def create_connection():
    """Cria e retorna uma conexão com o banco de dados MYSQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            # logger.info("Conexão ao MySQL bem sucedida")
            return conn

    except Error:
        # logger.info(f"Erro ao conectar com MYSQL: {e}")
        return None
