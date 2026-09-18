"""Formatação de números e datas no padrão brasileiro."""

from datetime import date

MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def _milhar_br(texto: str) -> str:
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def decimal(valor: float, casas: int = 2) -> str:
    return _milhar_br(f"{valor:,.{casas}f}")


def brl(valor: float, casas: int = 2) -> str:
    return f"R$ {decimal(valor, casas)}"


def pct(valor: float, casas: int = 0, sinal: bool = True) -> str:
    """0.123 -> '+12%'. Usa o sinal de menos tipográfico."""
    formato = f"{{:+.{casas}f}}" if sinal else f"{{:.{casas}f}}"
    texto = formato.format(valor * 100).replace(".", ",").replace("-", "−")
    return f"{texto}%"


def inteiro(valor: float) -> str:
    return decimal(valor, 0)


def data_curta(dia: date) -> str:
    return dia.strftime("%d/%m")


def data_longa(dia: date) -> str:
    return f"{dia.day} de {MESES[dia.month - 1]}"


def metrica(valor: float, tipo: str) -> str:
    """CPA em reais; ROAS como multiplicador com duas casas."""
    return brl(valor) if tipo == "CPA" else decimal(valor, 2)
