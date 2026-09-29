"""Gráficos das telas, gerados em Python como SVG no servidor.

São provisórios: o formato final entra na Sprint 4 (issue #17), a partir da ideia
do Gabriel. Regras seguidas desde já: linha de 2px, marcador com anel da cor do
fundo, grade em filete de 1px, um eixo só, texto sempre em cor de texto (nunca na
cor da série) e dica de valor ao passar o mouse em cada ponto.
"""

from __future__ import annotations

import math
from datetime import date
from html import escape
from typing import Callable

from markupsafe import Markup

from app.formatos import data_curta, metrica, pct

AZUL = "#0866FF"
LARANJA = "#C2410C"
TINTA = "#1C2B33"
MUDO = "#65676B"
TENDENCIA = "#8A8D91"
GRADE = "#E4E6EB"
LAVADO = "#F0F2F5"
FUNDO = "#FFFFFF"
FONTE = "Inter, Segoe UI, Helvetica, Arial, sans-serif"


def _passo_limpo(amplitude: float, alvo: int) -> float:
    if amplitude <= 0:
        return 1.0
    bruto = amplitude / alvo
    ordem = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * ordem:
            return m * ordem
    return 10 * ordem


def _eixo(vmin: float, vmax: float, alvo: int = 4) -> tuple[float, float, list[float]]:
    passo = _passo_limpo(vmax - vmin, alvo)
    inicio = math.floor(vmin / passo) * passo
    fim = math.ceil(vmax / passo) * passo
    ticks, valor = [], inicio
    while valor <= fim + passo * 1e-9:
        ticks.append(round(valor, 10))
        valor += passo
    return inicio, fim, ticks


def _texto(x: float, y: float, conteudo: str, *, tamanho: int = 12, cor: str = MUDO,
           ancora: str = "start", peso: int = 400) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONTE}" font-size="{tamanho}" '
        f'font-weight="{peso}" fill="{cor}" text-anchor="{ancora}">{escape(conteudo)}</text>'
    )


def _alvo(x: float, y: float, dica: str) -> str:
    """Área de toque maior que o ponto, com a dica nativa do navegador."""
    return (
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="transparent">'
        f"<title>{escape(dica)}</title></circle>"
    )


def _svg(largura: int, altura: int, titulo: str, corpo: list[str]) -> Markup:
    return Markup(
        f'<svg class="grafico__svg" viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="{escape(titulo)}" xmlns="http://www.w3.org/2000/svg">'
        f"<title>{escape(titulo)}</title>{''.join(corpo)}</svg>"
    )


def _formatador(unidade: str) -> Callable[[float], str]:
    return lambda valor: metrica(valor, unidade)


def sparkline(valores: list[float], titulo: str, largura: int = 112, altura: int = 28) -> Markup:
    """Tendência em cinza, com o ponto atual no azul."""
    if len(valores) < 2:
        return Markup("")
    vmin, vmax = min(valores), max(valores)

    def x(i: int) -> float:
        return 4 + i * (largura - 10) / (len(valores) - 1)

    def y(v: float) -> float:
        return altura - 5 - (v - vmin) * (altura - 10) / ((vmax - vmin) or 1)

    pontos = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(valores))
    xf, yf = x(len(valores) - 1), y(valores[-1])
    return Markup(
        f'<svg class="sparkline" viewBox="0 0 {largura} {altura}" width="{largura}" height="{altura}" '
        f'role="img" aria-label="{escape(titulo)}" xmlns="http://www.w3.org/2000/svg">'
        f"<title>{escape(titulo)}</title>"
        f'<polyline points="{pontos}" fill="none" stroke="{TENDENCIA}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{xf:.1f}" cy="{yf:.1f}" r="4" fill="{AZUL}" stroke="{FUNDO}" stroke-width="2"/>'
        f"</svg>"
    )


def leque(historico: list[tuple[date, float]], previsao: list, provisorio_desde: date,
          hoje: date, unidade: str, titulo: str) -> Markup:
    """Histórico da janela móvel + faixa P10–P90 e mediana da previsão."""
    largura, altura = 760, 330
    esq, dir_, topo, base = 72, 118, 28, 40
    datas = [d for d, _ in historico] + [p.data for p in previsao]
    n = len(datas)
    fmt = _formatador(unidade)

    def x(i: float) -> float:
        return esq + i * (largura - esq - dir_) / (n - 1)

    valores = [v for _, v in historico] + [p.p90 for p in previsao]
    y0, y1, ticks = _eixo(0, max(valores) * 1.05)

    def y(v: float) -> float:
        return altura - base - (v - y0) * (altura - base - topo) / ((y1 - y0) or 1)

    corpo: list[str] = []
    for t in ticks:
        corpo.append(
            f'<line x1="{esq}" x2="{largura - dir_}" y1="{y(t):.1f}" y2="{y(t):.1f}" '
            f'stroke="{GRADE}" stroke-width="1"/>'
        )
        corpo.append(_texto(esq - 10, y(t) + 4, fmt(t), ancora="end"))

    i_prov = datas.index(provisorio_desde)
    i_hoje = datas.index(hoje)
    meio_passo = (x(1) - x(0)) / 2
    corpo.append(
        f'<rect x="{x(i_prov) - meio_passo:.1f}" y="{topo}" width="{x(i_hoje) - x(i_prov) + meio_passo:.1f}" '
        f'height="{altura - base - topo}" fill="{LAVADO}"/>'
    )
    corpo.append(_texto(x(i_prov) - meio_passo + 4, altura - base - 8, "provisório", tamanho=11))
    corpo.append(
        f'<line x1="{x(i_hoje):.1f}" x2="{x(i_hoje):.1f}" y1="{topo}" y2="{altura - base}" '
        f'stroke="{TINTA}" stroke-width="1"/>'
    )
    corpo.append(_texto(x(i_hoje) + 6, topo + 14, "hoje", tamanho=11, cor=TINTA, peso=600))

    # A previsão parte do último dia fechado: os dias provisórios ainda vão mudar.
    nh = len(historico)
    ancora = i_prov - 1
    valor_ancora = historico[ancora][1]
    inicio = (x(ancora), y(valor_ancora))
    superior = [inicio] + [(x(nh + k), y(p.p90)) for k, p in enumerate(previsao)]
    inferior = [(x(nh + k), y(p.p10)) for k, p in enumerate(previsao)][::-1] + [inicio]
    faixa = " ".join(f"{px:.1f},{py:.1f}" for px, py in superior + inferior)
    corpo.append(f'<polygon points="{faixa}" fill="{AZUL}" fill-opacity=".12"/>')

    fechado = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(historico[: ancora + 1]))
    corpo.append(
        f'<polyline points="{fechado}" fill="none" stroke="{AZUL}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )
    provisorio = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(historico) if i >= ancora)
    corpo.append(
        f'<polyline points="{provisorio}" fill="none" stroke="{TENDENCIA}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )
    mediana = [inicio] + [(x(nh + k), y(p.p50)) for k, p in enumerate(previsao)]
    corpo.append(
        f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for px, py in mediana)}" fill="none" '
        f'stroke="{AZUL}" stroke-width="2" stroke-dasharray="6 5" stroke-linecap="round"/>'
    )
    corpo.append(
        f'<circle cx="{inicio[0]:.1f}" cy="{inicio[1]:.1f}" r="4.5" fill="{AZUL}" '
        f'stroke="{FUNDO}" stroke-width="2"/>'
    )

    fim = previsao[-1]
    xf = largura - dir_ + 8
    corpo.append(_texto(xf, y(fim.p90) + 4, f"P90 {fmt(fim.p90)}", tamanho=11))
    corpo.append(_texto(xf, y(fim.p50) + 4, f"P50 {fmt(fim.p50)}", tamanho=12, cor=TINTA, peso=600))
    corpo.append(_texto(xf, y(fim.p10) + 4, f"P10 {fmt(fim.p10)}", tamanho=11))

    for i, dia in enumerate(datas):
        if (n - 1 - i) % 7 == 0:
            corpo.append(_texto(x(i), altura - base + 20, data_curta(dia), ancora="middle"))

    for i, (dia, valor) in enumerate(historico):
        corpo.append(_alvo(x(i), y(valor), f"{data_curta(dia)}: {fmt(valor)}"))
    for k, p in enumerate(previsao):
        corpo.append(_alvo(
            x(nh + k), y(p.p50),
            f"{data_curta(p.data)}: previsto {fmt(p.p50)} (faixa {fmt(p.p10)} a {fmt(p.p90)})",
        ))
    return _svg(largura, altura, titulo, corpo)


def _barra(x0: float, x1: float, y: float, altura: float, cor: str) -> str:
    """Barra horizontal com a ponta de dado arredondada e a base reta."""
    raio = min(4.0, abs(x1 - x0) / 2)
    if abs(x1 - x0) < 0.5:
        return ""
    if x1 > x0:
        caminho = (
            f"M{x0:.1f},{y:.1f} H{x1 - raio:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + raio:.1f} "
            f"V{y + altura - raio:.1f} Q{x1:.1f},{y + altura:.1f} {x1 - raio:.1f},{y + altura:.1f} "
            f"H{x0:.1f} Z"
        )
    else:
        caminho = (
            f"M{x0:.1f},{y:.1f} H{x1 + raio:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + raio:.1f} "
            f"V{y + altura - raio:.1f} Q{x1:.1f},{y + altura:.1f} {x1 + raio:.1f},{y + altura:.1f} "
            f"H{x0:.1f} Z"
        )
    return f'<path d="{caminho}" fill="{cor}"/>'


def cascata(efeitos: list, total: float, titulo: str) -> Markup:
    """Efeito de cada fator sobre o CPA, a partir de uma linha de zero central."""
    linhas = [(e.rotulo, e.efeito_cpa, False) for e in efeitos] + [("Variação total do CPA", total, True)]
    largura, esq, dir_, topo, passo, espessura = 760, 230, 80, 56, 48, 20
    altura = topo + passo * len(linhas) + 12
    maior = max(abs(v) for _, v, _ in linhas) or 0.01
    zero = esq + (largura - esq - dir_) / 2
    escala = (largura - esq - dir_) / 2 / maior

    corpo = [
        f'<rect x="{esq}" y="14" width="12" height="12" rx="2" fill="{LARANJA}"/>',
        _texto(esq + 18, 24, "Aumenta o CPA", cor=TINTA),
        f'<rect x="{esq + 140}" y="14" width="12" height="12" rx="2" fill="{AZUL}"/>',
        _texto(esq + 158, 24, "Reduz o CPA", cor=TINTA),
        f'<line x1="{zero:.1f}" x2="{zero:.1f}" y1="{topo - 8}" y2="{altura - 8}" stroke="{GRADE}" stroke-width="1"/>',
    ]
    for i, (rotulo, valor, e_total) in enumerate(linhas):
        centro = topo + i * passo + passo / 2
        cor = TINTA if e_total else (LARANJA if valor > 0 else AZUL)
        corpo.append(_texto(esq - 16, centro + 4, rotulo, cor=TINTA, ancora="end", peso=600 if e_total else 400, tamanho=13))
        x1 = zero + valor * escala
        corpo.append(_barra(zero, x1, centro - espessura / 2, espessura, cor))
        if valor >= 0:
            corpo.append(_texto(x1 + 8, centro + 4, pct(valor), cor=TINTA, peso=600))
        else:
            corpo.append(_texto(x1 - 8, centro + 4, pct(valor), cor=TINTA, peso=600, ancora="end"))
    return _svg(largura, altura, titulo, corpo)


def previsto_realizado(pontos: list[tuple[date, float, float]], unidade: str, titulo: str) -> Markup:
    """Duas séries: o que a régua previu 7 dias antes e o que aconteceu."""
    largura, altura = 760, 300
    esq, dir_, topo, base = 72, 24, 48, 40
    fmt = _formatador(unidade)
    n = len(pontos)

    def x(i: int) -> float:
        return esq + i * (largura - esq - dir_) / (n - 1)

    maximo = max(max(p, r) for _, p, r in pontos)
    y0, y1, ticks = _eixo(0, maximo * 1.05)

    def y(v: float) -> float:
        return altura - base - (v - y0) * (altura - base - topo) / ((y1 - y0) or 1)

    corpo = [
        f'<line x1="{esq}" x2="{esq + 22}" y1="20" y2="20" stroke="{AZUL}" stroke-width="2"/>',
        _texto(esq + 30, 24, "Previsto 7 dias antes (régua)", cor=TINTA),
        f'<line x1="{esq + 250}" x2="{esq + 272}" y1="20" y2="20" stroke="{LARANJA}" stroke-width="2"/>',
        _texto(esq + 280, 24, "Realizado", cor=TINTA),
    ]
    for t in ticks:
        corpo.append(
            f'<line x1="{esq}" x2="{largura - dir_}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRADE}" stroke-width="1"/>'
        )
        corpo.append(_texto(esq - 10, y(t) + 4, fmt(t), ancora="end"))
    for indice, cor in ((1, AZUL), (2, LARANJA)):
        linha = " ".join(f"{x(i):.1f},{y(ponto[indice]):.1f}" for i, ponto in enumerate(pontos))
        corpo.append(
            f'<polyline points="{linha}" fill="none" stroke="{cor}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
        corpo.append(
            f'<circle cx="{x(n - 1):.1f}" cy="{y(pontos[-1][indice]):.1f}" r="4.5" fill="{cor}" '
            f'stroke="{FUNDO}" stroke-width="2"/>'
        )
    for i, (dia, _, _) in enumerate(pontos):
        if (n - 1 - i) % 7 == 0:
            corpo.append(_texto(x(i), altura - base + 20, data_curta(dia), ancora="middle"))
    for i, (dia, previsto, realizado) in enumerate(pontos):
        corpo.append(_alvo(
            x(i), (y(previsto) + y(realizado)) / 2,
            f"{data_curta(dia)}: previsto {fmt(previsto)}, realizado {fmt(realizado)}",
        ))
    return _svg(largura, altura, titulo, corpo)
