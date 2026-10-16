# Brasília Fight

Jogo de luta retrô em pygame, inspirado em Street Fighter / MUGEN: uma **sátira cômica** do
cenário político brasileiro. Bolsonaro, Lula e Xandão (Alexandre de Moraes) se enfrentam
em frente ao Congresso Nacional, usando **comidas** (e afins) como golpes especiais.

Projeto avaliativo da disciplina de Computação Gráfica (AFYA Montes Claros), desenvolvido
por Heitor Flávio Ribeiro e Thierry Amin.

## Requisitos

- **Python 3.9 ou mais recente** (testado com 3.9.6 no macOS e 3.12 no GitHub Actions)
- Dependências em `requirements.txt`: `pygame>=2.5` e `numpy>=1.21`
- Windows, macOS ou Linux; teclado (controle Xbox opcional)

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py          # janela
.venv/bin/python main.py --full   # tela cheia
```

No Windows, troque `.venv/bin/` por `.venv\Scripts\` (por exemplo, `.venv\Scripts\python main.py`).

Atalhos globais: **F11** tela cheia · **M** liga/desliga música · **ESC** pausa / volta.

Ou baixe a versão pronta para Windows, macOS ou Linux na página de **Releases** do GitHub.

## Objetivo e regras

- **Objetivo:** zerar a barra de vida do adversário (nocaute) ou terminar o round com mais vida.
- Cada round dura **99 segundos**. Se o tempo acabar, vence quem tiver mais vida; vida igual é empate.
- A partida é **melhor de 3**: vence quem ganhar 2 rounds. Duplo nocaute ou empate dá o round aos dois.
- **Defesa:** segure para trás. Agachado defende golpes baixos; em pé defende golpes no pulo.
- **Combo:** cada golpe seguido causa 12% menos dano, até o mínimo de 45%.
- **Super:** a barra roxa enche batendo e apanhando; cheia, libera o golpe mais forte.
- **Efeitos:** grudado (lento), bêbado (controles invertidos), censurado (sem especiais) e
  imbrochável (mais dano e velocidade). Os efeitos ativos aparecem no HUD.
- Cada especial tem tempo de recarga, e só pode haver um projétil comum de cada lutador na tela.

## Modos

- **1 jogador**: você contra a CPU (dificuldade Fácil / Normal / Difícil no menu)
- **2 jogadores**: no mesmo teclado ou com dois controles
- **CPU x CPU**: modo demonstração — você escolhe os dois lutadores (R = aleatório) e assiste

Ao fim da partida: **ENTER** revanche · **S** trocar personagens · **ESC** menu.

## Controles

| Ação            | Jogador 1 | Jogador 2               | Controle (Xbox) |
|-----------------|-----------|-------------------------|-----------------|
| Mover / pular / agachar | W A S D | Setas            | Analógico / D-pad |
| Soco            | J         | `,` ou Num 1            | X               |
| Chute           | K         | `.` ou Num 2            | A               |
| Especial 1      | L         | `/` ou Num 3            | Y               |
| Especial 2      | U         | `;` ou Num 4            | B               |
| Super           | I         | `'` ou Num 5            | LB / RB         |

- **Defender**: segure para *trás*. Agachado defende golpes baixos (rasteira, abóbora); em pé
  defende golpes no pulo.
- Agachado + chute = **rasteira** (derruba).
- Acertou um soco? Aperte um especial logo em seguida para emendar o **combo**.
- A **barra roxa** enche batendo e apanhando; cheia, libera o **SUPER**.
- Os controles também aparecem na tela de pausa (**ESC** ou **P** durante a luta).

As teclas podem ser trocadas em `brfight/config.py`.

## Personagens e habilidades

| Personagem | Especial 1 | Especial 2 | Super |
|---|---|---|---|
| **Bolsonaro** — O Capitão | **Cloroquina**: cápsula reta na altura da cabeça (dá para agachar) | **Leite Condensado**: lata em arco que deixa poça grudenta (rival fica lento) | **Viagra**: modo *Imbrochável* — mais dano, mais velocidade, não recua e recupera vida |
| **Lula** — O Companheiro | **Picanha**: espeto voando na altura do peito | **Abóbora**: rola pelo chão e derruba (pule!) | **51**: a garrafa explode e deixa o rival **bêbado** (controles invertidos) |
| **Xandão** — O Supremo | **Constituição**: livro pesado que empurra o rival | **Inquérito**: corrente que puxa e atordoa o rival | **Censurado**: carimbo gigante cai do céu, causa dano e **cala** o rival (sem especiais por alguns segundos) |

O balanceamento é medido com simulações CPU x CPU (`tools/balanceamento.py`). Em 90 partidas
na dificuldade Normal, os resultados foram Bolsonaro 57%, Lula 53% e Xandão 40%
(detalhes em [TESTES.md](TESTES.md)).

## Como funciona

### Colisões

A colisão usa **retângulos alinhados aos eixos** (AABB, com `pygame.Rect.colliderect`):

- Cada lutador tem uma **caixa de corpo**: 30×108 px em pé, 30×70 agachado e 30×88 no ar. Caído,
  não tem caixa e não pode ser atingido.
- Durante os quadros ativos de um golpe, existe uma **caixa de ataque** à frente do lutador,
  espelhada conforme o lado para onde ele olha.
- Se as duas caixas se sobrepõem, o golpe acerta **uma única vez**; as faíscas nascem no centro
  da interseção (`Rect.clip`).
- Projéteis usam o retângulo da própria imagem. A cloroquina passa a 84 px do chão, acima da
  caixa de quem está agachado (70 px), por isso agachar desvia dela.
- Projéteis de lados opostos que se tocam se anulam.
- Os corpos se empurram quando estão a menos de 34 px, e a posição é limitada à arena (24 a 616 px).

O código está em `brfight/fighter.py` (`attack_box`, `hurtbox`, `take_hit`) e
`brfight/scenes.py` (`_melee`, `_push_apart`, `_projectile_clash`).

### Técnicas de computação gráfica

- **Personagens com esqueleto articulado** (`art.py`): cada pose é um conjunto de ângulos; a
  posição das articulações é calculada por cinemática direta e o corpo é desenhado com primitivas.
- **Animação por interpolação de poses** (`fighter.py`): os ângulos são misturados entre a pose de
  preparação e a de impacto conforme os quadros do golpe; a caminhada usa um ciclo senoidal.
- **Transformações**: espelhamento ao virar, rotação na queda e nos projéteis (em passos de 45°
  para não borrar), escala nos retratos e no letreiro "VS".
- **Foto em pixel art** (`gfx.py`): recorte, redução, aumento de saturação e paleta de 32 cores
  com k-means (NumPy).
- **Partículas** (`fx.py`): faíscas, poeira, explosões e textos flutuantes com velocidade,
  gravidade e transparência.
- **Camadas e transparência**: cenário → zonas → lutadores → projéteis e partículas → balões →
  HUD → sobreposições escuras; lampejo e aura feitos com a silhueta do sprite.
- **Efeitos de impacto**: tremor de tela, pausa no impacto (*hitstop*), câmera lenta no nocaute
  e congelamento no super.

A explicação completa, com fórmulas e trechos de código, está na apresentação em PDF do projeto.

## Áudio real das falas

O jogo já vem com **áudio real em todas as falas**:

- **Xandão:** trechos do vídeo de referência, com a voz separada da música;
- **Bolsonaro e Lula:** recortes de áudios conhecidos do [myinstants](https://www.myinstants.com), mais o
  grito de nocaute do Bolsonaro, que vem do vídeo de referência;
- **Locutor:** "Round one / Round two / Final round / Fight!" no estilo Mortal Kombat (myinstants);
- **Nomes na tela de seleção:** locutor genérico gerado com uma voz do macOS (não imita ninguém).

Os balões mostram o que se ouve em cada áudio. Enquanto alguém fala, a música abaixa sozinha,
e o jogo espera a fala terminar antes de seguir (introdução, "Fight!", vitória).

Para trocar uma fala, coloque o arquivo (`.wav`, `.ogg` ou `.mp3`) em
`assets/personagens/<personagem>/<fala>` e ajuste o texto do balão em `brfight/characters.py`.
Para ver os nomes de todas as falas e o que já tem áudio:

```bash
.venv/bin/python tools/checar_audios.py
```

Cada personagem também pode ter um `ko.wav`, grito ao ser nocauteado. Os sons do locutor ficam em
`assets/sons/` (`round1`, `round2`, `round3`, `fight`) e a música em `assets/musica/`.

## Rostos reais (opcional)

Os personagens são caricaturas em pixel art desenhadas pelo código. Para usar uma foto do
rosto (como no vídeo de referência), recorte só a cabeça com fundo transparente e converta:

```bash
.venv/bin/python tools/pixelar.py rosto_recortado.png assets/personagens/lula/rosto.png --rosto
```

## Cenários

Toda imagem em `assets/bg/` vira um cenário, convertida para pixel art na hora (redução de
resolução + paleta de 32 cores). Ajustes por imagem (nome, recorte, cores, crédito) ficam em
`assets/bg/cenarios.json`. O cenário incluído é uma foto real do Congresso Nacional ao
pôr do sol. Para pré-visualizar a conversão de outra foto:

```bash
.venv/bin/python tools/pixelar.py minha_foto.jpg previa.png
```

## Testes

```bash
.venv/bin/python -m unittest discover -s tests -v
```

São 44 testes automatizados (controles, colisões, limites da arena, regras, pausa, reinício,
encerramento, recursos e desempenho), que rodam o jogo sem janela em cerca de 25 segundos e
não precisam de dependências extras. O registro das execuções, os testes manuais e os
problemas encontrados estão em [TESTES.md](TESTES.md).

Para simular partidas CPU x CPU e medir o balanceamento:

```bash
.venv/bin/python tools/balanceamento.py -n 5      # 30 partidas, dificuldade Normal
```

## Estrutura

```
main.py                    ponto de entrada (--full = tela cheia)
requirements.txt           dependências (pygame, numpy)
brfight/
  game.py                  laço principal: eventos, atualização, desenho, 60 FPS
  scenes.py                telas: título, seleção, VS, luta, pausa, resultado
  fighter.py               lutador: estados, física, golpes, colisão, dano, poses
  projectiles.py           comidas voadoras, poça, explosão, carimbo
  controls.py              teclado, joystick e IA da CPU
  art.py                   pixel art procedural (esqueleto, cabeças, corpo, itens)
  gfx.py                   textos, contornos e conversão de foto em pixel art
  fx.py                    partículas e textos flutuantes
  stage.py                 cenários (foto -> pixel art) e torcida
  hud.py                   barras de vida/super, cronômetro, rounds, combos
  audio.py                 efeitos, vozes e música chiptune sintetizados
  characters.py            personagens, habilidades, falas
  config.py                resolução, física, limites da arena, controles
assets/
  bg/                      cenários + cenarios.json
  fontes/                  fonte VT323 + licença
  personagens/<nome>/      falas reais
  sons/                    locutor (round1, round2, round3, fight)
  musica/                  música opcional
tests/test_jogo.py         testes automatizados (unittest)
tools/                     pixelar.py, checar_audios.py, balanceamento.py
.github/workflows/         release automática
CREDITOS.txt               créditos e licenças dos recursos externos
DIARIO.md                  diário de desenvolvimento (quatro etapas)
TESTES.md                  registro de testes
```

## Problemas conhecidos

- Com controle, não é possível pausar nem escolher revanche ou menu na tela final; essas ações
  exigem o teclado.
- Na pausa, balões de fala que estavam na tela aparecem por baixo da camada escura e podem
  cobrir parte das instruções.
- O Xandão vence menos que os outros nas simulações (40% em 90 partidas).
- Há um único cenário incluído (outros podem ser adicionados em `assets/bg/`).
- A dificuldade da CPU é escolhida no menu e não muda durante a partida.
- O app de macOS da release não é assinado (veja abaixo como liberar).
- Os áudios reais das falas não têm licença explícita (veja Créditos).

## Releases

Todo PR mergeado na `main` gera uma release automaticamente
(`.github/workflows/release.yml`): o jogo é compilado com PyInstaller para Windows, macOS e
Linux, testado e publicado em **Releases** com as notas geradas a partir dos PRs.

A versão segue `vMAJOR.MINOR.PATCH` e, por padrão, sobe o PATCH. Para mudar, coloque um
label no PR antes do merge:

| Label           | Efeito                |
|-----------------|-----------------------|
| (nenhum)        | v1.2.3 → v1.2.4       |
| `release:minor` | v1.2.3 → v1.3.0       |
| `release:major` | v1.2.3 → v2.0.0       |
| `release:skip`  | não gera release      |

A primeira release é a `v0.1.0`. O app de macOS não é assinado e roda em Apple Silicon
(M1 ou mais novo): na primeira vez, libere em Ajustes do Sistema → Privacidade e
Segurança → "Abrir Mesmo Assim".

## Documentação

- Apresentação em PDF (entregue separadamente): construção do jogo, arquitetura, técnicas
  gráficas, colisões, testes, evolução, créditos e uso de IA.
- [DIARIO.md](DIARIO.md): diário de desenvolvimento com as quatro etapas.
- [TESTES.md](TESTES.md): registro de testes e problemas encontrados.

## Créditos

Veja [CREDITOS.txt](CREDITOS.txt). Este é um projeto de humor/paródia sem fins comerciais; as falas
são caricaturas e não representam declarações literais.

Uso de IA: o Claude Code (Anthropic) foi usado como apoio no desenvolvimento, na depuração,
nos testes e na documentação. A declaração completa (finalidade, trechos afetados e validação)
está na seção 11.3 da apresentação.
