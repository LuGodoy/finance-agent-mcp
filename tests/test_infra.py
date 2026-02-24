import os
import unittest

from database.connection import create_connection

# Verifica se estamos no GitHub Actions
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


class TestInfra(unittest.TestCase):
    def test_env_variables_exist(self):
        """Valida se o .env foi carregado (Pula no GitHub)"""
        if IN_GITHUB_ACTIONS:
            self.skipTest("Pulando teste de .env no GitHub Actions")

        self.assertIsNotNone(os.getenv("DB_HOST"))
        self.assertIsNotNone(os.getenv("DB_NAME"))

    @unittest.skipIf(IN_GITHUB_ACTIONS, "Não há banco de dados no GitHub Actions")
    def test_database_connection(self):
        """Tenta estabelecer conexão real com o banco"""
        conn = create_connection()
        self.assertIsNotNone(conn, "Falha crítica: Não foi possível conectar ao MySQL")

        if conn:
            self.assertTrue(conn.is_connected())
            conn.close()

    @unittest.skipIf(IN_GITHUB_ACTIONS, "Não há banco de dados no GitHub Actions")
    def test_table_exists(self):
        """Verifica se a tabela configurada realmente existe no banco"""
        conn = create_connection()

        if conn is None:
            self.fail("Conexão não criada")

        cursor = conn.cursor()
        table_name = os.getenv("TABLE_NAME")

        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        result = cursor.fetchone()

        cursor.close()
        conn.close()
        self.assertIsNotNone(result)
