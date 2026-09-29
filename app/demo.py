"""Dados de demonstração das telas.

Tudo aqui é fictício e gerado em memória com semente fixa: nenhuma empresa real,
nenhum dado de conta de anúncio. A previsão é provisória — o último valor fechado
com uma faixa de passeio aleatório — só para dar forma às telas. O modelo por
quantis entra na Sprint 2 (issue #11) e o detector de anomalia na Sprint 3 (#13).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean, pstdev

from app.formatos import brl

HOJE = date(2026, 9, 17)
DIAS_HISTORICO = 42
DIAS_PROVISORIOS = 3
ULTIMO_FECHADO = DIAS_HISTORICO - DIAS_PROVISORIOS - 1
JANELA_ATUAL = 7
JANELA_BASE = 14
HORIZONTE_MAX = 14
Z80 = 1.2816

# Fração das conversões que a Meta já reportou nos dias provisórios (do mais
# antigo para o mais recente). É o atraso da janela de atribuição.
ATRASO_ATRIBUICAO = (0.92, 0.80, 0.60)

LIMIAR_ATENCAO = 0.10
LIMIAR_CRITICO = 0.25

NOME_FATOR = {
    "cpm": "custo por mil impressões",
    "ctr": "taxa de clique",
    "conv": "taxa de conversão",
}

# Artigo definido de cada fator, para a frase concordar: "o custo", "a taxa".
ARTIGO = {"cpm": "o", "ctr": "a", "conv": "a"}


@dataclass(frozen=True)
class Dia:
    data: date
    gasto: float
    impressoes: int
    cliques: int
    conversoes: int
    valor: float
    provisorio: bool


@dataclass(frozen=True)
class Janela:
    gasto: float
    impressoes: int
    cliques: int
    conversoes: int
    valor: float

    @property
    def cpm(self) -> float:
        return self.gasto / self.impressoes * 1000 if self.impressoes else 0.0

    @property
    def ctr(self) -> float:
        return self.cliques / self.impressoes if self.impressoes else 0.0

    @property
    def taxa_conversao(self) -> float:
        return self.conversoes / self.cliques if self.cliques else 0.0

    @property
    def cpa(self) -> float:
        return self.gasto / self.conversoes if self.conversoes else 0.0

    @property
    def roas(self) -> float:
        return self.valor / self.gasto if self.gasto else 0.0

    @property
    def ticket(self) -> float:
        return self.valor / self.conversoes if self.conversoes else 0.0

    def metrica(self, tipo: str) -> float:
        return self.cpa if tipo == "CPA" else self.roas


@dataclass(frozen=True)
class Ponto:
    data: date
    p10: float
    p50: float
    p90: float


@dataclass(frozen=True)
class Efeito:
    fator: str
    rotulo: str
    antes: float
    depois: float
    variacao: float
    efeito_cpa: float


@dataclass
class Alerta:
    id: str
    empresa_id: str
    empresa_nome: str
    campanha_id: str
    campanha_nome: str
    metrica: str
    variacao: float
    gravidade: str
    causa: str
    verba_em_risco: float
    detectado_em: date
    explicacao: str

    @property
    def estado(self) -> str:
        return FEEDBACK.get(self.id, "aberto")


@dataclass
class Campanha:
    id: str
    nome: str
    objetivo: str
    empresa_id: str
    metrica: str
    dias: list[Dia]
    atual: Janela = field(init=False)
    base: Janela = field(init=False)
    sigma: float = field(init=False)
    previsao: list[Ponto] = field(init=False)
    alerta: Alerta | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        fim = ULTIMO_FECHADO
        self.atual = somar(self.dias[fim - JANELA_ATUAL + 1: fim + 1])
        self.base = somar(self.dias[fim - JANELA_ATUAL - JANELA_BASE + 1: fim - JANELA_ATUAL + 1])
        fechados = [self.movel(i) for i in range(JANELA_ATUAL * 2, fim + 1)]
        passos = [depois - antes for antes, depois in zip(fechados, fechados[1:])]
        self.sigma = pstdev(passos) if len(passos) > 1 else 0.0
        centro = fechados[-1]
        self.previsao = []
        for h in range(1, HORIZONTE_MAX + 1):
            amplitude = Z80 * self.sigma * math.sqrt(h + DIAS_PROVISORIOS)
            self.previsao.append(
                Ponto(HOJE + timedelta(days=h), max(0.0, centro - amplitude), centro, centro + amplitude)
            )

    def movel(self, fim: int) -> float:
        """Métrica na janela móvel de 7 dias que termina no índice `fim`."""
        return somar(self.dias[max(0, fim - JANELA_ATUAL + 1): fim + 1]).metrica(self.metrica)

    @property
    def valor_atual(self) -> float:
        return self.atual.metrica(self.metrica)

    @property
    def valor_base(self) -> float:
        return self.base.metrica(self.metrica)

    @property
    def variacao(self) -> float:
        return self.valor_atual / self.valor_base - 1 if self.valor_base else 0.0

    @property
    def piora(self) -> float:
        """Positivo quando a campanha piorou: CPA subindo ou ROAS caindo."""
        return self.variacao if self.metrica == "CPA" else -self.variacao

    @property
    def gravidade(self) -> str:
        return self.alerta.gravidade if self.alerta else "normal"

    @property
    def gasto_diario(self) -> float:
        return self.atual.gasto / JANELA_ATUAL

    def previsao_em(self, horizonte: int) -> Ponto:
        return self.previsao[horizonte - 1]

    def serie(self, dias: int = 28) -> list[tuple[date, float]]:
        inicio = DIAS_HISTORICO - dias
        return [(self.dias[i].data, self.movel(i)) for i in range(inicio, DIAS_HISTORICO)]

    def efeitos(self) -> list[Efeito]:
        """Decompõe a variação do CPA: CPA = CPM / (1000 × CTR × taxa de conversão)."""
        a, b = self.base, self.atual
        return [
            Efeito("cpm", "Custo por mil impressões", a.cpm, b.cpm, b.cpm / a.cpm - 1, b.cpm / a.cpm - 1),
            Efeito("ctr", "Taxa de clique", a.ctr, b.ctr, b.ctr / a.ctr - 1, a.ctr / b.ctr - 1),
            Efeito(
                "conv", "Taxa de conversão", a.taxa_conversao, b.taxa_conversao,
                b.taxa_conversao / a.taxa_conversao - 1, a.taxa_conversao / b.taxa_conversao - 1,
            ),
        ]

    def culpado(self) -> Efeito:
        return max(self.efeitos(), key=lambda e: abs(e.efeito_cpa))

    def frase_diagnostico(self) -> str:
        variacao_cpa = self.atual.cpa / self.base.cpa - 1
        verbo = "subiu" if variacao_cpa > 0 else "caiu"
        principal = self.culpado()
        estaveis = [e for e in self.efeitos() if e is not principal and abs(e.variacao) < 0.05]
        movimento = "subiu" if principal.variacao > 0 else "caiu"
        contracao = "do" if ARTIGO[principal.fator] == "o" else "da"
        frase = (
            f"O CPA {verbo} {abs(variacao_cpa) * 100:.0f}% na última semana fechada. "
            f"A maior parte veio {contracao} {principal.rotulo.lower()}, que {movimento} "
            f"{abs(principal.variacao) * 100:.0f}%"
        )
        if estaveis:
            nomes = " e ".join(f"{ARTIGO[e.fator]} {e.rotulo.lower()}" for e in estaveis)
            concordancia = "ficou estável" if len(estaveis) == 1 else "ficaram estáveis"
            frase += f"; {nomes} {concordancia}"
        return frase + "."

    def acuracia(self, dias: int = 21) -> dict:
        """Régua: prever para daqui a 7 dias o último valor conhecido."""
        pontos = []
        for t in range(ULTIMO_FECHADO - dias + 1, ULTIMO_FECHADO + 1):
            pontos.append((self.dias[t].data, self.movel(t - 7), self.movel(t)))
        smape = mean(2 * abs(p - r) / (abs(p) + abs(r)) for _, p, r in pontos if p or r)
        amplitude = Z80 * self.sigma * math.sqrt(7)
        cobertura = mean(1.0 if abs(r - p) <= amplitude else 0.0 for _, p, r in pontos)
        return {"pontos": pontos, "smape": smape, "cobertura": cobertura}


@dataclass
class Empresa:
    id: str
    nome: str
    segmento: str
    metrica: str
    campanhas: list[Campanha]

    @property
    def atual(self) -> Janela:
        return somar_janelas(c.atual for c in self.campanhas)

    @property
    def base(self) -> Janela:
        return somar_janelas(c.base for c in self.campanhas)

    @property
    def alertas(self) -> list[Alerta]:
        return [c.alerta for c in self.campanhas if c.alerta]

    def resumo(self) -> dict:
        atual, base = self.atual, self.base
        valor_atual, valor_base = atual.metrica(self.metrica), base.metrica(self.metrica)
        gasto_7 = sum(c.gasto_diario * 7 for c in self.campanhas)
        if self.metrica == "CPA":
            resultados = sum(c.gasto_diario * 7 / c.previsao_em(7).p50 for c in self.campanhas)
            previsto = gasto_7 / resultados if resultados else 0.0
        else:
            receita = sum(c.gasto_diario * 7 * c.previsao_em(7).p50 for c in self.campanhas)
            previsto = receita / gasto_7 if gasto_7 else 0.0
        variacao = valor_atual / valor_base - 1 if valor_base else 0.0
        piora = variacao if self.metrica == "CPA" else -variacao
        return {
            "gasto": atual.gasto,
            "variacao_gasto": atual.gasto / (base.gasto / 2) - 1 if base.gasto else 0.0,
            "valor_atual": valor_atual,
            "variacao": variacao,
            "gravidade": classificar(piora),
            "previsto_7": previsto,
            "verba_em_risco": sum(a.verba_em_risco for a in self.alertas if a.estado != "descartado"),
            "alertas_abertos": sum(1 for a in self.alertas if a.estado == "aberto"),
        }


def somar(dias: list[Dia]) -> Janela:
    return Janela(
        gasto=sum(d.gasto for d in dias),
        impressoes=sum(d.impressoes for d in dias),
        cliques=sum(d.cliques for d in dias),
        conversoes=sum(d.conversoes for d in dias),
        valor=sum(d.valor for d in dias),
    )


def somar_janelas(janelas) -> Janela:
    janelas = list(janelas)
    return Janela(
        gasto=sum(j.gasto for j in janelas),
        impressoes=sum(j.impressoes for j in janelas),
        cliques=sum(j.cliques for j in janelas),
        conversoes=sum(j.conversoes for j in janelas),
        valor=sum(j.valor for j in janelas),
    )


def classificar(piora: float) -> str:
    if piora >= LIMIAR_CRITICO:
        return "critico"
    if piora >= LIMIAR_ATENCAO:
        return "atencao"
    return "normal"


def _gerar_dias(semente: int, gasto: float, cpm: float, ctr: float, conv: float,
                ticket: float, quebra: tuple[str, int, float] | None) -> list[Dia]:
    rng = random.Random(semente)
    dias = []
    for i in range(DIAS_HISTORICO):
        dia = HOJE - timedelta(days=DIAS_HISTORICO - 1 - i)
        fim_de_semana = dia.weekday() >= 5
        g = gasto * rng.uniform(0.9, 1.1)
        c_cpm = cpm * rng.uniform(0.94, 1.06) * (0.9 if fim_de_semana else 1.0)
        c_ctr = ctr * rng.uniform(0.93, 1.07)
        c_conv = conv * rng.uniform(0.9, 1.1) * (0.88 if fim_de_semana else 1.0)
        if quebra and i >= quebra[1]:
            fator, _, multiplicador = quebra
            if fator == "cpm":
                c_cpm *= multiplicador
            elif fator == "ctr":
                c_ctr *= multiplicador
            else:
                c_conv *= multiplicador
        impressoes = round(g / c_cpm * 1000)
        cliques = round(impressoes * c_ctr)
        conversoes_reais = cliques * c_conv
        provisorio = i > ULTIMO_FECHADO
        if provisorio:
            conversoes_reais *= ATRASO_ATRIBUICAO[i - ULTIMO_FECHADO - 1]
        conversoes = max(1, round(conversoes_reais))
        valor = conversoes * ticket * rng.uniform(0.9, 1.1)
        dias.append(Dia(dia, round(g, 2), impressoes, cliques, conversoes, round(valor, 2), provisorio))
    return dias


# (id, nome, segmento, métrica, [(id, nome, objetivo, parâmetros, quebra)])
# A quebra injeta uma mudança de nível: (fator, índice do dia, multiplicador).
_EMPRESAS = [
    ("parceira-a", "Parceira A", "Estética e depilação", "CPA", [
        ("a-laser", "Captação | Depilação a laser", "Leads",
         dict(gasto=95, cpm=18.0, ctr=0.021, conv=0.085, ticket=0.0), ("cpm", 33, 1.5)),
        ("a-unhas", "Captação | Unhas em gel", "Leads",
         dict(gasto=40, cpm=14.0, ctr=0.024, conv=0.07, ticket=0.0), None),
    ]),
    ("parceira-b", "Parceira B", "Advocacia trabalhista", "CPA", [
        ("b-consulta", "Leads | Consulta trabalhista", "Leads",
         dict(gasto=120, cpm=26.0, ctr=0.015, conv=0.06, ticket=0.0), ("ctr", 34, 0.78)),
        ("b-remarketing", "Leads | Remarketing do site", "Leads",
         dict(gasto=35, cpm=31.0, ctr=0.022, conv=0.09, ticket=0.0), None),
    ]),
    ("parceira-c", "Parceira C", "Loja virtual de moda", "ROAS", [
        ("c-verao", "Vendas | Coleção de verão", "Vendas",
         dict(gasto=180, cpm=22.0, ctr=0.018, conv=0.028, ticket=189.0), ("conv", 33, 0.62)),
        ("c-catalogo", "Vendas | Catálogo completo", "Vendas",
         dict(gasto=90, cpm=19.0, ctr=0.02, conv=0.024, ticket=154.0), None),
        ("c-carrinho", "Vendas | Carrinho abandonado", "Vendas",
         dict(gasto=30, cpm=35.0, ctr=0.03, conv=0.06, ticket=172.0), None),
    ]),
]

FEEDBACK: dict[str, str] = {}


def _explicacao(c: Campanha, verba: float) -> str:
    principal = c.culpado()
    direcao = "subiu" if c.variacao > 0 else "caiu"
    movimento = "subiu" if principal.variacao > 0 else "caiu"
    return (
        f"O {c.metrica} {direcao} {abs(c.variacao) * 100:.0f}% na última semana fechada, "
        f"comparado às duas semanas anteriores. {ARTIGO[principal.fator].capitalize()} "
        f"{principal.rotulo.lower()} {movimento} "
        f"{abs(principal.variacao) * 100:.0f}% no mesmo período. Mantido o ritmo de gasto, "
        f"cerca de {brl(verba, 0)} dos próximos 7 dias compram menos resultado do que "
        f"comprariam antes."
    )


def _detectar(c: Campanha, empresa: tuple) -> Alerta | None:
    gravidade = classificar(c.piora)
    if gravidade == "normal":
        return None
    gasto_7 = c.gasto_diario * 7
    if c.metrica == "CPA":
        verba = gasto_7 * (1 - c.valor_base / c.valor_atual)
    else:
        verba = gasto_7 * (1 - c.valor_atual / c.valor_base)
    detectado = c.dias[ULTIMO_FECHADO].data
    for i in range(ULTIMO_FECHADO - 13, ULTIMO_FECHADO + 1):
        valor = c.movel(i)
        piora = valor / c.valor_base - 1 if c.metrica == "CPA" else 1 - valor / c.valor_base
        if piora >= LIMIAR_ATENCAO:
            detectado = c.dias[i].data
            break
    return Alerta(
        id=f"al-{c.id}",
        empresa_id=empresa[0],
        empresa_nome=empresa[1],
        campanha_id=c.id,
        campanha_nome=c.nome,
        metrica=c.metrica,
        variacao=c.variacao,
        gravidade=gravidade,
        causa=NOME_FATOR[c.culpado().fator].capitalize(),
        verba_em_risco=max(0.0, verba),
        detectado_em=detectado,
        explicacao=_explicacao(c, max(0.0, verba)),
    )


def _montar() -> dict[str, Empresa]:
    empresas = {}
    semente = 20260917
    for empresa in _EMPRESAS:
        eid, nome, segmento, metrica, campanhas = empresa
        lista = []
        for cid, cnome, objetivo, parametros, quebra in campanhas:
            semente += 1
            campanha = Campanha(cid, cnome, objetivo, eid, metrica, _gerar_dias(semente, **parametros, quebra=quebra))
            campanha.alerta = _detectar(campanha, empresa)
            lista.append(campanha)
        empresas[eid] = Empresa(eid, nome, segmento, metrica, lista)
    return empresas


EMPRESAS = _montar()


def empresas() -> list[Empresa]:
    return list(EMPRESAS.values())


def empresa(empresa_id: str | None) -> Empresa | None:
    if empresa_id is None:
        return empresas()[0]
    return EMPRESAS.get(empresa_id)


def campanha(campanha_id: str) -> tuple[Empresa, Campanha] | None:
    for e in EMPRESAS.values():
        for c in e.campanhas:
            if c.id == campanha_id:
                return e, c
    return None


def alertas(empresa_id: str | None = None) -> list[Alerta]:
    lista = [a for e in EMPRESAS.values() for a in e.alertas if empresa_id in (None, e.id)]
    return sorted(lista, key=lambda a: a.verba_em_risco, reverse=True)


def alerta(alerta_id: str) -> Alerta | None:
    return next((a for a in alertas() if a.id == alerta_id), None)


def registrar_feedback(alerta_id: str, acao: str) -> None:
    if acao == "reabrir":
        FEEDBACK.pop(alerta_id, None)
    else:
        FEEDBACK[alerta_id] = "confirmado" if acao == "confirmar" else "descartado"


def reiniciar_feedback() -> None:
    FEEDBACK.clear()


def periodo_atual() -> tuple[date, date]:
    return (
        HOJE - timedelta(days=DIAS_PROVISORIOS + JANELA_ATUAL - 1),
        HOJE - timedelta(days=DIAS_PROVISORIOS),
    )
