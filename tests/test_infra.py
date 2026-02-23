import os
import pytest
from database.connection import create_connection

def test_env_variables_exist():
    """Valida se o .env foi carregado e as chaves essenciais existem"""
    assert os.getenv("DB_HOST") is not None, "DB_HOST não configurado no .env"
    assert os.getenv("DB_NAME") is not None, "DB_NAME não configurado no .env"
    assert os.getenv("TABLE_NAME") is not None, "TABLE_NAME não configurado no .env"

def test_database_connection():
    """Tenta estabelecer conexão real com o banco"""
    conn = create_connection()
    assert conn is not None, "Falha crítica: Não foi possível conectar ao MySQL"
    assert conn.is_connected(), "Conexão estabelecida, mas não está ativa"
    conn.close()

def test_table_exists():
    """Verifica se a tabela configurada realmente existe no banco"""
    conn = create_connection()
    cursor = conn.cursor()
    table_name = os.getenv("TABLE_NAME")
    
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    assert result is not None, f"A tabela '{table_name}' não foi encontrada no banco de dados"