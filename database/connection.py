import mysql.connector 
from mysql.connector import Error, errorcode
import os
from dotenv import load_dotenv
import logging

#logger = logging.getLogger(__name__)

load_dotenv(dotenv_path='.env')

DB_CONFIG = {
    'user':os.getenv("DB_USER"), 
    'password':os.getenv("DB_PASSWORD"), 
    'host':os.getenv("DB_HOST"), 
    'port':int(os.getenv("DB_PORT", 3306)), 
    'database':os.getenv("DB_NAME", "")
    }

def create_connection():
    """Cria e retorna uma conexão com o banco de dados MYSQL"""
    try:
        conn= mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            #logger.info("Conexão ao MySQL bem sucedida")
            return conn
        
    except Error as e:
        #logger.info(f"Erro ao conectar com MYSQL: {e}")
        return None