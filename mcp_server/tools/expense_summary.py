#import shared.date_config
#print(f"DEBUG: O arquivo date_config está em: {shared.date_config.__file__}")

from mcp import types
from typing import Dict, Any, cast
import json
import logging

from shared.date_config import PeriodHandler
from database.connection import create_connection
#from shared.config import setup_logging

# Inicializa o logging configurado no seu shared.config
#setup_logging()
#logger = logging.getLogger(__name__)

async def expense_summary(argument: Dict):
    """Lógica interna para buscar resumo de gastos no banco de dados."""
    args = argument or {}
    
    # Tratamento de parâmetros
    period_raw = args.get("period", "")
    #print(f"Período recebido: {period_raw}")
    
    # Limpeza de JSON (caso o LLM envie uma string JSON)
    if isinstance(period_raw, str) and period_raw.strip().startswith("{"):
        try:
            temp_dict = json.loads(period_raw)
            period_str = temp_dict.get("period", period_raw)
        except Exception:
            period_str = period_raw
    else:
        period_str = period_raw
    
    # Processamento de datas
    period = PeriodHandler.parse_periodo(period_str)
    #print(f"Data retornada por PeriodHandler: {period}")
    if not period:
        return [types.TextContent(type="text", text=f"Erro: Período '{period_str}' inválido.")]
    
    start_date = period.get("start") if period else None
    end_date = period.get("end") if period else None
    
    if not start_date or not end_date:
        return [types.TextContent(type="text", text=f"Erro: Não foi possível interpretar o período '{period_str}'.")]
    
    conn = None
    cursor = None
    
    # Inicialização de escopo
    total = 0.0
    qtd = 0
    
    try:
        # Conexão e query
        conn = create_connection()
        if not conn:
            return [types.TextContent(type="text", text="Erro: Não foi possível conectar ao banco.")]
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                SUM(ROUND(preco_unitario * quantidade, 2)) as total,
                COUNT(*) as quantidade_transacoes
            FROM controle_financeiro.itens_comprados
            WHERE data_compra BETWEEN %s AND %s
        """
        cursor.execute(query, (start_date, end_date))
        row = cursor.fetchone()
        
        # Processa o resultado com cast para Dict
        result = cast(Dict[str, Any], row) if row else None
        
        # Processamento do resultado
        if result:
            # Acesso seguro com cast
            try:
                total_raw = result.get('total')
                if total_raw is not None:
                    total = float(total_raw)
                else:
                    total = 0.0
            except (KeyError, ValueError, TypeError):
                total = 0.0
                
            try:
                qtd = result.get('quantidade_transacoes') or 0
            except (KeyError, TypeError):
                qtd = 0
        
        msg = (f"Periodo: {start_date} a {end_date} | "
               f"Total: R$ {total:.2f} | "
               f"Compras: {qtd}")
        
        return [types.TextContent(type="text", text=msg)]
        
    except Exception as e:
        #logger.error(f"Erro no banco de dados: {str(e)}")
        return [types.TextContent(type="text", text=f"Erro ao acessar o banco: {str(e)}")]
    
    finally:
        # Fechamento seguro da conexão
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
"""# USO        
if __name__ == "__main__":
    import asyncio
    result = asyncio.run(expense_summary({"period": "novembro 2025"})) # Imprimi tudo de print do data_utils
    #result = asyncio.run(expense_summary({"period": "novembro de 2025"})) 
    print(result)"""