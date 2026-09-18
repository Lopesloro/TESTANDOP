"""Texto da tela do projeto: ideia, integrantes, extensão, tecnologias e andamento."""

PROJETO = {
    "nome": "Radar de Campanha",
    "disciplina": "Projeto Integrador VI",
    "curso": "Engenharia de Software",
    "codigo": "12563",
    "instituicao": "PUC-Campinas",
    "semestre": "2º semestre de 2026",
    "orientadora": "Profa. Sílvia C. de Matos Soares",
    "repositorio": "https://github.com/Lopesloro/TESTANDOP",
}

INTEGRANTES = [
    "Gabriel Lopes Londe Rodrigues",
    "Nicolas Marques Linares",
    "Matheus Rocafa Moraes",
]

IDEIA = [
    "Pequenas e médias empresas descobrem tarde que o custo por lead dobrou. "
    "O Gerenciador de Anúncios mostra o que já aconteceu, e quando alguém olha, "
    "a verba da semana já foi embora.",
    "O Radar de Campanha olha para frente. Ele prevê o custo por lead (CPA) e o "
    "retorno sobre o investimento em anúncio (ROAS) de cada campanha para os "
    "próximos 7 e 14 dias, sempre com uma faixa de incerteza, e compara todo dia "
    "o que aconteceu com o que era esperado.",
    "Quando uma campanha sai da faixa, o sistema dispara um alerta dizendo qual "
    "parte da conta se moveu — custo por mil impressões, taxa de clique ou taxa "
    "de conversão — e quanto de verba está em risco. O sistema não cria, não pausa "
    "e não altera campanhas: a decisão continua com quem gerencia a conta.",
]

CIRCULO_DOURADO = [
    (
        "Por quê",
        "A verba de anúncio de uma empresa pequena não aguenta uma semana ruim, e "
        "a semana ruim só aparece no relatório depois de paga.",
    ),
    (
        "Como",
        "Previsão por quantis do CPA e do ROAS, comparação diária com o realizado e "
        "detecção de mudança de nível, com a explicação redigida por um modelo de "
        "linguagem a partir dos números.",
    ),
    (
        "O quê",
        "Um site com painel de previsão para 7 e 14 dias e uma fila de alertas com "
        "causa provável e verba em risco.",
    ),
]

EXTENSAO = [
    {
        "atividade": "Entrevista de levantamento",
        "com_quem": "Responsável pelo marketing de cada empresa parceira",
        "entrega": "Ata e lista de requisitos",
        "quando": "Sprint 1",
    },
    {
        "atividade": "Autorização de uso de dados",
        "com_quem": "Representante legal da empresa",
        "entrega": "Termo assinado com finalidade, escopo, prazo de retenção e revogação",
        "quando": "Sprint 1",
    },
    {
        "atividade": "Acesso aos dados das campanhas",
        "com_quem": "Quem administra a conta de anúncios",
        "entrega": "Acesso somente leitura ou exportação periódica",
        "quando": "Sprint 1",
    },
    {
        "atividade": "Validação do protótipo",
        "com_quem": "Empresas parceiras",
        "entrega": "Aceite registrado das telas",
        "quando": "Sprint 4",
    },
    {
        "atividade": "Validação final",
        "com_quem": "Empresas parceiras",
        "entrega": "Termo de aceite do projeto",
        "quando": "Sprint 6",
    },
]

TECNOLOGIAS = [
    ("Interface", "FastAPI, Jinja2 e HTMX, com o HTML montado no servidor e CSS próprio."),
    (
        "Dados",
        "PostgreSQL, pandas e a API de Marketing da Meta, com importação por planilha "
        "como caminho alternativo.",
    ),
    (
        "Inteligência artificial",
        "scikit-learn e statsmodels para previsão por quantis e detecção de mudança de "
        "nível; um modelo de linguagem para redigir a explicação de cada alerta.",
    ),
    (
        "Gráficos",
        "Python no servidor: Matplotlib e Plotly nos gráficos finais, SVG gerado pelo "
        "próprio backend nas telas.",
    ),
    (
        "Qualidade e segurança",
        "pytest, Playwright, bandit, pip-audit e gitleaks rodando no GitHub Actions em "
        "todo pull request.",
    ),
    ("Publicação", "Render, com banco PostgreSQL gerenciado."),
]

SPRINTS = [
    ("Sprint 0", "Fundação", "22/09 a 28/09", "andamento"),
    ("Sprint 1", "Parceiros, dados, telas e segurança", "29/09 a 12/10", "andamento"),
    ("Sprint 2", "Linha de base e previsão", "13/10 a 26/10", "a-fazer"),
    ("Sprint 3", "Anomalia, diagnóstico e explicação", "27/10 a 09/11", "a-fazer"),
    ("Sprint 4", "Gráficos e modelagem formal", "10/11 a 23/11", "a-fazer"),
    ("Sprint 5", "Testes, validação e publicação", "24/11 a 07/12", "a-fazer"),
    ("Sprint 6", "Entrega acadêmica", "a partir de 08/12", "a-fazer"),
]

ROTULO_ESTADO = {"andamento": "Em andamento", "a-fazer": "A fazer", "feito": "Feito"}
