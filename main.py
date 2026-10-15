"""Brasília Fight — jogo de luta retrô, sátira da política brasileira.

Uso:  python main.py            (janela)
      python main.py --full     (tela cheia)
"""
import sys

from brfight.game import Game


def main():
    Game(fullscreen="--full" in sys.argv).run()


if __name__ == "__main__":
    main()
