# Radar de Campanha

Previsão de custo por lead (CPA) e retorno (ROAS) das campanhas Meta Ads para os
próximos 7 a 14 dias, com alerta de anomalia antes que o orçamento queime.

Projeto Integrador VI — Engenharia de Software — PUC-Campinas, 2º semestre de 2026.
Disciplina 12563. Orientadora: Profa. Sílvia C. de Matos Soares.

## Integrantes

- Gabriel Lopes Londe Rodrigues
- Nicolas Marques Linares

## A ideia

Pequenas e médias empresas descobrem tarde que o custo por lead dobrou: o
Gerenciador de Anúncios mostra o que já aconteceu, e quando alguém olha, a verba
da semana já foi. O Radar de Campanha olha para frente. Ele prevê o CPA e o ROAS
de cada campanha para os próximos 7 e 14 dias, com uma faixa de incerteza, e
dispara um alerta quando o desempenho sai do previsto — dizendo qual peça da conta
se moveu (custo por mil impressões, taxa de clique ou taxa de conversão) e quanto
de verba está em risco.

O sistema não cria, não pausa e não altera campanhas. A decisão continua com a
pessoa que gerencia a conta.

## Extensão

62 horas por aluno junto a 2 a 5 empresas parceiras — clientes da BlueShieldPro,
com CNPJ — que participam das entrevistas de levantamento, da definição dos
requisitos, da validação do protótipo e do aceite final, e que autorizam por
escrito o uso dos dados das próprias campanhas.

## Como o trabalho entra

Cada item do checklist em [`docs/PLANO.md`](docs/PLANO.md) está aberto como issue e
entra no projeto por **pull request**. Todo PR roda os testes no GitHub Actions e
só vai para a `main` depois de aprovado e testado pelos integrantes.

## Rodar localmente

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.web:app --reload --port 8765
```

Abrir `http://localhost:8765`.

```bash
.venv/bin/pytest -ra
```

As telas usam **dados de demonstração** gerados em memória. Nenhum dado real de
empresa está no repositório.
