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

async def expense_items(argument: Dict):
    """
    Lógica interna para buscar gastos de itens específicos no banco de dados.
    """
    args = argument or {}
    
    # 1. TRATAMENTO DE PARÂMETROS (Flexibilidade para o LLM)
    # O Gemini pode enviar como 'item' ou 'nome_item'
    nome_item = args.get("item") or args.get("nome_item")
    period_raw = args.get("period", "")

    # 2. LIMPEZA DE JSON (Caso o LLM envie uma string JSON em vez de texto puro)
    if isinstance(period_raw, str) and period_raw.strip().startswith("{"):
        try:
            temp_dict = json.loads(period_raw)
            period_str = temp_dict.get("period", period_raw)
        except Exception:
            period_str = period_raw
    else:
        period_str = period_raw

    # 3. PROCESSAMENTO DE DATAS
    #logger.info(f"🔍 DEBUG: period_str recebido = '{period_str}'")
    period = PeriodHandler.parse_periodo(period_str)
    #logger.info(f"🔍 DEBUG: period retornado = {period}")
        
    if not period:
        return [types.TextContent(type="text", text=f"Erro: Período '{period_str}' inválido.")]
    
    start_date = period.get("start") if period else None
    end_date = period.get("end") if period else None
    #logger.info(f"🔍 DEBUG: start_date={start_date}, end_date={end_date}")

    # Validações Iniciais
    if not nome_item:
        return [types.TextContent(type="text", text="Erro: O nome do item não foi fornecido.")]
    
    if not start_date or not end_date:
        return [types.TextContent(type="text", text=f"Erro: Não foi possível interpretar o período '{period_str}'.")]

    conn = None
    cursor = None

    # INICIALIZAÇÃO DE ESCOPO (Evita NameError)
    total = 0.0
    qtd = 0
    try:
        # 4. CONEXÃO E QUERY
        conn = create_connection()
        if not conn:
            return [types.TextContent(type="text", text="Erro: Não foi possível conectar ao banco.")]

        cursor = conn.cursor(dictionary=True)
        
        # Usamos LIKE para encontrar itens mesmo que o usuário não digite o nome exato
        query = """
            SELECT 
                SUM(ROUND(preco_unitario * quantidade, 2)) as total,
                COUNT(*) as quantidade_transacoes
            FROM controle_financeiro.itens_comprados
            WHERE nome_item LIKE %s AND data_compra BETWEEN %s AND %s
        """
        search_term = f"{nome_item}%"
        cursor.execute(query, (search_term, start_date, end_date))
        row = cursor.fetchone()
        
        # Processa o resultado com cast para Dict
        result = cast(Dict[str, Any], row) if row else None

        # 5. PROCESSAMENTO DO RESULTADO
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

        if qtd == 0:
            msg = f"Não encontrei registros para '{nome_item}' entre {start_date} e {end_date}."
        else:
            msg = (f"Periodo: {start_date} a {end_date} | "
                   f"Item: {nome_item.capitalize()} | "
                   f"Total: R$ {total:.2f} | "
                   f"Compras: {qtd}")

        return [types.TextContent(type="text", text=msg)]

    except Exception as e:
        #logger.error(f"Erro no banco de dados: {str(e)}")
        return [types.TextContent(type="text", text=f"Erro ao acessar o banco: {str(e)}")]

    finally:
        # 6. FECHAMENTO SEGURO DA CONEXÃO
        if cursor: # Fecha apenas se o cursor foi criado
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Bloco de teste manual
"""if __name__ == "__main__":
    import asyncio
    print("=== TESTE MANUAL ===")
    
    # Simula a chamada que o Gemini faria
    teste = asyncio.run(expense_items({"item": "cerveja", "period": "dezembro 2025"}))
    print(f"Resultado: {teste[0].text}")"""