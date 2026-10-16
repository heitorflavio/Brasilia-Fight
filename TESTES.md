# Registro de testes — Brasília Fight

Este arquivo registra como o jogo é testado, o resultado de cada execução e os problemas
encontrados. Os testes automatizados ficam em [`tests/test_jogo.py`](tests/test_jogo.py).

## Como rodar

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Não precisa instalar nada além do `requirements.txt`: os testes usam o `unittest`, que já vem
com o Python. Eles abrem o jogo sem janela e sem som (drivers `dummy` do SDL), enviam eventos de
teclado e conferem o estado do jogo. A execução completa leva cerca de 25 segundos, porque
inclui três partidas inteiras CPU x CPU.

## O que é testado (44 testes)

| Área | Testes | O que verificam |
|---|---|---|
| Encerramento e menu | 4 | Fechar a janela encerra o laço; a opção SAIR encerra; o menu navega e abre a seleção; a dificuldade muda com as setas |
| Controles | 4 | J gera soco; cada comando é usado uma vez só; Enter repetido não confirma o lutador ao abrir a seleção; no CPU x CPU o jogador escolhe os dois lutadores |
| Colisões | 11 | Soco no alcance acerta e fora do alcance erra; o golpe acerta uma vez só; a caixa de ataque espelha com a direção; defesa segurando para trás; rasteira passa pela defesa em pé; cloroquina passa por cima de quem agacha; projéteis opostos se anulam; lutadores não se atravessam, nem presos na parede; lutador caído não é atingido |
| Limites | 3 | Andar e pular contra a parede esquerda e direita por 400 quadros sem sair da arena; o pulo sobe e volta ao chão |
| Regras | 8 | Tempo esgotado: vence quem tem mais vida, ou empata; vida zerada é nocaute; melhor de 3; combo reduz o dano em 12%; super exige barra cheia; censurado não usa especiais; bêbado inverte os controles |
| Pausa e reinício | 6 | ESC pausa e congela cronômetro e vida; ESC retoma; menu principal pela pausa; na tela final ENTER = revanche, S = trocar personagens, ESC = menu |
| Partidas completas | 4 | Três partidas CPU x CPU (uma em cada dificuldade) terminam; o vencedor tem 2 rounds; ninguém sai da arena; o tempo por quadro fica abaixo de 16,7 ms (60 FPS) |
| Recursos | 4 | Cenário e fonte existem; os três personagens têm dados completos; o código não tem caminhos absolutos; a redução de cores respeita a paleta |

## Execuções

### 16/10/2026 — macOS (Apple Silicon), Python 3.9.6, pygame 2.6.1, numpy 2.0.2

```
Ran 44 tests in 24.485s

OK
```

- **Resultado:** 44 de 44 testes passaram.
- **Desempenho:** 17.792 quadros processados; média de 0,89 ms por quadro, p99 de 1,50 ms e
  máximo de 5,5 ms. O limite a 60 FPS é 16,7 ms.

### 16/10/2026 — instalação limpa

Cópia só com os arquivos do repositório, ambiente virtual novo e
`pip install -r requirements.txt`, seguido da mesma bateria de testes.

- **Instalado:** pygame 2.6.1 e numpy 2.0.2 (Python 3.9.6), sem erros.
- **Resultado:** `Ran 44 tests in 25.171s — OK`. O `requirements.txt` basta para rodar o jogo
  e os testes.

### Os testes detectam erros?

Para conferir que os testes não passam "sempre", o código foi quebrado de propósito, só na
memória, em três pontos. Em todos os casos os testes correspondentes falharam:

| Falha introduzida | Testes que falharam |
|---|---|
| Remover o limite da arena | `test_parede_esquerda`, `test_parede_direita` |
| Remover a proteção contra Enter repetido na seleção | `test_selecao_ignora_enter_repetido` |
| Fazer o golpe acertar sem checar a sobreposição das caixas | `test_soco_fora_do_alcance_erra` |

## Balanceamento

Simulação de partidas CPU x CPU na dificuldade Normal, com todos os confrontos e os dois lados:

```bash
.venv/bin/python tools/balanceamento.py -n 5    # 30 partidas
```

Em 16/10/2026 foram rodados três lotes de 30 partidas (90 no total):

| Personagem | Lote 1 | Lote 2 | Lote 3 | Total |
|---|---|---|---|---|
| Bolsonaro | 16 de 20 | 8 de 20 | 10 de 20 | 34 de 60 (57%) |
| Lula | 9 de 20 | 13 de 20 | 10 de 20 | 32 de 60 (53%) |
| Xandão | 5 de 20 | 9 de 20 | 10 de 20 | 24 de 60 (40%) |

Não houve empates; as partidas tiveram em média 2,5 rounds e 105 segundos de jogo. A variação
entre lotes é grande, então 60 partidas por personagem não bastam para afirmar desequilíbrio.
Mesmo assim, o Xandão ficou abaixo dos outros no total e é o candidato a um ajuste.

## Teste dos executáveis (GitHub Actions)

A cada PR mergeado na `main`, o workflow [`release.yml`](.github/workflows/release.yml)
instala as dependências em uma máquina limpa, compila o jogo para Windows, macOS e Linux e abre
cada executável sem janela por 8 segundos. Se ele fechar sozinho, a release não é publicada.

## Testes manuais

O que os testes automáticos não cobrem precisa ser conferido jogando, de preferência no
computador da apresentação:

- [ ] O jogo abre com `python main.py` e com o executável da release
- [ ] Teclado do jogador 1 e do jogador 2 respondem sem atraso perceptível
- [ ] Controle (Xbox ou similar) move e golpeia na luta
- [ ] Falas, locutor e música tocam; a música abaixa durante as falas
- [ ] F11 alterna a tela cheia; M liga e desliga a música
- [ ] Textos legíveis no projetor (HUD, pausa, tela final)
- [ ] Partida completa no modo 1 jogador, com vitória e com derrota
- [ ] Revanche, troca de personagens e volta ao menu pela tela final
- [ ] Fechar pelo X da janela durante a luta

## Problemas encontrados

| Data | Problema | Como foi encontrado | Solução | Situação |
|---|---|---|---|---|
| 15/10/2026 | No CPU x CPU, os lutadores eram sorteados e travados ao abrir a tela | Uso do jogo | Seleção manual da CPU 1 e da CPU 2 (PR #3) | Corrigido; coberto por `test_selecao_cpu_x_cpu_escolhe_os_dois` |
| 15/10/2026 | Um Enter repetido confirmava os dois lutadores de uma vez | Uso do jogo | Entradas ignoradas por 0,25 s ao abrir a tela e após a 1ª escolha (PR #3) | Corrigido; coberto por `test_selecao_ignora_enter_repetido` |
| 15/10/2026 | "Inconstitucional!" tinha restos de outras falas | Ouvindo o áudio | Recorte de 2,38 s para 0,71 s (PR #4) | Corrigido |
| 15/10/2026 | Introdução do Bolsonaro com música e ruído de fundo | Ouvindo o áudio | Troca por um áudio limpo (`c8dfb65`) | Corrigido |
| 16/10/2026 | O README dizia que cada personagem vence ~50% | Simulação de 90 partidas | README corrigido com os números medidos | Corrigido |
| 16/10/2026 | O Xandão vence menos (40% em 90 partidas) | Simulação de 90 partidas | Ajustar recarga ou dano dos especiais | Aberto |
| 16/10/2026 | Na pausa, balões de fala aparecem por baixo da camada escura e cobrem as instruções | Capturas de tela da apresentação | Esconder os balões durante a pausa | Aberto |
| 16/10/2026 | Com controle, não dá para pausar nem escolher revanche ou menu na tela final | Revisão do código | Mapear o botão Start e os botões A/B nessas telas | Aberto |
