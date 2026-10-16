# Diário de Desenvolvimento — Brasília Fight

**Projeto:** Brasília Fight — Jogo de Luta 2D em Python e Pygame  
**Disciplina:** Computação Gráfica  
**Instituição:** AFYA Montes Claros  
**Curso:** Engenharia da Computação — 7º período  
**Integrante:** Thierry Amin  
**Equipe:** Thierry Amin e Heitor Flávio Ribeiro  
**Período documentado:** 11/10/2026 a 16/10/2026

## 1. Apresentação

Este diário registra as quatro etapas de desenvolvimento do jogo *Brasília Fight*: concepção, protótipo, versão intermediária e versão final.

O projeto consiste em um jogo de luta 2D desenvolvido em Python e Pygame, com três personagens inspirados em figuras da política brasileira, mecânicas de combate, golpes especiais, inteligência artificial e elementos visuais produzidos por programação.

O registro está organizado a partir da documentação técnica da equipe, das datas dos arquivos e do histórico de versões armazenado no GitHub.

Os marcos apresentados representam a evolução do projeto como um todo. As contribuições individuais devem ser identificadas conforme as atividades efetivamente realizadas por cada integrante.

---

## 2. Etapa 1 — Concepção do projeto

**Data de referência:** 11/10/2026

### Definição da proposta

A proposta do Brasília Fight foi desenvolver um jogo inspirado nos clássicos de luta dos anos 1990, especialmente *Street Fighter II* e *Mortal Kombat*, utilizando referências humorísticas da política brasileira.

O conceito tomou como referência um vídeo publicado pelo perfil @mortalkombatbrasileirox no TikTok.

As definições registradas para o projeto foram:

- **Tema:** sátira humorística da política brasileira.
- **Gênero:** jogo de luta 2D, um contra um.
- **Personagens:** Bolsonaro, Lula e Xandão.
- **Cenário:** Congresso Nacional, em Brasília.
- **Objetivo:** vencer dois rounds, reduzindo a vida do adversário ou mantendo mais vida ao final do tempo.
- **Modos:** jogador contra CPU, dois jogadores e CPU contra CPU.
- **Tecnologia:** Python e Pygame.
- **Identidade visual:** personagens desenhados por código, utilizando esqueletos articulados e animações procedurais.

### Aspectos técnicos definidos

Uma das principais decisões documentadas foi utilizar desenhos procedurais em lugar de sprites tradicionais. Essa abordagem permite representar movimentos por meio de cálculos geométricos e interpolação de ângulos.

Também foi estabelecida uma resolução interna de 640 × 360 pixels, com execução em 60 quadros por segundo.

### Evidências documentais

| Data | Registro |
|---|---|
| 11/10/2026 — 00h47 | Vídeo de referência salvo no projeto |
| 11/10/2026 — 00h49 | Criação do ambiente virtual Python |
| 11/10/2026 — 00h52 | Inclusão da imagem do Congresso Nacional |

Esses registros indicam a preparação inicial do projeto, embora não permitam identificar isoladamente o responsável por cada atividade.

---

## 3. Etapa 2 — Desenvolvimento do protótipo

**Data de referência:** 11/10/2026

### Estrutura técnica inicial

Na etapa de prototipação, foram organizados os componentes essenciais do jogo.

A documentação registra a elaboração dos seguintes módulos:

| Arquivo | Responsabilidade |
|---|---|
| `config.py` | Configurações de resolução, física e controles |
| `stage.py` | Construção do cenário |
| `controls.py` | Entrada de comandos por teclado e controle |
| `art.py` | Desenho procedural dos personagens |
| `fx.py` | Efeitos visuais e partículas |
| `hud.py` | Interface de vida, tempo e indicadores |
| `projectiles.py` | Projéteis e golpes especiais |
| `gfx.py` | Transformações e processamento gráfico |
| `main.py` | Ponto de entrada do programa |

### Conceitos de computação gráfica

Essa etapa reúne funcionalidades relacionadas aos conteúdos da disciplina, incluindo:

- Sistema de coordenadas bidimensionais.
- Representação e movimentação de personagens.
- Transformações geométricas.
- Construção de elementos gráficos por primitivas.
- Processamento de imagens para geração de pixel art.
- Composição de cena em camadas.
- Estruturas necessárias à detecção de colisões.

### Evidências

Os arquivos citados possuem registros de modificação entre 00h55 e 01h21 de 11/10/2026.

Entretanto, esses horários não comprovam, isoladamente, que todos os módulos já formavam um protótipo executável naquele momento.

A ausência de commits anteriores a 15/10/2026 limita a reconstrução precisa das primeiras versões.

---

## 4. Etapa 3 — Versão intermediária

**Data de referência:** 15/10/2026

### Consolidação da versão jogável

Em 15 de outubro, o projeto passou a apresentar uma versão completa registrada no GitHub.

Essa versão já reunia funcionalidades como:

- Menu principal e seleção de personagens.
- Tela de apresentação do confronto.
- Sistema de rounds e cronômetro.
- Barras de vida e de golpes especiais.
- Combate com personagens controlados pela CPU.
- Colisões entre ataques e lutadores.
- Pausa, encerramento e reinício da partida.

### Atualizações e correções

| Horário | Atualização | Registro |
|---|---|---|
| 11h48 | Primeira versão jogável no Git | `23d1ca4` |
| 11h56 | Configuração das releases automáticas | PR #1 |
| 15h43 | Inclusão de falas reais e locutor | PR #2 |
| 15h57 | Correção da seleção no modo CPU x CPU | PR #3 |
| 16h07 | Ajuste do áudio "Inconstitucional!" | PR #4 |
| 16h17 | Substituição de áudio com ruído | `c8dfb65` |

### Evolução observável

Uma das melhorias documentadas foi a alteração na seleção de personagens do modo CPU contra CPU.

Anteriormente, os personagens eram sorteados automaticamente. Na versão corrigida, tornou-se possível selecionar individualmente os dois lutadores.

Outro ajuste foi a prevenção de confirmações duplicadas, evitando que uma única entrada de teclado selecionasse os dois personagens.

As alterações de áudio também melhoraram a apresentação do jogo, por meio de recortes e redução de ruído em falas utilizadas nas partidas.

### Evidências

O histórico de commits e pull requests permite identificar essas alterações e comparar diferentes estados do código.

A documentação do projeto também apresenta capturas da tela de seleção antes e depois da correção.

---

## 5. Etapa 4 — Versão final

**Data de referência:** 16/10/2026

### Finalização e documentação

A etapa final documentada envolveu a organização dos materiais necessários à entrega acadêmica e a verificação de funcionalidades do jogo.

Entre os trabalhos registrados estão:

- Elaboração do relatório técnico de desenvolvimento.
- Documentação das regras e dos controles.
- Descrição da arquitetura do software.
- Registro das técnicas de computação gráfica.
- Organização das referências e créditos.
- Documentação do uso de inteligência artificial.
- Registro das dificuldades e soluções adotadas.

### Testes e verificação

O diário técnico do projeto informa a existência de 44 testes automatizados no arquivo `tests/test_jogo.py`.

Também registra:

- Verificação da instalação em ambiente limpo.
- Ferramenta de balanceamento em `tools/balanceamento.py`.
- Simulação de 90 partidas para avaliar o comportamento dos personagens.
- Organização do README com requisitos, instruções e problemas conhecidos.

Esses registros descrevem os procedimentos da equipe e não atribuem sua execução individual a um integrante específico.

### Resultado documentado

Ao final do período, o projeto é descrito como um jogo funcional, com três personagens, três modos de execução, controles configurados, sistemas de combate e recursos gráficos procedurais.

O relatório apresenta ainda