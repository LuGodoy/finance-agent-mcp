import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


def sanitize_identifier(name: str) -> str:
    if not name:
        return ""
    return name.replace("`", "")


load_dotenv(dotenv_path=".env")

DB_NAME = sanitize_identifier(os.getenv("DB_NAME", ""))
TABLE_NAME = sanitize_identifier(os.getenv("TABLE_NAME", ""))


def validate_env():
    """Verifica se todas as variáveis obrigatórias estão presentes."""
    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME", "TABLE_NAME"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f"Erro: Variáveis de ambiente ausentes no .env: {', '.join(missing)}"
        )


DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME"),
}


def create_connection():
    """Cria e retorna uma conexão com o banco de dados MYSQL"""

    if not os.getenv("GITHUB_ACTIONS"):
        validate_env()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn

    except Error:
        return None
