import unittest
from unittest.mock import patch


class TestFinanceAgent(unittest.TestCase):

    def _make_agent(self):
        from llm.client_gemini import FinanceAgent
        return FinanceAgent(api_key="fake-api-key")

    @patch("llm.client_gemini.asyncio.run")
    def test_ask_question_retorna_texto(self, mock_run):
        # Arrange
        mock_run.return_value = "Gasto total com mercado: R$ 200,00"
        agent = self._make_agent()

        # Act
        resultado = agent.ask_question("Quanto gastei com mercado?")

        # Assert
        self.assertIsNotNone(resultado)
        self.assertIn("R$", resultado)

    @patch("llm.client_gemini.asyncio.run")
    def test_ask_question_prompt_vazio(self, mock_run):
        # Testa comportamento com prompt vazio
        mock_run.return_value = "Não consegui gerar uma resposta."
        agent = self._make_agent()

        resultado = agent.ask_question("")

        self.assertEqual(resultado, "Não consegui gerar uma resposta.")

    @patch("llm.client_gemini.asyncio.run")
    def test_ask_question_propaga_excecao(self, mock_run):
        # Testa se exceções são propagadas corretamente
        mock_run.side_effect = Exception("API unavailable")
        agent = self._make_agent()

        with self.assertRaises(Exception) as context:
            agent.ask_question("Quanto gastei?")

        self.assertIn("API unavailable", str(context.exception))

    @patch("llm.client_gemini.asyncio.run")
    def test_ask_question_chama_asyncio_run(self, mock_run):
        # Garante que asyncio.run é chamado uma vez por pergunta
        mock_run.return_value = "Resposta qualquer"
        agent = self._make_agent()

        agent.ask_question("Qual meu gasto total?")

        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
    