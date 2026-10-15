"""Cenários: fotos reais de Brasília convertidas em pixel art na hora de carregar."""
import json
import math
import random

import pygame

from . import gfx
from .config import ASSETS, FLOOR_Y, GAME_H, GAME_W

IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


class Stage:
    def __init__(self, name, image, credit=""):
        self.name = name
        self.image = image
        self.credit = credit
        self.t = 0
        rng = random.Random(name)
        self.crowd = []
        for side, colors in ((0, [(250, 210, 30), (30, 150, 60), (40, 80, 170)]),
                             (1, [(210, 30, 40), (240, 240, 240), (180, 20, 30)])):
            for i in range(14):
                x = (8 + i * 9 + rng.randint(-2, 2)) if side == 0 else (GAME_W - 10 - i * 9 + rng.randint(-2, 2))
                self.crowd.append({
                    "x": x, "y": FLOOR_Y - 58 + rng.randint(-3, 3),
                    "c": rng.choice(colors), "skin": rng.choice([(235, 190, 160), (190, 140, 100), (140, 95, 65)]),
                    "ph": rng.random() * 6.28, "sign": rng.random() < 0.3, "side": side,
                })

    def update(self):
        self.t += 1

    def draw(self, surf, offset=(0, 0), excitement=0.0):
        ox, oy = offset
        surf.blit(self.image, (ox, oy))
        speed = 0.12 + excitement * 0.25
        for p in self.crowd:
            bob = abs(math.sin(self.t * speed + p["ph"])) * (1 + excitement * 2)
            x, y = p["x"] + ox, p["y"] - bob + oy
            pygame.draw.rect(surf, p["c"], (x - 3, y - 7, 7, 8))
            pygame.draw.rect(surf, p["skin"], (x - 2, y - 11, 5, 4))
            if p["sign"]:
                arm_y = y - 16 - bob
                pygame.draw.line(surf, (90, 70, 40), (x, y - 6), (x, arm_y), 1)
                sign_c = (250, 250, 240) if p["side"] == 0 else (250, 230, 60)
                pygame.draw.rect(surf, sign_c, (x - 5, arm_y - 6, 11, 6))
                pygame.draw.rect(surf, (20, 20, 20), (x - 5, arm_y - 6, 11, 6), 1)
        # sombra suave no chão para dar profundidade
        band = pygame.Surface((GAME_W, GAME_H - FLOOR_Y + 12), pygame.SRCALPHA)
        band.fill((0, 0, 0, 28))
        surf.blit(band, (ox, FLOOR_Y - 12 + oy))


def _fallback_image():
    img = pygame.Surface((GAME_W, GAME_H))
    for y in range(GAME_H):
        t = y / GAME_H
        c = (int(250 - 120 * t), int(150 - 60 * t), int(110 + 60 * t))
        pygame.draw.line(img, c, (0, y), (GAME_W, y))
    pygame.draw.rect(img, (70, 120, 50), (0, FLOOR_Y - 60, GAME_W, GAME_H))
    # silhueta do Congresso
    pygame.draw.rect(img, (215, 210, 200), (290, 140, 22, 130))
    pygame.draw.rect(img, (215, 210, 200), (318, 140, 22, 130))
    pygame.draw.rect(img, (225, 220, 210), (150, 255, 340, 12))
    pygame.draw.ellipse(img, (235, 230, 220), (390, 232, 90, 26))
    pygame.draw.circle(img, (235, 230, 220), (210, 256), 26, draw_top_left=True, draw_top_right=True)
    return img


def load_stages():
    folder = ASSETS / "bg"
    cfg = {}
    cfg_file = folder / "cenarios.json"
    if cfg_file.exists():
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cfg = {}
    stages = []
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() not in IMG_EXTS:
            continue
        c = cfg.get(path.name, {})
        try:
            raw = pygame.image.load(str(path)).convert()
        except pygame.error:
            continue
        raw = gfx.crop_to_aspect(raw, GAME_W / GAME_H, c.get("foco_y", 0.5), c.get("foco_x", 0.5))
        img = gfx.pixelate(raw, (GAME_W, GAME_H), pixel=c.get("pixel", 2), colors=c.get("cores", 32),
                           saturation=c.get("saturacao", 1.3))
        stages.append(Stage(c.get("nome", path.stem.replace("_", " ").title()), img, c.get("credito", "")))
    if not stages:
        stages.append(Stage("Esplanada", _fallback_image()))
    return stages
