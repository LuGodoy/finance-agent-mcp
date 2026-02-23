import os
import json
from dotenv import load_dotenv 
from typing import Any, Dict, cast
from mcp import types
from database.connection import create_connection
from shared.date_config import PeriodHandler
from database.connection import create_connection, DB_NAME, TABLE_NAME

load_dotenv()

async def expense_summary(argument: Dict):
    """Lógica interna para buscar resumo de gastos no banco de dados."""
    args = argument or {}

    period_raw = args.get("period", "")
    
    if isinstance(period_raw, str) and period_raw.strip().startswith("{"):
        try:
            temp_dict = json.loads(period_raw)
            period_str = temp_dict.get("period", period_raw)
        except Exception:
            period_str = period_raw
    else:
        period_str = period_raw

    period = PeriodHandler.parse_periodo(period_str)
    
    if not period:
        return [types.TextContent(type="text", text=f"Erro: Período '{period_str}' inválido.")]

    start_date = period.get("start") if period else None
    end_date = period.get("end") if period else None

    if not start_date or not end_date:
        return [
            types.TextContent(
                type="text", text=f"Erro: Não foi possível interpretar o período '{period_str}'."
            )
        ]

    conn = None
    cursor = None

    total = 0.0
    qtd = 0

    try:
        conn = create_connection()
        if not conn:
            return [
                types.TextContent(type="text", text="Erro: Não foi possível conectar ao banco.")
            ]

        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT
                SUM(ROUND(preco_unitario * quantidade, 2)) as total,
                COUNT(*) as quantidade_transacoes
            FROM `{DB_NAME}`.`{TABLE_NAME}`
            WHERE data_compra BETWEEN %s AND %s
        """
        cursor.execute(query, (start_date, end_date))
        row = cursor.fetchone()

        result = cast(Dict[str, Any], row) if row else None

        if result:
            try:
                total_raw = result.get("total")
                if total_raw is not None:
                    total = float(total_raw)
                else:
                    total = 0.0
            except (KeyError, ValueError, TypeError):
                total = 0.0

            try:
                qtd = result.get("quantidade_transacoes") or 0
            except (KeyError, TypeError):
                qtd = 0

        msg = f"Periodo: {start_date} a {end_date} | Total: R$ {total:.2f} | Compras: {qtd}"

        return [types.TextContent(type="text", text=msg)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Erro ao acessar o banco: {str(e)}")]

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
