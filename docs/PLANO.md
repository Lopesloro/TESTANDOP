# PI VI — Previsão de CPA/ROAS e alerta de anomalia em campanhas Meta Ads

## Contexto

O PDF `PI VI Especificacao Documentacao de Projeto.docx.pdf` é a especificação de
documentação final da disciplina 12563 (Engenharia de Software, PUC-Campinas,
2º semestre de 2026): 16 seções em ABNT, 62 horas de extensão com 2 a 5
representantes da comunidade externa, vídeo, slides e banner. A especificação
define o **formato da entrega**, não o produto.

**Produto:** software que prevê o custo por lead (CPA) e o retorno (ROAS) das
campanhas Meta Ads de uma empresa para os próximos **7 a 14 dias**, e dispara
**alerta de anomalia** — queda de desempenho detectada antes que o orçamento
queime.

**Parceiros da extensão:** 2 a 5 clientes da BlueShieldPro, empresas com CNPJ,
que participam da definição, das entrevistas, da validação do protótipo e do
aceite final, e que autorizam o uso dos dados reais das campanhas delas.

**Demonstração:** painel com previsão e alerta de anomalia funcionando sobre
dados reais de campanha.

Projeto **novo**, base de dados própria. Nenhuma conta Meta pessoal ou da
BlueShieldPro entra no projeto sem pedido explícito.

---

## Aderência à especificação (verificação item a item)

| Exigência do PDF | Como a ideia atende | Ponto de atenção |
|---|---|---|
| Tecnologia atual: IA | Previsão de série temporal + detecção de anomalia + LLM explicando | Atende com folga; é IA de ponta a ponta |
| Seção 11.1 Base de dados | Dados reais de campanha dos parceiros, via API da Meta ou exportação | **Depende de autorização formal** — tarefa da Sprint 1 |
| 11.2 Pré-processamento | Consolidação de janela de atribuição, tratamento de zero-inflação, normalização por moeda e fuso | Ver risco da atribuição retroativa abaixo |
| 11.3 Modelos | Baseline sazonal, modelo de quantis, detecção de mudança de nível | — |
| 11.4 Treinamento e validação | Validação com origem móvel (*rolling origin*), nunca aleatória | — |
| 11.5 Métricas | sMAPE/MAE da previsão, cobertura do intervalo, precisão/recall do alerta, tempo até detecção | Vira a seção 5.3 |
| 5.3 Requisitos de IA | Limiares mínimos declarados antes do treino | — |
| Seção 3 Representantes | Clientes BSP com CNPJ | 2 a 5, com nome, e-mail, cargo, organização e CNPJ |
| Seção 6 Benchmarking | Madgicx, Revealbot, AdEspresso, Triple Whale | Precisa de tabela e diferencial escrito |
| Seção 8 Protótipos | Figma + aceite dos parceiros | Aceite registrado, não só o link |
| Seção 9 Modelo de dados | MER multiempresa | Isolamento por empresa é requisito, não detalhe |
| Seção 12 Testes | Unit, integração gravada, E2E, avaliação do modelo, bateria de segurança | — |
| 11.7 Cibersegurança | Recorte declarado: **defesa** | Entra como RNF (5.2) e evidência na seção 12 |
| Seção 14 Ética/LGPD | Dado de campanha de terceiro: consentimento, finalidade, retenção, anonimização no relatório | Obrigatório, não decorativo |

**Onde a ideia é mais forte que a anterior:** o alvo é numérico, medido contra o
realizado, e o acerto aparece sozinho — o painel de acurácia é a própria prova da
seção 14. **Onde ela é mais arriscada:** sem histórico suficiente de conversão,
CPA vira número ruidoso; e a Meta revisa dados recentes retroativamente. Os dois
riscos têm contramedida no plano, e ambos viram parágrafo bom no relatório.

---

## Decisões travadas

| Eixo | Decisão |
|---|---|
| Formato | **Site web**, acessado pelo navegador. Não é aplicativo de loja, não há build Android/iOS. Responsivo: no celular abre pelo navegador. PWA (ícone na tela inicial, sem loja) fica como trabalho futuro na seção 15. |
| Pilha | Python full-stack: FastAPI + Jinja2 + HTMX, CSS próprio. Um só deploy. |
| Gráficos | Matplotlib/Plotly server-side, renderizados pelo backend. |
| Front | Segue a skill `padrao-de-sites`, Dialeto **A — Autoridade**, mais as proibições de `Cofre/_ai/design/PADRAO-VISUAL.md`. |
| Dados | Reais dos parceiros (com autorização) + dataset público de Meta/Facebook Ads + gerador sintético para exercitar o pipeline. |
| Cibersegurança | **Só defesa**: hardening, verificação automatizada de controles, conformidade. Nenhum ataque executado. |
| Banco | Postgres (Render). MER relacional multiempresa. |
| Tecnologia atual declarada | Inteligência Artificial (11.1 a 11.5). |

Repositório: [Lopesloro/TESTANDOP](https://github.com/Lopesloro/TESTANDOP)
Título de trabalho: **Radar de Campanha** (confirmar com o time).
Integrantes: Gabriel Lopes Londe Rodrigues e Nicolas Marques Linares.

**Fluxo de trabalho:** cada bloco deste checklist está aberto como issue no
GitHub e entra por pull request. O CI roda os testes em todo PR; nada vai para a
`main` sem aprovação e teste dos integrantes.

---

## Arquitetura

```
app/
  web/          FastAPI + rotas + templates Jinja (HTMX nas telas vivas)
  templates/    base.html + 5 telas; CSS único no Dialeto A
  ingestao/
    meta.py       coleta diária por campanha/conjunto (API ou CSV)
    consolidacao.py  marca o que já é dado fechado e o que ainda vai mudar
  dominio/      Empresa, ContaAnuncio, Campanha, SerieDiaria, Previsao,
                Alerta, Feedback, Usuario, Auditoria
  ia/
    baseline.py     persistência e ingênuo sazonal — a régua
    previsao.py     modelo de quantis: P10 / P50 / P90 para CPA e ROAS
    anomalia.py     resíduo fora da banda + mudança de nível + regra robusta
    diagnostico.py  decomposição do CPA em CPM × CTR × taxa de conversão
    suavizacao.py   encolhimento bayesiano para taxa com pouca conversão
    avaliacao.py    origem móvel, sMAPE, cobertura, precisão/recall, tempo até detecção
    llm.py          explicação do alerta e da previsão, ancorada nos números
    aprendizado.py  feedback do usuário -> limiar recalibrado
  graficos/     um arquivo por gráfico
  seguranca/    auth, isolamento por empresa, rate limit, cabeçalhos, segredos
  dados/        migrações, seeds, gerador sintético, carregador do dataset público
testes/         unit, integracao, e2e, seguranca, modelo
docs/           relatório em construção, seção a seção; evidências
```

**Fluxo:** coleta diária → consolidação (só dado fechado alimenta treino) →
previsão P10/P50/P90 para 7 e 14 dias → comparação do realizado contra a banda →
alerta com causa provável → LLM redige → usuário confirma ou descarta → o
feedback recalibra o limiar.

**O que "aprende com o uso" significa aqui (escrever assim no relatório):** não é
fine-tuning de pesos. São três mecanismos honestos — (a) cada dia novo entra na
série e o modelo é reajustado; (b) alerta confirmado ou descartado move o limiar
de disparo, reduzindo falso alarme; (c) casos passados parecidos entram como
exemplo no prompt do LLM. Prometer mais que isso na banca é insustentável.

---

# CHECKLIST

## Sprint 0 — Fundação (22/09 – 28/09)

- [ ] Repo `TESTANDOP` com `.gitignore`, `README.md`, modelo de PR e licença
- [ ] Dependências: fastapi, uvicorn, jinja2, sqlalchemy, alembic, psycopg,
      pandas, numpy, scikit-learn, statsmodels, matplotlib, plotly, pytest,
      httpx, bandit, pip-audit, ruff
- [ ] Postgres local (docker) + Postgres no Render; Alembic inicializado
- [ ] FastAPI subindo com `/saude` (versão + estado do banco)
- [ ] `.env.example` sem nenhum valor real; `gitleaks` em pre-commit
- [ ] Definir time, papéis e o número do Time X (arquivo final: `Time X.docx`)
- [ ] Criar `docs/relatorio/` com as 16 seções vazias, cada uma com o trecho da
      especificação colado como lembrete do que ela cobra
- [ ] Abrir o quadro SCRUM (backlog + sprints) — a seção 13 se alimenta dele
      desde o primeiro dia

## Sprint 1 — Parceiros, dados, telas e verificação de segurança (29/09 – 12/10)

> Prioridade declarada: tela + funcionalidade + teste de segurança.

### Parceiros e dados (prazo duro — critério de reprovação)
- [ ] Fechar 2 a 5 empresas com CNPJ: nome, e-mail, cargo do responsável,
      razão social e CNPJ
- [ ] **Termo de autorização de uso de dados** assinado por cada empresa:
      finalidade acadêmica, escopo (métricas de campanha), prazo de retenção,
      direito de revogação. Sem isso, não coletar
- [ ] Definir a via de acesso por empresa: acesso de parceiro no Business Manager
      (somente leitura) **ou** exportação periódica do Gerenciador de Anúncios
- [ ] Roteiro de entrevista escrito; aplicar e lavrar ata de cada conversa
      (é daqui que saem as personas e os requisitos)
- [ ] Abrir a ficha individual de horas de extensão de cada aluno (meta: 62h)
- [ ] Levantar quanto histórico cada empresa tem: dias com gasto, conversões por
      dia, se há valor de compra registrado. **Esse levantamento decide o modelo** —
      sem volume de conversão, o alvo primário vira CPA suavizado e o alerta se
      apoia em métricas de topo (CPM, CTR, visualizações da página)

### Ingestão
- [ ] `ingestao/meta.py`: coleta diária por campanha e por conjunto — gasto,
      impressões, cliques, CPM, CTR, frequência, leads, compras e valor de compra
- [ ] `ingestao/consolidacao.py`: **a janela de atribuição da Meta revisa os dias
      recentes**. Marcar cada linha como provisória ou fechada; treinar e alertar
      só sobre o que fechou, e exibir o provisório com marcação na tela
- [ ] Importador de CSV como caminho alternativo, com o mesmo esquema
- [ ] Carga agendada diária + registro de execução (o que entrou, quando, erros)

### Telas (Dialeto A — Autoridade)
- [ ] Ler `references/dialeto-a.md`, `references/animacoes.md` e
      `references/anti-referencias.md` da skill antes de escrever CSS
- [ ] Propor em lista curta (tipografia, paleta hex, seções, o que vai no topo) e
      só então construir — a skill exige a proposta antes do código
- [ ] Tela 1 — **Painel**: por empresa, CPA e ROAS atuais contra o previsto, com
      a faixa de incerteza e o estado de cada campanha
- [ ] Tela 2 — **Previsão da campanha**: série histórica + leque de previsão de
      7 e 14 dias (P10/P50/P90) e orçamento projetado
- [ ] Tela 3 — **Alertas**: fila por gravidade, causa provável, quanto de verba
      está em risco, botões *confirmar* e *descartar* (alimentam o aprendizado)
- [ ] Tela 4 — **Diagnóstico**: decomposição do CPA em CPM × CTR × taxa de
      conversão, mostrando qual dos três se moveu
- [ ] Tela 5 — **Acurácia**: previsto contra realizado ao longo do tempo e o
      histórico de alertas certos e falsos
- [ ] Conteúdo nasce no HTML; JavaScript só troca estado depois
- [ ] Sem botão flutuante de WhatsApp, sem três colunas de ícone genérico, sem
      contador animado, uma só cor de ação
- [ ] Responsivo a 375px sem rolagem horizontal

### Segurança — defesa e verificação (sem ataque)
- [ ] **Isolamento por empresa**: toda consulta filtra pela empresa do usuário;
      teste automatizado que tenta ler dados de outra empresa e exige 403
- [ ] Autenticação por sessão, senha com Argon2, cookie `HttpOnly`+`Secure`+`SameSite`
- [ ] Token de acesso à API da Meta cifrado em repouso; nunca em log, nunca no repo
- [ ] Rate limit nas rotas de ingestão, de LLM e de exportação
- [ ] Cabeçalhos: CSP sem `unsafe-inline`, HSTS, X-Content-Type-Options, Referrer-Policy
- [ ] CSRF em todo formulário; validação de entrada com Pydantic estrita
- [ ] Trilha de auditoria: quem viu dado de qual empresa e quando
- [ ] Defesa contra injeção de prompt: texto vindo de campanha entra no LLM como
      **dado delimitado**, nunca como instrução; saída do LLM não dispara ação
- [ ] CI: `bandit` (SAST), `pip-audit` (dependências), `gitleaks` (segredos),
      testes de autorização, de cabeçalho e de rate limit
- [ ] Guardar as saídas em `docs/evidencias/seguranca/` — material da seção 12

### Documento
- [ ] Seção 1 Introdução + Círculo Dourado · Seção 2 Objetivos · Seção 3 Representantes
- [ ] Seção 6 Benchmarking: tabela contra Madgicx, Revealbot, AdEspresso
      (e Triple Whale, se couber) + diferencial escrito

## Sprint 2 — Linha de base e previsão (13/10 – 26/10)

- [ ] `dados/publico.py`: dataset público de Meta/Facebook Ads para pré-treino e
      comparação — registrar origem, licença e volume
- [ ] `dados/sintetico.py`: gerador com sazonalidade semanal, ruído de conversão e
      quebras de nível injetadas — serve para medir o detector, nunca para
      apresentar resultado
- [ ] `ia/baseline.py`: **a régua** — repetir o último valor e média dos últimos 7
      dias. Nenhum resultado de modelo é reportado sem a régua ao lado
- [ ] `ia/suavizacao.py`: encolhimento bayesiano da taxa de conversão (Beta-Binomial)
      para campanha com poucas conversões
- [ ] `ia/previsao.py`: previsão de **quantis** P10/P50/P90 para CPA e ROAS em
      horizonte de 7 e 14 dias — prever faixa, nunca só o ponto
  - [ ] Atributos: defasagens de 1/7/14 dias, média móvel, dia da semana, gasto
        planejado, frequência, CPM, CTR, tempo de vida da campanha
  - [ ] Agrupamento hierárquico: campanha nova herda o comportamento da conta
        (partida a frio)
- [ ] Validação com **origem móvel**, nunca embaralhada
- [ ] `ia/avaliacao.py`: sMAPE, MAE, *pinball loss*, cobertura observada do
      intervalo de 80%, tudo contra a régua
- [ ] Declarar as métricas mínimas da seção 5.3, por exemplo:
      sMAPE do CPA em 7 dias ≤ régua − 15% · cobertura do intervalo de 80% entre
      75% e 85% · resposta do painel < 2s (p95)
- [ ] Teste que **falha o CI** se o modelo não superar a régua
- [ ] Documento: Seções 4, 5.1, 5.2, 5.3, 11.1, 11.2

## Sprint 3 — Anomalia, diagnóstico e LLM (27/10 – 09/11)

- [ ] `ia/anomalia.py` em três camadas:
  - [ ] realizado fora da banda P10–P90 por N dias seguidos
  - [ ] mudança de nível (CUSUM ou Page-Hinkley) sobre CPA, CPM e CTR
  - [ ] regra robusta mediana ± k·MAD para série curta
- [ ] Gravidade calculada por **verba em risco**, não só por desvio percentual
- [ ] `ia/diagnostico.py`: decompor a variação do CPA em CPM × CTR × taxa de
      conversão e nomear o culpado ("CPM subiu 38%, CTR estável")
- [ ] `ia/llm.py`: redige o alerta em português a partir dos números calculados —
      o LLM **não** produz métrica, só explica a que recebeu
- [ ] O prompt escreve ingrediente, não resposta pronta: nada de frase-modelo que
      sai literal para o cliente
- [ ] Divergência entre modelo e LLM aparece na tela; o LLM não bloqueia nada
- [ ] `ia/aprendizado.py`: alerta confirmado ou descartado ajusta o limiar; medir
      a queda do falso alarme ao longo das semanas — é a prova de que aprende
- [ ] Métricas do detector: precisão, recall, F1, tempo médio até detecção,
      falsos alarmes por campanha por semana
- [ ] Notificação por e-mail do alerta grave (com preferência por empresa)
- [ ] Teste de regressão do LLM: casos fixos, verificando a forma da saída
- [ ] Documento: Seções 11.3, 11.4, 11.5

## Sprint 4 — Gráficos Python e modelagem formal (10/11 – 23/11)

- [ ] **Aguardar a ideia de gráfico do Gabriel e implementá-la primeiro** — ela
      manda sobre a lista abaixo
- [ ] Conjunto padrão, um arquivo por gráfico:
  - [ ] Leque de previsão: histórico + P10/P50/P90 em 7 e 14 dias
  - [ ] Carta de controle do CPA com limites e pontos de alerta marcados
  - [ ] Cascata do CPA: contribuição de CPM, CTR e taxa de conversão
  - [ ] Previsto contra realizado, com a diagonal e o erro destacado
  - [ ] Mapa de calor dia × campanha de desvio em relação ao previsto
  - [ ] Curva precisão-recall do detector, com o limiar em uso marcado
- [ ] Todo gráfico com eixo rotulado, unidade explícita, legível em P&B
- [ ] Render server-side com cache por hash dos dados
- [ ] Seção 9: MER completo, com a chave de empresa em toda tabela de dado
- [ ] Seção 10: diagrama de arquitetura + tecnologias
- [ ] Seção 7: personas tiradas das entrevistas reais
- [ ] Seção 8: protótipos no Figma, prints legíveis e **aceite registrado** dos
      parceiros

## Sprint 5 — Testes, validação e endurecimento (24/11 – 07/12)

- [ ] Unitários: consolidação, suavização, baseline, avaliação, regras de alerta
- [ ] Integração da camada Meta com **conexão gravada**: fixtures capturadas uma
      vez, testes rodando sem rede
- [ ] Testar a função que o servidor realmente chama, não uma cópia de teste
- [ ] E2E com Playwright nas 5 telas, a 375px e 1280px
- [ ] Clicar em todo botão de ação depois de qualquer mexida em JavaScript
- [ ] Bateria de segurança repetida, com evidência nova
- [ ] Nenhum teste pulado contando como verde (`pytest -ra` mostrando os skips)
- [ ] Deploy no Render com Postgres; reiniciar o serviço e confirmar que
      previsões, alertas e feedback sobreviveram (disco do plano free é descartável)
- [ ] Validação final com os parceiros; ajustes a partir do retorno
- [ ] Documento: Seção 12 (testes e resultados) e Seção 13 (SCRUM: backlog,
      cronograma planejado e cronograma real)

## Sprint 6 — Entrega acadêmica (08/12 – entrega)

- [ ] Seção 14: resultados contra os objetivos; o que não foi atingido e por quê;
      ética, viés (poucas empresas, um nicho, um país), impacto social e LGPD
- [ ] Seção 15: conclusão, limitações e trabalhos futuros
- [ ] Seção 16: termo de aceite assinado pelos parceiros
- [ ] Referências em ABNT
- [ ] Relatório de Curricularização da Extensão (único, com nome e RA de todos)
- [ ] Ficha individual de extensão de cada aluno, fechando 62h
- [ ] Formatação ABNT revisada; arquivo nomeado `Time X.docx`
- [ ] Vídeo do sistema em funcionamento, mostrando uma previsão e um alerta reais
- [ ] Slides com o vídeo embutido
- [ ] Banner conforme o modelo do CANVAS
- [ ] Ensaio cronometrado da apresentação

---

## Mapa: seção da especificação → onde ela nasce

| Seção | Sprint | Artefato de origem |
|---|---|---|
| 1–3 Introdução, Objetivos, Representantes | 1 | Entrevistas e termos dos parceiros |
| 4 Fundamentação | 2 | Séries temporais, detecção de anomalia, Eng. de Software |
| 5 Requisitos (incl. 5.3) | 2 | `ia/avaliacao.py` |
| 6 Benchmarking | 1 | Pesquisa de concorrentes |
| 7 Personas · 8 Protótipos | 4 | Figma + aceite dos parceiros |
| 9 Modelo de dados · 10 Arquitetura | 4 | Alembic + diagrama |
| 11.1–11.5 Solução de IA | 2–3 | Código de `ia/` |
| 11.7 Cibersegurança | 1 | Recorte **defesa**; controles em `seguranca/` |
| 12 Testes | 5 | `docs/evidencias/` |
| 13 Gestão | 5 | Quadro SCRUM mantido desde a Sprint 0 |
| 14–16 Resultados, Conclusão, Aceite | 6 | — |

---

## Verificação de ponta a ponta

1. `pytest -q -ra` verde, com os skips listados — nenhum teste pulado passando por verde
2. `bandit -r app/` e `pip-audit` sem achado alto; `gitleaks detect` limpo
3. Usuário da empresa A tentando abrir dado da empresa B recebe 403, com o teste provando
4. `uvicorn app.web:app` local → percorrer as 5 telas; console do navegador sem erro
5. Carregar uma empresa parceira e conferir que gasto e conversões do painel batem
   com o Gerenciador de Anúncios dela no mesmo período
6. `python -m app.ia.avaliacao` imprimindo modelo **e** régua lado a lado, com
   sMAPE, cobertura do intervalo e as métricas do detector
7. Injetar uma quebra conhecida na série sintética e confirmar que o alerta
   dispara, com a causa provável correta e o tempo até detecção registrado
8. Playwright a 375px e 1280px, sem rolagem horizontal e sem conteúdo que dependa de JS
9. Reiniciar o serviço no Render e confirmar que previsões, alertas e feedback sobreviveram

---

## Riscos declarados

| Risco | Efeito | Contramedida |
|---|---|---|
| Parceiro não autoriza acesso a tempo | Sem dado real, projeto trava | Termo na Sprint 1; caminho alternativo por CSV; dataset público sustenta o modelo enquanto isso |
| Poucas conversões por dia | CPA vira ruído e o alerta dispara à toa | Encolhimento bayesiano; alerta em métrica de topo quando falta volume; gravidade por verba em risco |
| Meta revisa dados recentes | Modelo treina em número que ainda vai mudar; alerta falso | Marcar provisório × fechado; treinar e alertar só no fechado |
| Campanha nova sem histórico | Previsão impossível na largada | Herança hierárquica da conta; declarar o mínimo de dias para prever |
| Render free | Serviço dorme e o disco é descartável | Tudo em Postgres; medir o tempo do primeiro acesso |
| LLM inventar métrica | Orientação errada com cara de certa | Número vem do banco para a tela; LLM só redige; teste de regressão |
| Dado de terceiro | Exposição indevida, problema de LGPD | Isolamento por empresa testado, cifra em repouso, auditoria, anonimização no relatório |

---

## Datas

Sprints de duas semanas a partir de 2026-09-22, fechando em meados de dezembro.
Confirmar com o calendário da professora Sílvia C. de Matos Soares antes de
congelar a Sprint 6.
