import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union

import dateparser

logger = logging.getLogger(__name__)


class DateHandler:
    @staticmethod
    def sanitize_for_mysql(date: Union[str, datetime, int, float, None]) -> Optional[str]:
        """
        Converte uma data em um formato adequado para o MySQL.

        Args:
            date: A data a ser convertida. Pode ser uma string no formato
                'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS', um objeto datetime,
                ou um valor numérico (timestamp).

        Returns:
            Uma string representando a data no formato adequado para o MySQL ('YYYY-MM-DD'),
            ou None se a data for inválida.
        """

        if date is None or date == "":
            return None

        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")

        if isinstance(date, (int, float)):
            dt = datetime.fromtimestamp(date)
            return dt.strftime("%Y-%m-%d")

        if isinstance(date, str):
            date = date.strip().strip("\"'")
            # Tenta extrair um ano de 4 dígitos manualmente se existir
            year_match = re.search(r"\b(20\d{2})\b", date)
            extracted_year = year_match.group(1) if year_match else None

            parsed = dateparser.parse(
                date,
                languages=["pt", "de", "en"],  # português, alemão, inglês, etc.
                settings={
                    "PREFER_DATES_FROM": "past",
                    "DATE_ORDER": "DMY",  # ajuda em formatos 10/01/2026 etc. [web:108][web:107]
                    "RELATIVE_BASE": datetime(int(extracted_year), 1, 1)
                    if extracted_year
                    else datetime.now(),
                },
            )
            if parsed is None:
                return None
            return parsed.strftime("%Y-%m-%d")

        return None


class PeriodHandler:
    @staticmethod
    def parse_periodo(period: Union[str, dict, tuple, None]) -> Dict[str, Optional[str]]:
        """
        Interpreta um período e retorna um dicionário com as datas de início e fim (YYYY-MM-DD).

        Args:
            Aceita:
            - dict: {"start": ..., "end": ...}
            - tuple/list: (inicio, fim)
            - string: "hoje", "ontem", "este mês", "últimos 7 dias",
            nomes de meses em pt, datas soltas, etc.

        Returns:
            Um dicionário ({"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}) com as chaves 'start' e 'end' representando as datas de início e fim.
        """
        result: Dict[str, Optional[str]] = {"start": None, "end": None}
        if not period:
            return result

        if isinstance(period, dict):
            result["start"] = DateHandler.sanitize_for_mysql(period.get("start"))
            result["end"] = DateHandler.sanitize_for_mysql(period.get("end"))
            return result

        if isinstance(period, (tuple, list)) and len(period) == 2:
            result["start"] = DateHandler.sanitize_for_mysql(period[0])
            result["end"] = DateHandler.sanitize_for_mysql(period[1])
            return result

        if isinstance(period, str):
            raw_str = period
            text = raw_str.lower().strip()
            hoje = datetime.now().date()

            patterns = [
                # ========= PORTUGUÊS =========
                # Adicione este padrão no topo da lista 'patterns' dentro de parse_periodo
                (
                    r"(.+?)\s+(?:a|at[ée]|to|bis)\s+(.+)",
                    lambda m: (
                        dateparser.parse(
                            m.group(1), languages=["pt", "de", "en"], settings={"DATE_ORDER": "DMY"}
                        ),
                        dateparser.parse(
                            m.group(2), languages=["pt", "de", "en"], settings={"DATE_ORDER": "DMY"}
                        ),
                    ),
                ),
                # Dias
                (r"^hoje$", lambda m: (hoje, hoje)),
                (r"^ontem$", lambda m: (hoje - timedelta(days=1), hoje - timedelta(days=1))),
                # Semana
                (r"esta semana|essa semana", lambda m: PeriodHandler._semana_atual()),
                (r"semana passada|[úu]ltima semana", lambda m: PeriodHandler._semana_passada()),
                # Mês atual / passado
                (
                    r"m[eê]s passado|ultimo mes|último m[eê]s",
                    lambda m: PeriodHandler._mes_passado(),
                ),
                (r"este m[eê]s|esse m[eê]s", lambda m: PeriodHandler._mes_atual()),
                # Ano atual / passado
                (r"este ano|esse ano", lambda m: PeriodHandler._ano_atual()),
                (r"ano passado|[úu]ltimo ano", lambda m: PeriodHandler._ano_passado()),
                # Últimos N dias / meses
                (
                    r"[úu]ltimos?\s+(\d+)\s+dias?",
                    lambda m: (hoje - timedelta(days=int(m.group(1))), hoje),
                ),
                (
                    r"[úu]ltimos?\s+(\d+)\s+meses",
                    lambda m: PeriodHandler._ultimos_meses(int(m.group(1))),
                ),
                # Meses específicos (português) - CORRIGIDO para aceitar "dezembro 2025" e "dezembro de 2025"
                (
                    r"dezembro\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(12, m.group(1)),
                ),
                (r"dezembro$", lambda m: PeriodHandler._mes_especifico(12, None)),
                # _________
                # ========= PORTUGUÊS (EXEMPLO NOVEMBRO) =========
                # Primeiro: O padrão mais específico (com ano)
                (
                    r"novembro\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(11, m.group(1)),
                ),
                # Segundo: O padrão genérico (sem ano) - note o '$' para garantir que não há nada depois
                (r"^novembro$", lambda m: PeriodHandler._mes_especifico(11, None)),
                # _______
                # (r'novembro\s+(?:de\s+)?(\d{4})', lambda m: PeriodHandler._mes_especifico(11, m.group(1))),
                # (r'novembro$', lambda m: PeriodHandler._mes_especifico(11, None)),
                (
                    r"outubro\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(10, m.group(1)),
                ),
                (r"outubro$", lambda m: PeriodHandler._mes_especifico(10, None)),
                (
                    r"setembro\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(9, m.group(1)),
                ),
                (r"setembro$", lambda m: PeriodHandler._mes_especifico(9, None)),
                (
                    r"agosto\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(8, m.group(1)),
                ),
                (r"agosto$", lambda m: PeriodHandler._mes_especifico(8, None)),
                (
                    r"julho\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(7, m.group(1)),
                ),
                (r"julho$", lambda m: PeriodHandler._mes_especifico(7, None)),
                (
                    r"junho\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(6, m.group(1)),
                ),
                (r"junho$", lambda m: PeriodHandler._mes_especifico(6, None)),
                (
                    r"maio\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(5, m.group(1)),
                ),
                (r"maio$", lambda m: PeriodHandler._mes_especifico(5, None)),
                (
                    r"abril\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(4, m.group(1)),
                ),
                (r"abril$", lambda m: PeriodHandler._mes_especifico(4, None)),
                (
                    r"mar[cç]o\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(3, m.group(1)),
                ),
                (r"mar[cç]o$", lambda m: PeriodHandler._mes_especifico(3, None)),
                (
                    r"fevereiro\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(2, m.group(1)),
                ),
                (r"fevereiro$", lambda m: PeriodHandler._mes_especifico(2, None)),
                (
                    r"janeiro\s+(?:de\s+)?(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(1, m.group(1)),
                ),
                (r"janeiro$", lambda m: PeriodHandler._mes_especifico(1, None)),
                # Trimestre (pt)
                (
                    r"q(\d)|(\d)º\s+trimestre",
                    lambda m: PeriodHandler._trimestre(int(m.group(1) or m.group(2))),
                ),
                # ========= ALEMÃO =========
                # Dias
                (r"^heute$", lambda m: (hoje, hoje)),
                (r"^gestern$", lambda m: (hoje - timedelta(days=1), hoje - timedelta(days=1))),
                # Semana
                (r"diese woche", lambda m: PeriodHandler._semana_atual()),
                (
                    r"letzte woche",
                    lambda m: PeriodHandler._semana_atual(),
                ),  # se quiser tratar igual
                # Mês atual / passado
                (r"dieser monat", lambda m: PeriodHandler._mes_atual()),
                (r"letzter monat", lambda m: PeriodHandler._mes_passado()),
                # Ano atual / passado
                (r"dieses jahr", lambda m: PeriodHandler._ano_atual()),
                (r"letztes jahr", lambda m: PeriodHandler._ano_passado()),
                # Últimos N dias / meses
                (
                    r"letzten?\s+(\d+)\s+tage?",
                    lambda m: (hoje - timedelta(days=int(m.group(1))), hoje),
                ),
                (
                    r"letzten?\s+(\d+)\s+monate?",
                    lambda m: PeriodHandler._ultimos_meses(int(m.group(1))),
                ),
                # Meses específicos (alemão)
                (r"januar\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(1, m.group(1))),
                (r"januar$", lambda m: PeriodHandler._mes_especifico(1, None)),
                (r"februar\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(2, m.group(1))),
                (r"februar$", lambda m: PeriodHandler._mes_especifico(2, None)),
                (
                    r"(?:märz|maerz)\s+(\d{4})",
                    lambda m: PeriodHandler._mes_especifico(3, m.group(1)),
                ),
                (r"(?:märz|maerz)$", lambda m: PeriodHandler._mes_especifico(3, None)),
                (r"april\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(4, m.group(1))),
                (r"april$", lambda m: PeriodHandler._mes_especifico(4, None)),
                (r"mai\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(5, m.group(1))),
                (r"mai$", lambda m: PeriodHandler._mes_especifico(5, None)),
                (r"juni\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(6, m.group(1))),
                (r"juni$", lambda m: PeriodHandler._mes_especifico(6, None)),
                (r"juli\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(7, m.group(1))),
                (r"juli$", lambda m: PeriodHandler._mes_especifico(7, None)),
                (r"august\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(8, m.group(1))),
                (r"august$", lambda m: PeriodHandler._mes_especifico(8, None)),
                (r"september\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(9, m.group(1))),
                (r"september$", lambda m: PeriodHandler._mes_especifico(9, None)),
                (r"oktober\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(10, m.group(1))),
                (r"oktober$", lambda m: PeriodHandler._mes_especifico(10, None)),
                (r"november\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(11, m.group(1))),
                (r"november$", lambda m: PeriodHandler._mes_especifico(11, None)),
                (r"dezember\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(12, m.group(1))),
                (r"dezember$", lambda m: PeriodHandler._mes_especifico(12, None)),
                # ========= INGLÊS =========
                (r"^today$", lambda m: (hoje, hoje)),
                (r"^yesterday$", lambda m: (hoje - timedelta(days=1), hoje - timedelta(days=1))),
                (r"^this week$", lambda m: PeriodHandler._semana_atual()),
                (r"^last week$", lambda m: PeriodHandler._semana_atual()),
                (r"^this month$", lambda m: PeriodHandler._mes_atual()),
                (r"^last month$", lambda m: PeriodHandler._mes_passado()),
                (r"^this year$", lambda m: PeriodHandler._ano_atual()),
                (r"^last year$", lambda m: PeriodHandler._ano_passado()),
                (r"last\s+(\d+)\s+days?", lambda m: (hoje - timedelta(days=int(m.group(1))), hoje)),
                (
                    r"last\s+(\d+)\s+months?",
                    lambda m: PeriodHandler._ultimos_meses(int(m.group(1))),
                ),
                # Meses específicos (inglês)
                (r"january\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(1, m.group(1))),
                (r"january$", lambda m: PeriodHandler._mes_especifico(1, None)),
                (r"february\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(2, m.group(1))),
                (r"february$", lambda m: PeriodHandler._mes_especifico(2, None)),
                (r"march\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(3, m.group(1))),
                (r"march$", lambda m: PeriodHandler._mes_especifico(3, None)),
                (r"april\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(4, m.group(1))),
                (r"april$", lambda m: PeriodHandler._mes_especifico(4, None)),
                (r"may\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(5, m.group(1))),
                (r"may$", lambda m: PeriodHandler._mes_especifico(5, None)),
                (r"june\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(6, m.group(1))),
                (r"june$", lambda m: PeriodHandler._mes_especifico(6, None)),
                (r"july\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(7, m.group(1))),
                (r"july$", lambda m: PeriodHandler._mes_especifico(7, None)),
                (r"august\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(8, m.group(1))),
                (r"august$", lambda m: PeriodHandler._mes_especifico(8, None)),
                (r"september\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(9, m.group(1))),
                (r"september$", lambda m: PeriodHandler._mes_especifico(9, None)),
                (r"october\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(10, m.group(1))),
                (r"october$", lambda m: PeriodHandler._mes_especifico(10, None)),
                (r"november\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(11, m.group(1))),
                (r"november$", lambda m: PeriodHandler._mes_especifico(11, None)),
                (r"december\s+(\d{4})", lambda m: PeriodHandler._mes_especifico(12, m.group(1))),
                (r"december$", lambda m: PeriodHandler._mes_especifico(12, None)),
            ]
            for pattern, func in patterns:
                match = re.search(pattern, text)
                if match:
                    start, end = func(match)
                    result["start"] = start.strftime("%Y-%m-%d") if start else None
                    result["end"] = end.strftime("%Y-%m-%d") if end else None
                    return result

            # 2) CASO ESPECIAL: string é só um ano (ex.: "2025", "  2023  ")
            match_ano = re.fullmatch(r"\s*(\d{4})\s*", raw_str)
            if match_ano:
                inicio, fim = PeriodHandler._ano_especifico(match_ano.group(1))
                result["start"] = inicio.strftime("%Y-%m-%d")
                result["end"] = fim.strftime("%Y-%m-%d")
                return result

            # Fallback: data única via dateparser (desabilitado para meses específicos)
            # Verifica se é um mês conhecido antes de usar dateparser
            meses_conhecidos = [
                "janeiro",
                "fevereiro",
                "março",
                "marco",
                "abril",
                "maio",
                "junho",
                "julho",
                "agosto",
                "setembro",
                "outubro",
                "novembro",
                "dezembro",
                "januar",
                "februar",
                "märz",
                "maerz",
                "mai",
                "juni",
                "juli",
                "august",
                "september",
                "oktober",
                "november",
                "dezember",
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "september",
                "october",
                "december",
            ]

            # Se contém um mês conhecido, não usar dateparser
            if not any(mes in text for mes in meses_conhecidos):
                parsed = dateparser.parse(
                    raw_str,
                    languages=["pt", "de", "en"],
                    settings={"PREFER_DATES_FROM": "past", "DATE_ORDER": "DMY"},
                )
                if parsed:
                    only_date = parsed.strftime("%Y-%m-%d")
                    result["start"] = only_date
                    result["end"] = only_date
        return result

    # ===== Helpers que precisam existir =====
    @staticmethod
    def _semana_atual() -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        inicio = hoje - timedelta(days=hoje.weekday())  # segunda
        fim = inicio + timedelta(days=6)  # domingo
        return inicio, fim

    @staticmethod
    def _semana_passada() -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        # 1. Encontra a segunda-feira da semana ATUAL
        segunda_atual = hoje - timedelta(days=hoje.weekday())

        # 2. Subtrai 7 dias para chegar na segunda da semana PASSADA
        inicio = segunda_atual - timedelta(days=7)

        # 3. Soma 6 dias à segunda passada para chegar no domingo passado
        fim = inicio + timedelta(days=6)

        return inicio, fim

    @staticmethod
    def _mes_atual() -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        inicio = hoje.replace(day=1)
        if hoje.month == 12:
            fim = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fim = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)
        return inicio, fim

    @staticmethod
    def _mes_passado() -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        primeiro_deste_mes = hoje.replace(day=1)
        fim = primeiro_deste_mes - timedelta(days=1)
        inicio = fim.replace(day=1)
        return inicio, fim

    @staticmethod
    def _ultimos_meses(n: int) -> Tuple[datetime, datetime]:
        fim = datetime.now()
        ano = fim.year
        mes = fim.month - n
        while mes <= 0:
            mes += 12
            ano -= 1
        inicio = datetime(ano, mes, 1)
        return inicio, fim

    @staticmethod
    def _ano_atual() -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        inicio = hoje.replace(month=1, day=1)
        fim = hoje.replace(month=12, day=31)
        return inicio, fim

    @staticmethod
    def _ano_passado() -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        ano = hoje.year - 1
        inicio = datetime(ano, 1, 1)
        fim = datetime(ano, 12, 31)
        return inicio, fim

    @staticmethod
    def _ano_especifico(ano_str: Optional[str]) -> Tuple[datetime, datetime]:
        """
        Retorna o primeiro e o último dia de um ano específico.
        Se ano_str for None, usa o ano atual.
        """
        hoje = datetime.now()
        ano = int(ano_str) if ano_str else hoje.year

        inicio = datetime(ano, 1, 1)
        fim = datetime(ano, 12, 31)
        return inicio, fim

    @staticmethod
    def _mes_especifico(mes: int, ano_str: Optional[str]) -> Tuple[datetime, datetime]:
        hoje = datetime.now()
        # Se o regex capturou o ano (\d{4}), usamos ele. Caso contrário, usamos o ano atual.
        ano = int(ano_str) if ano_str else hoje.year

        inicio = datetime(ano, mes, 1)
        if mes == 12:
            fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            fim = datetime(ano, mes + 1, 1) - timedelta(days=1)
        return inicio, fim

    @staticmethod
    def _trimestre(num: int) -> Tuple[datetime, datetime]:
        """
        Ex: _trimestre(1) -> (01-01, 31-03) do ano atual
        """
        hoje = datetime.now()
        ano = hoje.year
        mes_inicio = 3 * (num - 1) + 1
        inicio = datetime(ano, mes_inicio, 1)
        mes_fim = mes_inicio + 2
        if mes_fim == 12:
            fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            fim = datetime(ano, mes_fim + 1, 1) - timedelta(days=1)
        return inicio, fim


# Teste ano especifico
# print(PeriodHandler.parse_periodo("2024"))
"""# USO
print("#--------------------- ----------------#\n"
      "#     Uso da Class DateHandler        #\n"
     "#-------------------------------------#\n")

ins = DateHandler()
result = ins.sanitize_for_mysql("2026-01-10")
print(result)
result = ins.sanitize_for_mysql('2026/01/10')
print(result)
result = ins.sanitize_for_mysql('26 de fevereiro de 2026')
print(result)
result = ins.sanitize_for_mysql("2026-01-11")
print(result)
result = ins.sanitize_for_mysql('20/01/2026 20:04:02')
print(result)
result = ins.sanitize_for_mysql("ontem")
print(result)
result = ins.sanitize_for_mysql("amanhã")
print(result)
result = ins.sanitize_for_mysql("mês passado")
print(result)
result = ins.sanitize_for_mysql("ano passado")
print(result)
result = ins.sanitize_for_mysql("24 januar 2025")
print(result)
result = ins.sanitize_for_mysql("freitag")
print(result)

print("#--------------------------------------#\n"
      "#     Uso da Class PeriodHandler       #\n"
     "#---------------------------------------#\n")
# ===== TESTES DateHandler =====
print("=== Testes DateHandler ===")
print(DateHandler.sanitize_for_mysql("2026-01-10"))              # ISO
print(DateHandler.sanitize_for_mysql("10/01/2026"))              # pt numérico
print(DateHandler.sanitize_for_mysql("24 de janeiro de 2026"))   # pt extenso
print(DateHandler.sanitize_for_mysql("24. Januar 2026"))         # de extenso
print(DateHandler.sanitize_for_mysql("January 24, 2026"))        # en extenso

print(DateHandler.sanitize_for_mysql(1705536000))                # timestamp (exemplo)
print(DateHandler.sanitize_for_mysql(datetime(2026, 1, 24)))     # datetime direto
print(DateHandler.sanitize_for_mysql(None))                      # None
print(DateHandler.sanitize_for_mysql(""))                        # vazio


# ===== TESTES PeriodHandler: dicionário e tupla =====
print("\n=== Testes PeriodHandler (dict / tuple) ===")
print(PeriodHandler.parse_periodo({
    "start": "2026-01-01",
    "end": "2026-01-31"
}))
print(PeriodHandler.parse_periodo((
    "24 de janeiro de 2026",
    "24. Januar 2026"
)))


# ===== TESTES PeriodHandler: português =====
print("\n=== Testes PeriodHandler (PT) ===")
print("hoje:", PeriodHandler.parse_periodo("hoje"))
print("ontem:", PeriodHandler.parse_periodo("ontem"))
print("esta semana:", PeriodHandler.parse_periodo("esta semana"))
print("este mês:", PeriodHandler.parse_periodo("este mês"))
print("mês passado:", PeriodHandler.parse_periodo("mês passado"))
print("este ano:", PeriodHandler.parse_periodo("este ano"))
print("ano passado:", PeriodHandler.parse_periodo("ano passado"))
print("últimos 7 dias:", PeriodHandler.parse_periodo("últimos 7 dias"))
print("últimos 3 meses:", PeriodHandler.parse_periodo("últimos 3 meses"))
print("janeiro 2026:", PeriodHandler.parse_periodo("janeiro 2026"))
print("março 2026:", PeriodHandler.parse_periodo("março 2026"))


# ===== TESTES PeriodHandler: alemão =====
print("\n=== Testes PeriodHandler (DE) ===")
print("heute:", PeriodHandler.parse_periodo("heute"))
print("gestern:", PeriodHandler.parse_periodo("gestern"))
print("diese woche:", PeriodHandler.parse_periodo("diese Woche"))
print("dieser monat:", PeriodHandler.parse_periodo("dieser Monat"))
print("letzter monat:", PeriodHandler.parse_periodo("letzter Monat"))
print("dieses jahr:", PeriodHandler.parse_periodo("dieses Jahr"))
print("letztes jahr:", PeriodHandler.parse_periodo("letztes Jahr"))
print("letzten 7 tage:", PeriodHandler.parse_periodo("letzten 7 Tage"))
print("letzten 3 monate:", PeriodHandler.parse_periodo("letzten 3 Monate"))
print("januar 2026:", PeriodHandler.parse_periodo("Januar 2026"))
print("märz 2026:", PeriodHandler.parse_periodo("März 2026"))


# ===== TESTES PeriodHandler: inglês (se patterns de EN estiverem incluídos) =====
print("\n=== Testes PeriodHandler (EN) ===")
print("today:", PeriodHandler.parse_periodo("today"))
print("yesterday:", PeriodHandler.parse_periodo("yesterday"))
print("this week:", PeriodHandler.parse_periodo("this week"))
print("this month:", PeriodHandler.parse_periodo("this month"))
print("last month:", PeriodHandler.parse_periodo("last month"))
print("this year:", PeriodHandler.parse_periodo("this year"))
print("last year:", PeriodHandler.parse_periodo("last year"))
print("last 7 days:", PeriodHandler.parse_periodo("last 7 days"))
print("last 3 months:", PeriodHandler.parse_periodo("last 3 months"))
print("March 2026:", PeriodHandler.parse_periodo("March 2026"))


# ===== TESTES PeriodHandler: datas “soltas” que vão para o dateparser =====
print("\n=== Testes PeriodHandler (datas pontuais via dateparser) ===")
print("24 de janeiro de 2026:", PeriodHandler.parse_periodo("24 de janeiro de 2026"))
print("24. Januar 2026:", PeriodHandler.parse_periodo("24. Januar 2026"))
print("24 January 2026:", PeriodHandler.parse_periodo("24 January 2026"))
print("10/01/2026:", PeriodHandler.parse_periodo("10/01/2026"))
print("2026-01-10:", PeriodHandler.parse_periodo("2026-01-10"))
"""
"""# USO
print("#--------------------- ----------------#\n"
      "#     Uso da Class DateHandler        #\n"
     "#-------------------------------------#\n")

ins = DateHandler()
result = ins.sanitize_for_mysql("2026-01-10")
print(result)
result = ins.sanitize_for_mysql('2026/01/10')
print(result)
result = ins.sanitize_for_mysql('26 de fevereiro de 2026')
print(result)
result = ins.sanitize_for_mysql("2026-01-11")
print(result)
result = ins.sanitize_for_mysql('20/01/2026 20:04:02')
print(result)
result = ins.sanitize_for_mysql("ontem")
print(result)
result = ins.sanitize_for_mysql("amanhã")
print(result)
result = ins.sanitize_for_mysql("mês passado")
print(result)
result = ins.sanitize_for_mysql("ano passado")
print(result)
result = ins.sanitize_for_mysql("24 januar 2025")
print(result)
result = ins.sanitize_for_mysql("freitag")
print(result)

print("#--------------------------------------#\n"
      "#     Uso da Class PeriodHandler       #\n"
     "#---------------------------------------#\n")
# ===== TESTES DateHandler =====
print("=== Testes DateHandler ===")
print(DateHandler.sanitize_for_mysql("2026-01-10"))              # ISO
print(DateHandler.sanitize_for_mysql("10/01/2026"))              # pt numérico
print(DateHandler.sanitize_for_mysql("24 de janeiro de 2026"))   # pt extenso
print(DateHandler.sanitize_for_mysql("24. Januar 2026"))         # de extenso
print(DateHandler.sanitize_for_mysql("January 24, 2026"))        # en extenso

print(DateHandler.sanitize_for_mysql(1705536000))                # timestamp (exemplo)
print(DateHandler.sanitize_for_mysql(datetime(2026, 1, 24)))     # datetime direto
print(DateHandler.sanitize_for_mysql(None))                      # None
print(DateHandler.sanitize_for_mysql(""))                        # vazio


# ===== TESTES PeriodHandler: dicionário e tupla =====
print("\n=== Testes PeriodHandler (dict / tuple) ===")
print(PeriodHandler.parse_periodo({
    "start": "2026-01-01",
    "end": "2026-01-31"
}))
print(PeriodHandler.parse_periodo((
    "24 de janeiro de 2026",
    "24. Januar 2026"
)))


# ===== TESTES PeriodHandler: português =====
print("\n=== Testes PeriodHandler (PT) ===")
print("hoje:", PeriodHandler.parse_periodo("hoje"))
print("ontem:", PeriodHandler.parse_periodo("ontem"))
print("esta semana:", PeriodHandler.parse_periodo("esta semana"))
print("este mês:", PeriodHandler.parse_periodo("este mês"))
print("mês passado:", PeriodHandler.parse_periodo("mês passado"))
print("este ano:", PeriodHandler.parse_periodo("este ano"))
print("ano passado:", PeriodHandler.parse_periodo("ano passado"))
print("últimos 7 dias:", PeriodHandler.parse_periodo("últimos 7 dias"))
print("últimos 3 meses:", PeriodHandler.parse_periodo("últimos 3 meses"))
print("janeiro 2026:", PeriodHandler.parse_periodo("janeiro 2026"))
print("março 2026:", PeriodHandler.parse_periodo("março 2026"))


# ===== TESTES PeriodHandler: alemão =====
print("\n=== Testes PeriodHandler (DE) ===")
print("heute:", PeriodHandler.parse_periodo("heute"))
print("gestern:", PeriodHandler.parse_periodo("gestern"))
print("diese woche:", PeriodHandler.parse_periodo("diese Woche"))
print("dieser monat:", PeriodHandler.parse_periodo("dieser Monat"))
print("letzter monat:", PeriodHandler.parse_periodo("letzter Monat"))
print("dieses jahr:", PeriodHandler.parse_periodo("dieses Jahr"))
print("letztes jahr:", PeriodHandler.parse_periodo("letztes Jahr"))
print("letzten 7 tage:", PeriodHandler.parse_periodo("letzten 7 Tage"))
print("letzten 3 monate:", PeriodHandler.parse_periodo("letzten 3 Monate"))
print("januar 2026:", PeriodHandler.parse_periodo("Januar 2026"))
print("märz 2026:", PeriodHandler.parse_periodo("März 2026"))


# ===== TESTES PeriodHandler: inglês (se patterns de EN estiverem incluídos) =====
print("\n=== Testes PeriodHandler (EN) ===")
print("today:", PeriodHandler.parse_periodo("today"))
print("yesterday:", PeriodHandler.parse_periodo("yesterday"))
print("this week:", PeriodHandler.parse_periodo("this week"))
print("this month:", PeriodHandler.parse_periodo("this month"))
print("last month:", PeriodHandler.parse_periodo("last month"))
print("this year:", PeriodHandler.parse_periodo("this year"))
print("last year:", PeriodHandler.parse_periodo("last year"))
print("last 7 days:", PeriodHandler.parse_periodo("last 7 days"))
print("last 3 months:", PeriodHandler.parse_periodo("last 3 months"))
print("March 2026:", PeriodHandler.parse_periodo("March 2026"))


# ===== TESTES PeriodHandler: datas “soltas” que vão para o dateparser =====
print("\n=== Testes PeriodHandler (datas pontuais via dateparser) ===")
print("24 de janeiro de 2026:", PeriodHandler.parse_periodo("24 de janeiro de 2026"))
print("24. Januar 2026:", PeriodHandler.parse_periodo("24. Januar 2026"))
print("24 January 2026:", PeriodHandler.parse_periodo("24 January 2026"))
print("10/01/2026:", PeriodHandler.parse_periodo("10/01/2026"))
print("2026-01-10:", PeriodHandler.parse_periodo("2026-01-10"))
"""
"""# USO
print("#--------------------- ----------------#\n"
      "#     Uso da Class DateHandler        #\n"
     "#-------------------------------------#\n")

ins = DateHandler()
result = ins.sanitize_for_mysql("2026-01-10")
print(result)
result = ins.sanitize_for_mysql('2026/01/10')
print(result)
result = ins.sanitize_for_mysql('26 de fevereiro de 2026')
print(result)
result = ins.sanitize_for_mysql("2026-01-11")
print(result)
result = ins.sanitize_for_mysql('20/01/2026 20:04:02')
print(result)
result = ins.sanitize_for_mysql("ontem")
print(result)
result = ins.sanitize_for_mysql("amanhã")
print(result)
result = ins.sanitize_for_mysql("mês passado")
print(result)
result = ins.sanitize_for_mysql("ano passado")
print(result)
result = ins.sanitize_for_mysql("24 januar 2025")
print(result)
result = ins.sanitize_for_mysql("freitag")
print(result)

print("#--------------------------------------#\n"
      "#     Uso da Class PeriodHandler       #\n"
     "#---------------------------------------#\n")
# ===== TESTES DateHandler =====
print("=== Testes DateHandler ===")
print(DateHandler.sanitize_for_mysql("2026-01-10"))              # ISO
print(DateHandler.sanitize_for_mysql("10/01/2026"))              # pt numérico
print(DateHandler.sanitize_for_mysql("24 de janeiro de 2026"))   # pt extenso
print(DateHandler.sanitize_for_mysql("24. Januar 2026"))         # de extenso
print(DateHandler.sanitize_for_mysql("January 24, 2026"))        # en extenso

print(DateHandler.sanitize_for_mysql(1705536000))                # timestamp (exemplo)
print(DateHandler.sanitize_for_mysql(datetime(2026, 1, 24)))     # datetime direto
print(DateHandler.sanitize_for_mysql(None))                      # None
print(DateHandler.sanitize_for_mysql(""))                        # vazio


# ===== TESTES PeriodHandler: dicionário e tupla =====
print("\n=== Testes PeriodHandler (dict / tuple) ===")
print(PeriodHandler.parse_periodo({
    "start": "2026-01-01",
    "end": "2026-01-31"
}))
print(PeriodHandler.parse_periodo((
    "24 de janeiro de 2026",
    "24. Januar 2026"
)))


# ===== TESTES PeriodHandler: português =====
print("\n=== Testes PeriodHandler (PT) ===")
print("hoje:", PeriodHandler.parse_periodo("hoje"))
print("ontem:", PeriodHandler.parse_periodo("ontem"))
print("esta semana:", PeriodHandler.parse_periodo("esta semana"))
print("este mês:", PeriodHandler.parse_periodo("este mês"))
print("mês passado:", PeriodHandler.parse_periodo("mês passado"))
print("este ano:", PeriodHandler.parse_periodo("este ano"))
print("ano passado:", PeriodHandler.parse_periodo("ano passado"))
print("últimos 7 dias:", PeriodHandler.parse_periodo("últimos 7 dias"))
print("últimos 3 meses:", PeriodHandler.parse_periodo("últimos 3 meses"))
print("janeiro 2026:", PeriodHandler.parse_periodo("janeiro 2026"))
print("março 2026:", PeriodHandler.parse_periodo("março 2026"))


# ===== TESTES PeriodHandler: alemão =====
print("\n=== Testes PeriodHandler (DE) ===")
print("heute:", PeriodHandler.parse_periodo("heute"))
print("gestern:", PeriodHandler.parse_periodo("gestern"))
print("diese woche:", PeriodHandler.parse_periodo("diese Woche"))
print("dieser monat:", PeriodHandler.parse_periodo("dieser Monat"))
print("letzter monat:", PeriodHandler.parse_periodo("letzter Monat"))
print("dieses jahr:", PeriodHandler.parse_periodo("dieses Jahr"))
print("letztes jahr:", PeriodHandler.parse_periodo("letztes Jahr"))
print("letzten 7 tage:", PeriodHandler.parse_periodo("letzten 7 Tage"))
print("letzten 3 monate:", PeriodHandler.parse_periodo("letzten 3 Monate"))
print("januar 2026:", PeriodHandler.parse_periodo("Januar 2026"))
print("märz 2026:", PeriodHandler.parse_periodo("März 2026"))


# ===== TESTES PeriodHandler: inglês (se patterns de EN estiverem incluídos) =====
print("\n=== Testes PeriodHandler (EN) ===")
print("today:", PeriodHandler.parse_periodo("today"))
print("yesterday:", PeriodHandler.parse_periodo("yesterday"))
print("this week:", PeriodHandler.parse_periodo("this week"))
print("this month:", PeriodHandler.parse_periodo("this month"))
print("last month:", PeriodHandler.parse_periodo("last month"))
print("this year:", PeriodHandler.parse_periodo("this year"))
print("last year:", PeriodHandler.parse_periodo("last year"))
print("last 7 days:", PeriodHandler.parse_periodo("last 7 days"))
print("last 3 months:", PeriodHandler.parse_periodo("last 3 months"))
print("March 2026:", PeriodHandler.parse_periodo("March 2026"))


# ===== TESTES PeriodHandler: datas “soltas” que vão para o dateparser =====
print("\n=== Testes PeriodHandler (datas pontuais via dateparser) ===")
print("24 de janeiro de 2026:", PeriodHandler.parse_periodo("24 de janeiro de 2026"))
print("24. Januar 2026:", PeriodHandler.parse_periodo("24. Januar 2026"))
print("24 January 2026:", PeriodHandler.parse_periodo("24 January 2026"))
print("10/01/2026:", PeriodHandler.parse_periodo("10/01/2026"))
print("2026-01-10:", PeriodHandler.parse_periodo("2026-01-10"))
"""
"""# USO
print("#--------------------- ----------------#\n"
      "#     Uso da Class DateHandler        #\n"
     "#-------------------------------------#\n")

ins = DateHandler()
result = ins.sanitize_for_mysql("2026-01-10")
print(result)
result = ins.sanitize_for_mysql('2026/01/10')
print(result)
result = ins.sanitize_for_mysql('26 de fevereiro de 2026')
print(result)
result = ins.sanitize_for_mysql("2026-01-11")
print(result)
result = ins.sanitize_for_mysql('20/01/2026 20:04:02')
print(result)
result = ins.sanitize_for_mysql("ontem")
print(result)
result = ins.sanitize_for_mysql("amanhã")
print(result)
result = ins.sanitize_for_mysql("mês passado")
print(result)
result = ins.sanitize_for_mysql("ano passado")
print(result)
result = ins.sanitize_for_mysql("24 januar 2025")
print(result)
result = ins.sanitize_for_mysql("freitag")
print(result)

print("#--------------------------------------#\n"
      "#     Uso da Class PeriodHandler       #\n"
     "#---------------------------------------#\n")
# ===== TESTES DateHandler =====
print("=== Testes DateHandler ===")
print(DateHandler.sanitize_for_mysql("2026-01-10"))              # ISO
print(DateHandler.sanitize_for_mysql("10/01/2026"))              # pt numérico
print(DateHandler.sanitize_for_mysql("24 de janeiro de 2026"))   # pt extenso
print(DateHandler.sanitize_for_mysql("24. Januar 2026"))         # de extenso
print(DateHandler.sanitize_for_mysql("January 24, 2026"))        # en extenso

print(DateHandler.sanitize_for_mysql(1705536000))                # timestamp (exemplo)
print(DateHandler.sanitize_for_mysql(datetime(2026, 1, 24)))     # datetime direto
print(DateHandler.sanitize_for_mysql(None))                      # None
print(DateHandler.sanitize_for_mysql(""))                        # vazio


# ===== TESTES PeriodHandler: dicionário e tupla =====
print("\n=== Testes PeriodHandler (dict / tuple) ===")
print(PeriodHandler.parse_periodo({
    "start": "2026-01-01",
    "end": "2026-01-31"
}))
print(PeriodHandler.parse_periodo((
    "24 de janeiro de 2026",
    "24. Januar 2026"
)))


# ===== TESTES PeriodHandler: português =====
print("\n=== Testes PeriodHandler (PT) ===")
print("hoje:", PeriodHandler.parse_periodo("hoje"))
print("ontem:", PeriodHandler.parse_periodo("ontem"))
print("esta semana:", PeriodHandler.parse_periodo("esta semana"))
print("este mês:", PeriodHandler.parse_periodo("este mês"))
print("mês passado:", PeriodHandler.parse_periodo("mês passado"))
print("este ano:", PeriodHandler.parse_periodo("este ano"))
print("ano passado:", PeriodHandler.parse_periodo("ano passado"))
print("últimos 7 dias:", PeriodHandler.parse_periodo("últimos 7 dias"))
print("últimos 3 meses:", PeriodHandler.parse_periodo("últimos 3 meses"))
print("janeiro 2026:", PeriodHandler.parse_periodo("janeiro 2026"))
print("março 2026:", PeriodHandler.parse_periodo("março 2026"))


# ===== TESTES PeriodHandler: alemão =====
print("\n=== Testes PeriodHandler (DE) ===")
print("heute:", PeriodHandler.parse_periodo("heute"))
print("gestern:", PeriodHandler.parse_periodo("gestern"))
print("diese woche:", PeriodHandler.parse_periodo("diese Woche"))
print("dieser monat:", PeriodHandler.parse_periodo("dieser Monat"))
print("letzter monat:", PeriodHandler.parse_periodo("letzter Monat"))
print("dieses jahr:", PeriodHandler.parse_periodo("dieses Jahr"))
print("letztes jahr:", PeriodHandler.parse_periodo("letztes Jahr"))
print("letzten 7 tage:", PeriodHandler.parse_periodo("letzten 7 Tage"))
print("letzten 3 monate:", PeriodHandler.parse_periodo("letzten 3 Monate"))
print("januar 2026:", PeriodHandler.parse_periodo("Januar 2026"))
print("märz 2026:", PeriodHandler.parse_periodo("März 2026"))


# ===== TESTES PeriodHandler: inglês (se patterns de EN estiverem incluídos) =====
print("\n=== Testes PeriodHandler (EN) ===")
print("today:", PeriodHandler.parse_periodo("today"))
print("yesterday:", PeriodHandler.parse_periodo("yesterday"))
print("this week:", PeriodHandler.parse_periodo("this week"))
print("this month:", PeriodHandler.parse_periodo("this month"))
print("last month:", PeriodHandler.parse_periodo("last month"))
print("this year:", PeriodHandler.parse_periodo("this year"))
print("last year:", PeriodHandler.parse_periodo("last year"))
print("last 7 days:", PeriodHandler.parse_periodo("last 7 days"))
print("last 3 months:", PeriodHandler.parse_periodo("last 3 months"))
print("March 2026:", PeriodHandler.parse_periodo("March 2026"))


# ===== TESTES PeriodHandler: datas “soltas” que vão para o dateparser =====
print("\n=== Testes PeriodHandler (datas pontuais via dateparser) ===")
print("24 de janeiro de 2026:", PeriodHandler.parse_periodo("24 de janeiro de 2026"))
print("24. Januar 2026:", PeriodHandler.parse_periodo("24. Januar 2026"))
print("24 January 2026:", PeriodHandler.parse_periodo("24 January 2026"))
print("10/01/2026:", PeriodHandler.parse_periodo("10/01/2026"))
print("2026-01-10:", PeriodHandler.parse_periodo("2026-01-10"))
"""
