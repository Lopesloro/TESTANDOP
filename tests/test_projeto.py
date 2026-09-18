from fastapi.testclient import TestClient

from app.web import app

cliente = TestClient(app)


def test_saude_responde():
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json()["estado"] == "ok"


def test_tela_do_projeto_mostra_os_integrantes():
    html = cliente.get("/").text
    assert "Gabriel Lopes Londe Rodrigues" in html
    assert "Nicolas Marques Linares" in html
    assert "Matheus Rocafa Moraes" in html
    assert "Sílvia C. de Matos Soares" in html
    assert "Nicolas Marques Linares e Matheus Rocafa Moraes." in html


def test_tela_do_projeto_mostra_a_ideia():
    html = cliente.get("/").text
    assert "7 a 14 dias" in html
    assert "custo por lead" in html
    assert "não cria, não pausa" in html


def test_tela_do_projeto_mostra_a_extensao():
    html = cliente.get("/").text
    assert "62 horas" in html
    assert "Autorização de uso de dados" in html
    assert "Termo de aceite do projeto" in html


def test_tela_do_projeto_mostra_as_tecnologias_e_o_andamento():
    html = cliente.get("/").text
    for area in ("Interface", "Inteligência artificial", "Qualidade e segurança"):
        assert area in html
    assert "Sprint 6" in html
    assert "pull request" in html


def test_conteudo_nao_depende_de_javascript():
    """Nada de conteúdo injetado por script: o texto já vem no HTML do servidor."""
    html = cliente.get("/").text
    assert "Prever o custo antes que a verba queime" in html
    assert 'id="hero-titulo"' in html


def test_css_usa_o_azul_da_meta_e_nenhuma_sombra():
    css = cliente.get("/static/css/app.css").text
    assert "#0866FF" in css
    assert "box-shadow" not in css
    assert "prefers-reduced-motion" in css


def test_rota_inexistente_da_404():
    assert cliente.get("/nao-existe").status_code == 404
