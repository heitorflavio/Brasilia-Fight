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

Ou baixe a versão pronta para Windows, macOS ou Linux na página de **Releases** do GitHub.

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

O jogo já vem com **áudio real em todas as falas**:

- **Xandão:** trechos do vídeo de referência, com a voz separada da música;
- **Bolsonaro e Lula:** recortes de áudios conhecidos do [myinstants](https://www.myinstants.com), mais o
  "É só um minutozinho" e o grito de nocaute do Bolsonaro, que vêm do vídeo de referência;
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

## Créditos

Veja `assets/CREDITOS.txt`. Este é um projeto de humor/paródia sem fins comerciais; as falas
são caricaturas e não representam declarações literais.
