import sys
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
        self.server_params = StdioServerParameters(command=sys.executable, args=["mcp_server/server.py"])

    async def _process_mcp_cycle(self, prompt: str):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                mcp_tools_list = await session.list_tools()

                declarations = []
                for t in mcp_tools_list.tools:
                    schema_obj = None
                    if t.inputSchema:
                        schema_obj = types.Schema(**t.inputSchema)

                    declarations.append(
                        types.FunctionDeclaration(
                            name=t.name, description=t.description, parameters=schema_obj
                        )
                    )

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

                client = genai.Client(api_key=self.api_key)
                model_id = "models/gemini-2.5-flash"

                logger.info(f"Solicitando modelo: {model_id}")

                from llm.prompts import SYSTEM_INSTRUCTION

                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[gemini_tool],
                    temperature=0.1,
                )

                response = client.models.generate_content(
                    model=model_id, contents=prompt, config=config
                )

                if (
                    response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                ):
                    part = response.candidates[0].content.parts[0]

                    if part.function_call:
                        fc = part.function_call

                        if not fc.name:
                            logger.error("Modelo tentou chamar uma função sem nome.")
                            return "Erro: O modelo não especificou a ferramenta corretamente."

                        logger.info(f"Executando ferramenta MCP: {fc.name}")

                        tool_result = await session.call_tool(
                            name=fc.name, arguments=dict(fc.args) if fc.args else {}
                        )

                        text_parts = [
                            content.text
                            for content in tool_result.content
                            if isinstance(content, TextContent)
                        ]

                        result_text = (
                            " ".join(text_parts) if text_parts else "Sem resultado textual."
                        )

                        logger.info(f"Resultado da ferramenta: {result_text}")

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

                return response.text or "Não consegui gerar uma resposta."

    async def ask_question(self, prompt: str) -> str:
        try:
            return await self._process_mcp_cycle(prompt)
        except Exception as e:
            logger.error(f"Erro no FinanceAgent: {e}")
            raise e
