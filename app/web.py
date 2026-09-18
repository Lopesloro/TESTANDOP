"""Aplicação web do Radar de Campanha."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import conteudo

VERSAO = "0.1.0"
BASE = Path(__file__).resolve().parent

app = FastAPI(title=conteudo.PROJETO["nome"], version=VERSAO, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

MENU = [
    {"id": "projeto", "rotulo": "O projeto", "href": "/#projeto"},
    {"id": "quem-faz", "rotulo": "Quem faz", "href": "/#quem-faz"},
    {"id": "extensao", "rotulo": "Extensão", "href": "/#extensao"},
    {"id": "tecnologias", "rotulo": "Tecnologias", "href": "/#tecnologias"},
    {"id": "andamento", "rotulo": "Andamento", "href": "/#andamento"},
]

CHAMADA_HERO = {"rotulo": "Conhecer o projeto", "href": "#projeto"}


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


@app.get("/saude")
def saude() -> dict:
    return {"estado": "ok", "versao": VERSAO}
