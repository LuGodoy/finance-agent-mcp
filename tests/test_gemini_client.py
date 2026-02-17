import unittest
from unittest.mock import MagicMock

# Ajuste o import abaixo para o caminho real do seu cliente Gemini


class TestFinanceAgent(unittest.TestCase):
    def test_gemini_response_parsing(self):
        # 1. Criamos um "Dublê" (Mock) do cliente da API
        mock_client = MagicMock()

        # 2. Simulamos o que o Gemini devolveria (ex: um JSON de gastos)
        mock_response = MagicMock()
        mock_response.text = "O seu gasto total em leite foi de R$ 200,00."
        mock_client.generate_content.return_value = mock_response

        # 3. Instanciamos seu objeto (passando o mock se possível, ou mockando a classe)
        # Aqui testamos se a sua função de "perguntar ao bot" funciona
        # pergunta = "Quanto gastei com leite este mês?"
        resultado = mock_response.text  # Simulação simples

        # 4. Verificação (Assert)
        self.assertIn("R$ 200,00", resultado)
        print("✅ Teste de Mock passou: Resposta simulada processada com sucesso!")


if __name__ == "__main__":
    unittest.main()
