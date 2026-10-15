"""HUD estilo arcade: retratos, barras de vida/super, cronômetro, rounds e combos."""
import math

import pygame

from . import art, gfx
from .config import GAME_W, METER_MAX

BAR_W = 232
STATUS_LABELS = [("buff", "IMBROCHÁVEL", (110, 170, 255)), ("drunk", "BÊBADO", (255, 200, 60)),
                 ("silenced", "CENSURADO", (235, 50, 60)), ("slow", "GRUDADO", (250, 244, 220))]


class HUD:
    def __init__(self):
        self.t = 0
        self.portraits = {}

    def portrait(self, f):
        key = (f.style["head"], f.style.get("skin"))
        if key not in self.portraits:
            self.portraits[key] = art.head(f.style)
        return self.portraits[key]

    def draw(self, surf, fighters, timer_s, rounds_to_win):
        self.t += 1
        for i, f in enumerate(fighters):
            self._side(surf, f, i)
        # cronômetro
        box = pygame.Rect(GAME_W // 2 - 22, 10, 44, 30)
        pygame.draw.rect(surf, (20, 20, 40), box, border_radius=4)
        pygame.draw.rect(surf, (230, 200, 60), box, 2, border_radius=4)
        gfx.draw_text(surf, f"{max(0, timer_s):02d}", 26, box.center, (255, 240, 120), "center", ow=2)
        # vitórias de round
        for i, f in enumerate(fighters):
            for r in range(rounds_to_win):
                cx = GAME_W // 2 + (-34 - r * 12 if i == 0 else 34 + r * 12)
                won = r < f.round_wins
                pygame.draw.circle(surf, (20, 20, 30), (cx, 48), 5)
                pygame.draw.circle(surf, (255, 210, 50) if won else (80, 80, 90), (cx, 48), 4)

    def _side(self, surf, f, i):
        left = i == 0
        pr = self.portrait(f)
        if not left:
            pr = pygame.transform.flip(pr, True, False)
        px = 6 if left else GAME_W - 6 - 36
        frame = pygame.Rect(px, 6, 36, 40)
        pygame.draw.rect(surf, (25, 25, 45), frame)
        surf.blit(pr, (px + 2, 7))
        pygame.draw.rect(surf, (230, 200, 60), frame, 2)

        bx = 46 if left else GAME_W - 46 - BAR_W
        by = 20
        gfx.draw_text(surf, f.data["name"], 13, (bx if left else bx + BAR_W, by - 1), (255, 255, 255),
                      "bottomleft" if left else "bottomright")
        pygame.draw.rect(surf, (20, 10, 20), (bx - 2, by - 2, BAR_W + 4, 16))
        pygame.draw.rect(surf, (120, 20, 30), (bx, by, BAR_W, 12))
        tw = int(BAR_W * f.hp_trail / 100)
        hw = int(BAR_W * f.hp / 100)
        low = f.hp < 25 and (self.t // 8) % 2
        main = (255, 120, 40) if low else (255, 222, 40)
        if left:
            pygame.draw.rect(surf, (250, 70, 50), (bx + BAR_W - tw, by, tw, 12))
            pygame.draw.rect(surf, main, (bx + BAR_W - hw, by, hw, 12))
            pygame.draw.rect(surf, (255, 250, 180), (bx + BAR_W - hw, by + 1, hw, 2))
        else:
            pygame.draw.rect(surf, (250, 70, 50), (bx, by, tw, 12))
            pygame.draw.rect(surf, main, (bx, by, hw, 12))
            pygame.draw.rect(surf, (255, 250, 180), (bx, by + 1, hw, 2))

        # barra de super (roxa)
        mw = 150
        mx = bx + BAR_W - mw if left else bx
        my = by + 16
        full = f.meter >= METER_MAX
        pygame.draw.rect(surf, (20, 10, 30), (mx - 2, my - 2, mw + 4, 9))
        pygame.draw.rect(surf, (50, 30, 70), (mx, my, mw, 5))
        w = int(mw * min(1.0, f.meter / METER_MAX))
        col = (200, 120, 255) if not full else ((255, 255, 255) if (self.t // 5) % 2 else (180, 90, 255))
        if left:
            pygame.draw.rect(surf, col, (mx + mw - w, my, w, 5))
        else:
            pygame.draw.rect(surf, col, (mx, my, w, 5))
        if full:
            sp = f.data["specials"]["s3"]["nome"].upper()
            gfx.draw_text(surf, f"SUPER: {sp}!", 13, (mx - 6 if left else mx + mw + 6, my - 3),
                          (230, 190, 255), "topright" if left else "topleft")

        # status
        tags = [(lab, c) for key, lab, c in STATUS_LABELS if f.status[key] > 0]
        x = bx + BAR_W if left else bx
        for lab, c in tags:
            r = gfx.draw_text(surf, lab, 13, (x, my + 9), c, "topright" if left else "topleft")
            x = r.left - 6 if left else r.right + 6

    def combo(self, surf, f, i):
        if f.combo >= 2 and f.combo_timer > 0:
            s = gfx.gradient_text(f"{f.combo} COMBO", 30, (255, 255, 200), (255, 150, 30), ow=2)
            bounce = int(math.sin(f.combo_timer * 0.4) * 2) if f.combo_timer > 55 else 0
            if i == 0:
                surf.blit(s, (10, 92 + bounce))
            else:
                surf.blit(s, (GAME_W - 10 - s.get_width(), 92 + bounce))
