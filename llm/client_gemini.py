import asyncio
import logging

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

logger = logging.getLogger(__name__)


class FinanceAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.server_params = StdioServerParameters(
            command="python",
            args=["mcp_server/server.py"]
            )

    async def _process_mcp_cycle(self, prompt: str):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                mcp_tools_list = await session.list_tools()

                # --- CORREÇÃO DO ERRO DE TIPAGEM ---
                ## 1. Mapeamos as declarações convertendo o dicionário para o objeto Schema
                declarations = []
                for t in mcp_tools_list.tools:
                    # Se o inputSchema existir, criamos o objeto Schema usando desempacotamento
                    # Isso evita o uso de 'from_dict' e resolve o erro do Pylance
                    schema_obj = None
                    if t.inputSchema:
                        # No SDK novo, passamos os campos do dict como argumentos nomeados
                        schema_obj = types.Schema(**t.inputSchema)

                    declarations.append(
                        types.FunctionDeclaration(
                            name=t.name, description=t.description, parameters=schema_obj
                        )
                    )

                # 2. Criamos o objeto Tool do Gemini
                gemini_tool = types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=t.name,
                            description=t.description,
                            parameters=types.Schema(**t.inputSchema) if t.inputSchema else None,
                        )
                        for t in mcp_tools_list.tools
                    ]
                )

                # CORREÇÃO DEFINITIVA:
                # Passamos a lista diretamente no dicionário ou config.
                # Se o erro persistir na variável 'tools_for_gemini',
                # simplesmente remova a variável e coloque o valor direto no config:

                client = genai.Client(api_key=self.api_key)
                model_id = "models/gemini-2.5-flash" #"gemini-3-flash-preview"  #"gemini-1.5-flash"  #"gemini-3-flash-preview"  # "gemini-2.0-flash" #"gemini-flash-latest" #"gemini-1.5-flash" #"gemini-2.5-flash" #"gemini-1.5-flash" #"gemini-2.0-flash"

                logger.info(f"Solicitando modelo: {model_id}")

                from llm.prompts import SYSTEM_INSTRUCTION

                # Ao passar [gemini_tool] diretamente aqui, o Python faz o casting automático correto
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[gemini_tool],  # <--- Passe direto aqui
                    temperature=0.1,
                )

                response = client.models.generate_content(
                    model=model_id, contents=prompt, config=config
                )

                # 1. Verificamos se existem candidatos e conteúdo antes de acessar parts
                # Usamos 'is not None' para garantir a segurança no Pylance
                if (
                    response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                ):
                    part = response.candidates[0].content.parts[0]

                    # Verificamos se existe a chamada de função
                    if part.function_call:
                        fc = part.function_call

                        # RESOLUÇÃO DO ERRO:
                        # Verificamos explicitamente se fc.name não é None
                        if not fc.name:
                            logger.error("Modelo tentou chamar uma função sem nome.")
                            return "Erro: O modelo não especificou a ferramenta corretamente."

                        # Agora o Pylance sabe que 'fc.name' é obrigatoriamente 'str'
                        logger.info(f"Executando ferramenta MCP: {fc.name}")

                        # Chama o servidor MCP
                        tool_result = await session.call_tool(
                            name=fc.name, arguments=dict(fc.args) if fc.args else {}
                        )

                        # 2. EXTRAÇÃO SEGURA: Filtramos apenas conteúdos de texto
                        # Isso resolve os erros de ImageContent, AudioContent, etc.
                        text_parts = [
                            content.text
                            for content in tool_result.content
                            if isinstance(content, TextContent)
                        ]

                        result_text = (
                            " ".join(text_parts) if text_parts else "Sem resultado textual."
                        )

                        logger.info(f"Resultado da ferramenta: {result_text}")

                        # Segunda chamada para finalizar a resposta
                        response = client.models.generate_content(
                            model=model_id,
                            contents=[
                                types.Content(role="user", parts=[types.Part(text=prompt)]),
                                response.candidates[0].content,
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part(
                                            function_response=types.FunctionResponse(
                                                name=fc.name, response={"result": result_text}
                                            )
                                        )
                                    ],
                                ),
                            ],
                            config=config,
                        )

                # O atributo .text do SDK 2.0 já lida com o None internamente
                return response.text or "Não consegui gerar uma resposta."

    """def ask_question(self, prompt: str) -> str:
        try:
            # No Streamlit, pode haver um loop rodando.
            # Esta é a forma mais segura de rodar o async
            return asyncio.run(self._process_mcp_cycle(prompt))
        except Exception as e:
            logger.error(f"Erro no FinanceAgent: {e}")
            raise e"""

    async def ask_question(self, prompt: str) -> str: # DEVE SER ASYNC
        try:
            # DEVE TER AWAIT
            return await self._process_mcp_cycle(prompt) 
        except Exception as e:
            logger.error(f"Erro no FinanceAgent: {e}")
            raise e
