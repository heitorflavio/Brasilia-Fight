"""Converte uma foto em pixel art (mesmo processo usado nos cenários do jogo).

Exemplos:
  python tools/pixelar.py foto_brasilia.jpg assets/bg/minha_foto.png
  python tools/pixelar.py rosto_recortado.png assets/personagens/lula/rosto.png --rosto

O modo --rosto gera 32x37 px (tamanho da cabeça dos lutadores). Use uma imagem PNG com
fundo transparente, só com o rosto, para ficar no estilo do vídeo de referência.
"""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from brfight import gfx  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--largura", type=int, default=640)
    ap.add_argument("--altura", type=int, default=360)
    ap.add_argument("--pixel", type=int, default=2, help="tamanho do 'pixel grande' (padrão 2)")
    ap.add_argument("--cores", type=int, default=32, help="cores na paleta (padrão 32)")
    ap.add_argument("--foco-y", type=float, default=0.5, help="0 = topo, 1 = base, ao recortar em 16:9")
    ap.add_argument("--rosto", action="store_true", help="gera cabeça 32x37 para assets/personagens/<id>/rosto.png")
    a = ap.parse_args()

    pygame.init()
    pygame.display.set_mode((1, 1))
    img = pygame.image.load(a.entrada)
    img = img.convert_alpha() if img.get_flags() & pygame.SRCALPHA else img.convert()
    if a.rosto:
        out = gfx.pixelate(img, (32, 37), pixel=1, colors=min(a.cores, 24), saturation=1.15)
    else:
        img = gfx.crop_to_aspect(img, a.largura / a.altura, a.foco_y)
        out = gfx.pixelate(img, (a.largura, a.altura), pixel=a.pixel, colors=a.cores)
    pygame.image.save(out, a.saida)
    print(f"ok -> {a.saida} ({out.get_width()}x{out.get_height()})")


if __name__ == "__main__":
    main()
