"""Simula partidas CPU x CPU sem janela e mostra a taxa de vitória de cada personagem.

Exemplos:
  python tools/balanceamento.py                  # 5 partidas por confronto, dificuldade Normal
  python tools/balanceamento.py -n 15 -d 2       # 15 por confronto, dificuldade Difícil

Cada confronto é jogado com os dois lados (Bolsonaro x Lula e Lula x Bolsonaro), então
com -n 5 são 30 partidas no total e 20 por personagem.
"""
import argparse
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brfight.characters import ORDER  # noqa: E402
from brfight.config import DIFFICULTIES  # noqa: E402
from brfight.game import Game  # noqa: E402
from brfight.scenes import FightScene  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-n", type=int, default=5, help="partidas por confronto (padrão: 5)")
    ap.add_argument("-d", type=int, default=1, choices=range(len(DIFFICULTIES)),
                    help="dificuldade da CPU: 0 fácil, 1 normal, 2 difícil (padrão: 1)")
    args = ap.parse_args()

    game = Game()
    game.difficulty = args.d
    wins, played = Counter(), Counter()
    draws, rounds, frames = 0, 0, 0
    pairs = [(a, b) for a in ORDER for b in ORDER if a != b]
    for i, (p1, p2) in enumerate(pairs):
        for _ in range(args.n):
            sc = FightScene(game, p1, p2, "cpu", game.stages[0])
            game.change(sc)
            while sc.phase != "end":
                game.step([])
                frames += 1
            played[p1] += 1
            played[p2] += 1
            rounds += sc.round
            if sc.match_winner is None:
                draws += 1
            else:
                wins[sc.match_winner.id] += 1
        print(f"  confronto {i + 1}/{len(pairs)} concluído", file=sys.stderr)

    total = len(pairs) * args.n
    print(f"\n{total} partidas CPU x CPU, dificuldade {DIFFICULTIES[args.d]}")
    for cid in ORDER:
        print(f"  {cid:10s} {wins[cid]:3d} de {played[cid]:3d}  ({100 * wins[cid] / played[cid]:.0f}%)")
    print(f"  empates: {draws}   rounds por partida: {rounds / total:.2f}   "
          f"duração média: {frames / total / 60:.0f} s de jogo")


if __name__ == "__main__":
    main()
