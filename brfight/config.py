"""Constantes globais e mapeamento de controles."""
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

TITLE = "Brasília Fight"

# Resolução interna (pixel art). A janela é escalada com pygame.SCALED.
GAME_W, GAME_H = 640, 360
FPS = 60

FLOOR_Y = 326          # y dos pés dos lutadores
STAGE_LEFT = 24        # limites da arena
STAGE_RIGHT = GAME_W - 24
GRAVITY = 0.62

ROUND_TIME = 99        # segundos
ROUNDS_TO_WIN = 2      # melhor de 3
METER_MAX = 100

# Controles de teclado. Cada ação aceita várias teclas.
KEYMAP_P1 = {
    "up": [pygame.K_w],
    "down": [pygame.K_s],
    "left": [pygame.K_a],
    "right": [pygame.K_d],
    "punch": [pygame.K_j],
    "kick": [pygame.K_k],
    "s1": [pygame.K_l],
    "s2": [pygame.K_u],
    "s3": [pygame.K_i],
}

KEYMAP_P2 = {
    "up": [pygame.K_UP],
    "down": [pygame.K_DOWN],
    "left": [pygame.K_LEFT],
    "right": [pygame.K_RIGHT],
    "punch": [pygame.K_KP1, pygame.K_COMMA],
    "kick": [pygame.K_KP2, pygame.K_PERIOD],
    "s1": [pygame.K_KP3, pygame.K_SLASH],
    "s2": [pygame.K_KP4, pygame.K_SEMICOLON],
    "s3": [pygame.K_KP5, pygame.K_QUOTE],
}

# Botões de joystick (layout Xbox/SDL): A, B, X, Y, LB, RB
PAD_BUTTONS = {
    "punch": [2],   # X
    "kick": [0],    # A
    "s1": [3],      # Y
    "s2": [1],      # B
    "s3": [4, 5],   # LB / RB
}

DIFFICULTIES = ["FÁCIL", "NORMAL", "DIFÍCIL"]
