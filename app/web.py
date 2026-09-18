"""Aplicação web do Radar de Campanha."""

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import conteudo, demo, formatos
from app.graficos import svg

VERSAO = "0.2.0"
BASE = Path(__file__).resolve().parent

app = FastAPI(title=conteudo.PROJETO["nome"], version=VERSAO, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.filters.update(
    brl=formatos.brl,
    pct=formatos.pct,
    decimal=formatos.decimal,
    inteiro=formatos.inteiro,
    data_curta=formatos.data_curta,
    data_longa=formatos.data_longa,
    metrica=formatos.metrica,
)

MENU = [
    {"id": "projeto", "rotulo": "Projeto", "href": "/"},
    {"id": "painel", "rotulo": "Painel", "href": "/painel"},
    {"id": "previsao", "rotulo": "Previsão", "href": "/previsao"},
    {"id": "alertas", "rotulo": "Alertas", "href": "/alertas"},
    {"id": "diagnostico", "rotulo": "Diagnóstico", "href": "/diagnostico"},
    {"id": "acuracia", "rotulo": "Acurácia", "href": "/acuracia"},
]

CHAMADA_HERO = {"rotulo": "Abrir o painel", "href": "/painel"}
HORIZONTES = (7, 14)
ACOES_ALERTA = {"confirmar", "descartar", "reabrir"}


def pagina(request: Request, nome: str, ativo: str, **contexto) -> HTMLResponse:
    """Renderiza um template com o contexto comum a todas as telas."""
    return templates.TemplateResponse(
        request,
        nome,
        {
            "projeto": conteudo.PROJETO,
            "integrantes": conteudo.INTEGRANTES,
            "versao": VERSAO,
            "menu": MENU,
            "ativo": ativo,
            **contexto,
        },
    )


def _empresa_ou_404(empresa_id: str | None) -> demo.Empresa:
    empresa = demo.empresa(empresa_id)
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa


def _campanha_ou_404(campanha_id: str) -> tuple[demo.Empresa, demo.Campanha]:
    achado = demo.campanha(campanha_id)
    if achado is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return achado


@app.get("/", response_class=HTMLResponse)
def tela_projeto(request: Request) -> HTMLResponse:
    return pagina(
        request,
        "projeto.html",
        "projeto",
        ideia=conteudo.IDEIA,
        circulo=conteudo.CIRCULO_DOURADO,
        extensao=conteudo.EXTENSAO,
        tecnologias=conteudo.TECNOLOGIAS,
        sprints=conteudo.SPRINTS,
        rotulo_estado=conteudo.ROTULO_ESTADO,
        chamada=CHAMADA_HERO,
    )


@app.get("/painel", response_class=HTMLResponse)
def tela_painel(request: Request, empresa: str | None = None) -> HTMLResponse:
    atual = _empresa_ou_404(empresa)
    tendencias = {
        c.id: svg.sparkline(
            [valor for _, valor in c.serie(28)],
            f"Tendência de 28 dias do {c.metrica} de {c.nome}",
        )
        for c in atual.campanhas
    }
    inicio, fim = demo.periodo_atual()
    return pagina(
        request,
        "painel.html",
        "painel",
        empresa=atual,
        empresas=demo.empresas(),
        resumo=atual.resumo(),
        tendencias=tendencias,
        inicio=inicio,
        fim=fim,
    )


@app.get("/previsao")
def previsao_inicial(empresa: str | None = None) -> RedirectResponse:
    atual = _empresa_ou_404(empresa)
    return RedirectResponse(f"/previsao/{atual.campanhas[0].id}", status_code=303)


@app.get("/previsao/{campanha_id}", response_class=HTMLResponse)
def tela_previsao(request: Request, campanha_id: str, horizonte: int = 14) -> HTMLResponse:
    if horizonte not in HORIZONTES:
        raise HTTPException(status_code=400, detail="O horizonte deve ser 7 ou 14 dias")
    empresa, campanha = _campanha_ou_404(campanha_id)
    previsao = campanha.previsao[:horizonte]
    ponto = campanha.previsao_em(horizonte)
    gasto_projetado = campanha.gasto_diario * horizonte
    if campanha.metrica == "CPA":
        esperado = {
            "rotulo": "Leads esperados",
            "minimo": formatos.inteiro(gasto_projetado / ponto.p90) if ponto.p90 else "0",
            "maximo": formatos.inteiro(gasto_projetado / ponto.p10) if ponto.p10 else "sem teto",
        }
    else:
        esperado = {
            "rotulo": "Receita esperada",
            "minimo": formatos.brl(gasto_projetado * ponto.p10, 0),
            "maximo": formatos.brl(gasto_projetado * ponto.p90, 0),
        }
    grafico = svg.leque(
        campanha.serie(28),
        previsao,
        provisorio_desde=campanha.dias[demo.ULTIMO_FECHADO + 1].data,
        hoje=demo.HOJE,
        unidade=campanha.metrica,
        titulo=f"{campanha.metrica} de {campanha.nome}: 28 dias de histórico e previsão para {horizonte} dias",
    )
    return pagina(
        request,
        "previsao.html",
        "previsao",
        empresa=empresa,
        campanha=campanha,
        horizonte=horizonte,
        horizontes=HORIZONTES,
        grafico=grafico,
        ponto=ponto,
        previsao=previsao,
        gasto_projetado=gasto_projetado,
        esperado=esperado,
        dias_provisorios=demo.DIAS_PROVISORIOS,
    )


@app.get("/alertas", response_class=HTMLResponse)
def tela_alertas(request: Request, empresa: str | None = None) -> HTMLResponse:
    if empresa is not None:
        _empresa_ou_404(empresa)
    return pagina(
        request,
        "alertas.html",
        "alertas",
        alertas=demo.alertas(empresa),
        empresas=demo.empresas(),
        filtro=empresa,
    )


@app.post("/alertas/{alerta_id}")
def registrar_alerta(alerta_id: str, acao: str = Form(...), empresa: str = Form("")) -> RedirectResponse:
    if acao not in ACOES_ALERTA:
        raise HTTPException(status_code=400, detail="Ação inválida")
    if demo.alerta(alerta_id) is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    demo.registrar_feedback(alerta_id, acao)
    filtro = f"?empresa={empresa}" if empresa and demo.empresa(empresa) else ""
    return RedirectResponse(f"/alertas{filtro}#alerta-{alerta_id}", status_code=303)


@app.get("/diagnostico")
def diagnostico_inicial(empresa: str | None = None) -> RedirectResponse:
    atual = _empresa_ou_404(empresa)
    pior = max(atual.campanhas, key=lambda c: c.piora)
    return RedirectResponse(f"/diagnostico/{pior.id}", status_code=303)


@app.get("/diagnostico/{campanha_id}", response_class=HTMLResponse)
def tela_diagnostico(request: Request, campanha_id: str) -> HTMLResponse:
    empresa, campanha = _campanha_ou_404(campanha_id)
    antes, depois = campanha.base, campanha.atual
    efeitos = campanha.efeitos()
    total = depois.cpa / antes.cpa - 1
    efeito = {e.fator: e for e in efeitos}
    linhas = [
        ("Custo por mil impressões (CPM)", formatos.brl(antes.cpm), formatos.brl(depois.cpm),
         formatos.pct(efeito["cpm"].variacao), formatos.pct(efeito["cpm"].efeito_cpa)),
        ("Taxa de clique (CTR)", formatos.pct(antes.ctr, 2, False), formatos.pct(depois.ctr, 2, False),
         formatos.pct(efeito["ctr"].variacao), formatos.pct(efeito["ctr"].efeito_cpa)),
        ("Taxa de conversão", formatos.pct(antes.taxa_conversao, 1, False),
         formatos.pct(depois.taxa_conversao, 1, False),
         formatos.pct(efeito["conv"].variacao), formatos.pct(efeito["conv"].efeito_cpa)),
        ("Custo por resultado (CPA)", formatos.brl(antes.cpa), formatos.brl(depois.cpa),
         formatos.pct(total), formatos.pct(total)),
    ]
    if campanha.metrica == "ROAS":
        linhas += [
            ("Ticket médio", formatos.brl(antes.ticket), formatos.brl(depois.ticket),
             formatos.pct(depois.ticket / antes.ticket - 1), "—"),
            ("Retorno sobre o gasto (ROAS)", formatos.decimal(antes.roas), formatos.decimal(depois.roas),
             formatos.pct(depois.roas / antes.roas - 1), "—"),
        ]
    grafico = svg.cascata(efeitos, total, f"Efeito de cada fator no CPA de {campanha.nome}")
    inicio, fim = demo.periodo_atual()
    return pagina(
        request,
        "diagnostico.html",
        "diagnostico",
        empresa=empresa,
        campanha=campanha,
        linhas=linhas,
        grafico=grafico,
        frase=campanha.frase_diagnostico(),
        inicio=inicio,
        fim=fim,
    )


@app.get("/acuracia", response_class=HTMLResponse)
def tela_acuracia(request: Request, empresa: str | None = None, campanha: str | None = None) -> HTMLResponse:
    atual = _empresa_ou_404(empresa)
    medidas = {c.id: c.acuracia() for c in atual.campanhas}
    if campanha is None:
        escolhida = atual.campanhas[0]
    else:
        escolhida = next((c for c in atual.campanhas if c.id == campanha), None)
        if escolhida is None:
            raise HTTPException(status_code=404, detail="Campanha não encontrada nesta empresa")
    grafico = svg.previsto_realizado(
        medidas[escolhida.id]["pontos"],
        escolhida.metrica,
        f"{escolhida.metrica} previsto 7 dias antes e realizado: {escolhida.nome}",
    )
    todos = demo.alertas()
    confirmados = sum(1 for a in todos if a.estado == "confirmado")
    descartados = sum(1 for a in todos if a.estado == "descartado")
    julgados = confirmados + descartados
    return pagina(
        request,
        "acuracia.html",
        "acuracia",
        empresa=atual,
        empresas=demo.empresas(),
        medidas=medidas,
        escolhida=escolhida,
        grafico=grafico,
        feedback={
            "confirmados": confirmados,
            "descartados": descartados,
            "abertos": len(todos) - julgados,
            "precisao": confirmados / julgados if julgados else None,
        },
    )


@app.get("/saude")
def saude() -> dict:
    return {"estado": "ok", "versao": VERSAO}
