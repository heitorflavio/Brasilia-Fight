# Brasília Fight

Jogo de luta retrô em pygame, inspirado em Street Fighter / MUGEN: uma **sátira cômica** do
cenário político brasileiro. Bolsonaro, Lula e Xandão (Alexandre de Moraes) se enfrentam
em frente ao Congresso Nacional, usando **comidas** (e afins) como golpes especiais.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py          # janela
.venv/bin/python main.py --full   # tela cheia
```

Atalhos globais: **F11** tela cheia · **M** liga/desliga música · **ESC** pausa / volta.

## Modos

- **1 jogador**: você contra a CPU (dificuldade Fácil / Normal / Difícil no menu)
- **2 jogadores**: no mesmo teclado ou com dois controles
- **CPU x CPU**: modo demonstração

Partidas em melhor de 3 rounds, 99 segundos por round.

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

As teclas podem ser trocadas em `brfight/config.py`.

## Personagens e habilidades

| Personagem | Especial 1 | Especial 2 | Super |
|---|---|---|---|
| **Bolsonaro** — O Capitão | **Cloroquina**: cápsula reta na altura da cabeça (dá para agachar) | **Leite Condensado**: lata em arco que deixa poça grudenta (rival fica lento) | **Viagra**: modo *Imbrochável* — mais dano, mais velocidade, não recua e recupera vida |
| **Lula** — O Companheiro | **Picanha**: espeto voando na altura do peito | **Abóbora**: rola pelo chão e derruba (pule!) | **51**: a garrafa explode e deixa o rival **bêbado** (controles invertidos) |
| **Xandão** — O Supremo | **Constituição**: livro pesado que empurra o rival | **Inquérito**: corrente que puxa e atordoa o rival | **Censurado**: carimbo gigante cai do céu, causa dano e **cala** o rival (sem especiais por alguns segundos) |

O balanceamento foi ajustado com simulações CPU x CPU (cada personagem vence ~50%).

## Áudio real das falas

Toda fala tem uma voz sintetizada "estilo videogame" como padrão. Para usar o **áudio real**
de cada fala, coloque o arquivo (`.mp3`, `.ogg` ou `.wav`) com o nome certo na pasta do
personagem — o jogo usa o arquivo automaticamente:

```
assets/personagens/bolsonaro/cloroquina.mp3
assets/personagens/bolsonaro/leite_condensado.mp3
assets/personagens/bolsonaro/viagra.mp3
assets/personagens/lula/picanha.mp3
assets/personagens/lula/abobora.mp3
assets/personagens/lula/pinga51.mp3
assets/personagens/xandao/constituicao.mp3
assets/personagens/xandao/inquerito.mp3
assets/personagens/xandao/censurado.mp3
... e também nome, intro, vitoria1, vitoria2, vitoria3 para cada um
```

Para ver a lista completa (com o texto de cada fala) e o que ainda falta:

```bash
.venv/bin/python tools/checar_audios.py
```

Dica: corte os trechos curtos (1–3 s) e normalize o volume. Os textos das falas ficam em
`brfight/characters.py` — se trocar o áudio por outra frase, troque o texto do balão também.

Outros sons também podem ser substituídos: `assets/sons/<nome>.wav` (ex.: `ko`, `fight`,
`soco`, `chute`, `vitoria`) e a música: qualquer arquivo em `assets/musica/`.

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

## Estrutura

```
main.py                 ponto de entrada
brfight/config.py       resolução, física, controles
brfight/characters.py   personagens, habilidades, falas
brfight/fighter.py      lutador: estados, golpes, dano, poses
brfight/projectiles.py  comidas voadoras, poça, explosão, carimbo
brfight/controls.py     teclado, joystick e IA da CPU
brfight/art.py          pixel art procedural (cabeças, corpo, itens)
brfight/stage.py        cenários (foto -> pixel art) e torcida
brfight/audio.py        efeitos, vozes e música chiptune sintetizados
brfight/hud.py          barras de vida/super, cronômetro, combos
brfight/scenes.py       título, seleção, VS, luta, pausa, resultado
tools/                  pixelar.py e checar_audios.py
```

## Créditos

Veja `assets/CREDITOS.txt`. Este é um projeto de humor/paródia sem fins comerciais; as falas
são caricaturas e não representam declarações literais.
