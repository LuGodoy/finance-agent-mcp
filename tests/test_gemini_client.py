import asyncio
import unittest
from unittest.mock import AsyncMock, patch


class TestFinanceAgent(unittest.TestCase):
    def _make_agent(self):
        from llm.client_gemini import FinanceAgent

        return FinanceAgent(api_key="fake-api-key")

    @patch("llm.client_gemini.FinanceAgent._process_mcp_cycle", new_callable=AsyncMock)
    def test_ask_question_retorna_texto(self, mock_process):

        mock_process.return_value = "Gasto total: R$ 200,00"
        agent = self._make_agent()

        resultado = asyncio.run(agent.ask_question("Quanto gastei?"))

        self.assertIn("R$", resultado)

    @patch("llm.client_gemini.FinanceAgent._process_mcp_cycle", new_callable=AsyncMock)
    def test_ask_question_propaga_excecao(self, mock_process):

        mock_process.side_effect = Exception("API unavailable")
        agent = self._make_agent()

        with self.assertRaises(Exception):
            asyncio.run(agent.ask_question("teste"))
