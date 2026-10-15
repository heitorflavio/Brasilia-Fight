"""Partículas, faíscas de impacto e textos flutuantes."""
import math
import random

import pygame

from . import gfx


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav", "kind", "text", "surf")

    def __init__(self, x, y, vx, vy, life, color, size=2, grav=0.0, kind="sq", text=None):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.grav, self.kind = color, size, grav, kind
        self.text = text
        self.surf = None


class FX:
    def __init__(self):
        self.parts = []
        self.rng = random.Random()

    def clear(self):
        self.parts.clear()

    def add(self, *a, **kw):
        p = Particle(*a, **kw)
        self.parts.append(p)
        return p

    def spark(self, x, y, color=(255, 240, 120), n=10, power=4.0):
        r = self.rng
        self.add(x, y, 0, 0, 8, (255, 255, 255), size=14, kind="star")
        for _ in range(n):
            a = r.uniform(0, math.tau)
            sp = r.uniform(power * 0.4, power)
            self.add(x, y, math.cos(a) * sp, math.sin(a) * sp, r.randint(8, 16), color, size=r.choice((2, 3)))

    def block(self, x, y):
        self.add(x, y, 0, 0, 7, (150, 210, 255), size=10, kind="ring")
        for _ in range(5):
            a = self.rng.uniform(0, math.tau)
            self.add(x, y, math.cos(a) * 2, math.sin(a) * 2, 8, (190, 230, 255), size=2)

    def burst(self, x, y, colors, n=14, power=4.0, grav=0.25, life=(15, 30), size=(2, 4)):
        r = self.rng
        for _ in range(n):
            a = r.uniform(-math.pi, 0) if grav > 0 else r.uniform(0, math.tau)
            sp = r.uniform(power * 0.3, power)
            self.add(x, y, math.cos(a) * sp, math.sin(a) * sp, r.randint(*life), r.choice(colors),
                     size=r.randint(*size), grav=grav)

    def dust(self, x, y, n=6):
        for _ in range(n):
            self.add(x + self.rng.uniform(-10, 10), y, self.rng.uniform(-1.5, 1.5), self.rng.uniform(-1.2, -0.2),
                     self.rng.randint(14, 24), (200, 190, 160), size=self.rng.randint(2, 4), grav=0.02)

    def text(self, x, y, txt, color=(255, 230, 60), size=20, life=50, vy=-0.8):
        surf = gfx.text_surface(txt, size, color, ow=2)
        half = surf.get_width() // 2 + 4
        x = max(half, min(640 - half, x))
        p = self.add(x, y, 0, vy, life, color, size=size, kind="text", text=txt)
        p.surf = surf
        return p

    def ring(self, x, y, color, size=30, life=14):
        self.add(x, y, 0, 0, life, color, size=size, kind="ring")

    def update(self):
        alive = []
        for p in self.parts:
            p.life -= 1
            if p.life <= 0:
                continue
            p.vy += p.grav
            p.x += p.vx
            p.y += p.vy
            if p.kind == "text":
                p.vy *= 0.94
            alive.append(p)
        self.parts = alive

    def draw(self, surf, off=(0, 0)):
        ox, oy = off
        for p in self.parts:
            k = p.life / p.max_life
            x, y = int(p.x + ox), int(p.y + oy)
            if p.kind == "sq":
                pygame.draw.rect(surf, p.color, (x, y, p.size, p.size))
            elif p.kind == "star":
                r = int(p.size * (1.2 - k * 0.6))
                pts = []
                for i in range(8):
                    a = i * math.pi / 4 + 0.3
                    rr = r if i % 2 == 0 else r * 0.4
                    pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
                pygame.draw.polygon(surf, (255, 255, 220), pts)
                pygame.draw.polygon(surf, (255, 200, 60), pts, 1)
            elif p.kind == "ring":
                r = int(p.size * (1 - k) + 3)
                pygame.draw.circle(surf, p.color, (x, y), r, 2)
            elif p.kind == "text":
                s = p.surf
                if k < 0.3:
                    s = s.copy()
                    s.set_alpha(int(255 * k / 0.3))
                surf.blit(s, s.get_rect(center=(x, y)))
