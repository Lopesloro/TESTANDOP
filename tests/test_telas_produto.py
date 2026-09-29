import pytest
from fastapi.testclient import TestClient

from app import demo, formatos
from app.web import app

cliente = TestClient(app)
sem_seguir = TestClient(app, follow_redirects=False)

TELAS = [
    "/painel",
    "/painel?empresa=parceira-c",
    "/previsao/a-laser",
    "/previsao/c-verao?horizonte=7",
    "/alertas",
    "/diagnostico/a-laser",
    "/diagnostico/c-verao",
    "/acuracia",
]


@pytest.fixture(autouse=True)
def feedback_limpo():
    demo.reiniciar_feedback()
    yield
    demo.reiniciar_feedback()


@pytest.mark.parametrize("rota", TELAS)
def test_tela_responde_e_avisa_que_os_dados_sao_de_demonstracao(rota):
    resposta = cliente.get(rota)
    assert resposta.status_code == 200
    assert "Dados de demonstração" in resposta.text


def test_menu_tem_as_seis_telas():
    html = cliente.get("/painel").text
    for rotulo in ("Projeto", "Painel", "Previsão", "Alertas", "Diagnóstico", "Acurácia"):
        assert f">{rotulo}</a>" in html


def test_rotas_sem_campanha_redirecionam_para_a_primeira():
    assert sem_seguir.get("/previsao").headers["location"] == "/previsao/a-laser"
    assert sem_seguir.get("/previsao?empresa=parceira-b").headers["location"] == "/previsao/b-consulta"
    assert sem_seguir.get("/diagnostico").status_code == 303


def test_empresa_e_campanha_inexistentes_dao_404():
    assert cliente.get("/painel?empresa=nao-existe").status_code == 404
    assert cliente.get("/previsao/nao-existe").status_code == 404
    assert cliente.get("/diagnostico/nao-existe").status_code == 404
    assert cliente.get("/acuracia?empresa=parceira-a&campanha=c-verao").status_code == 404


def test_horizonte_so_aceita_7_ou_14():
    assert cliente.get("/previsao/a-laser?horizonte=7").status_code == 200
    assert cliente.get("/previsao/a-laser?horizonte=30").status_code == 400


def test_loja_virtual_usa_roas_e_as_demais_usam_cpa():
    assert "ROAS da semana" in cliente.get("/painel?empresa=parceira-c").text
    assert "CPA da semana" in cliente.get("/painel?empresa=parceira-a").text


def test_previsao_traz_grafico_com_dica_em_cada_ponto_e_tabela_dia_a_dia():
    html = cliente.get("/previsao/a-laser?horizonte=7").text
    assert '<svg class="grafico__svg"' in html
    assert "previsto R$" in html
    assert html.count("<tr>") >= 1 + 7


def test_dias_provisorios_ficam_fora_da_previsao():
    _, campanha = demo.campanha("a-laser")
    ultimo_fechado = campanha.movel(demo.ULTIMO_FECHADO)
    assert campanha.previsao_em(1).p50 == pytest.approx(ultimo_fechado)
    assert all(d.provisorio for d in campanha.dias[-demo.DIAS_PROVISORIOS:])


def test_faixa_se_abre_com_o_horizonte():
    _, campanha = demo.campanha("b-consulta")
    curta, longa = campanha.previsao_em(7), campanha.previsao_em(14)
    assert curta.p10 <= curta.p50 <= curta.p90
    assert (longa.p90 - longa.p10) > (curta.p90 - curta.p10)


def test_alertas_saem_das_quebras_injetadas_e_ordenados_por_verba():
    alertas = demo.alertas()
    assert {a.campanha_id for a in alertas} == {"a-laser", "b-consulta", "c-verao"}
    verbas = [a.verba_em_risco for a in alertas]
    assert verbas == sorted(verbas, reverse=True)


def test_diagnostico_aponta_o_fator_que_mudou():
    assert demo.campanha("a-laser")[1].culpado().fator == "cpm"
    assert demo.campanha("b-consulta")[1].culpado().fator == "ctr"
    assert demo.campanha("c-verao")[1].culpado().fator == "conv"
    html = cliente.get("/diagnostico/a-laser").text
    assert "do custo por mil impressões" in html


def test_confirmar_descartar_e_reabrir_alerta():
    resposta = sem_seguir.post("/alertas/al-a-laser", data={"acao": "confirmar", "empresa": "parceira-a"})
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/alertas?empresa=parceira-a#alerta-al-a-laser"
    assert "Confirmado nesta demonstração" in cliente.get("/alertas").text

    sem_seguir.post("/alertas/al-b-consulta", data={"acao": "descartar"})
    html = cliente.get("/acuracia").text
    assert "50%" in html

    sem_seguir.post("/alertas/al-a-laser", data={"acao": "reabrir"})
    assert demo.alerta("al-a-laser").estado == "aberto"


def test_feedback_rejeita_acao_invalida_e_alerta_inexistente():
    assert sem_seguir.post("/alertas/al-a-laser", data={"acao": "apagar"}).status_code == 400
    assert sem_seguir.post("/alertas/nao-existe", data={"acao": "confirmar"}).status_code == 404


def test_redirecionamento_do_feedback_ignora_empresa_desconhecida():
    resposta = sem_seguir.post("/alertas/al-a-laser", data={"acao": "confirmar", "empresa": "//evil.example"})
    assert resposta.headers["location"] == "/alertas#alerta-al-a-laser"


def test_dados_de_demonstracao_sao_deterministicos():
    primeira = [d.gasto for d in demo.campanha("c-verao")[1].dias]
    segunda = [d.gasto for d in demo._gerar_dias(20260917 + 5, 180, 22.0, 0.018, 0.028, 189.0, ("conv", 33, 0.62))]
    assert primeira == segunda


def test_formatos_brasileiros():
    assert formatos.brl(1234.5) == "R$ 1.234,50"
    assert formatos.pct(0.123) == "+12%"
    assert formatos.pct(-0.05, 1) == "−5,0%"
    assert formatos.metrica(4.321, "ROAS") == "4,32"
