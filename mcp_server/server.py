from typing import Any, Coroutine, cast

from fastmcp import FastMCP

from mcp_server.tools.expense_items import expense_items
from mcp_server.tools.expense_summary import expense_summary

mcp = FastMCP("gerenciador de Gastos")


@mcp.tool()
async def get_expense_summary(period: str) -> str:
    """
    Consulta o total de gastos e número de transações no banco de dados.
    Esta é a ferramenta principal para resumos financeiros.
    Args:
        period: O período desejado (ex: 'janeiro 2026', 'hoje', 'este mês').
    """

    try:
        resultado_mcp = await expense_summary({"period": period})
        # resultado_mcp = asyncio.run(expense_summary({"period": period}))
        # IMPORTANTE: Extraia apenas o texto para o Gemini
        # Como expense_summary retorna list[types.TextContent]
        if isinstance(resultado_mcp, list) and len(resultado_mcp) > 0:
            return str(resultado_mcp[0].text)

        return str(resultado_mcp)
    except Exception as e:
        return f"Erro na ferramenta get_expense_summary: {str(e)}"


@mcp.tool()
async def get_expense_items(item: str, period: str) -> str:
    """
    Busca o total gasto em um item específico (ex: 'leite') num período.
    """
    # Chamamos a função interna passando o dicionário que ela espera
    try:
        corrotina = cast(Coroutine[Any, Any, list], expense_items({"item": item, "period": period}))
        resultado_bruto = await corrotina

        # O FastMCP precisa de uma string, então extraimos o texto da lista:
        if isinstance(resultado_bruto, list) and len(resultado_bruto) > 0:
            # content = resultado_bruto[0].text
            return str(resultado_bruto[0].text)

        return str(resultado_bruto)
    except Exception as e:
        return f"Erro na ferramenta get_expense_items: {str(e)}"


if __name__ == "__main__":
    mcp.run()
