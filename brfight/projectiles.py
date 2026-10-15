"""Projéteis (as comidas!) e zonas/efeitos de cenário criados pelos especiais."""
import math

import pygame

from . import art, audio
from .config import FLOOR_Y, GAME_W

HIT_DEFAULTS = dict(dmg=5, hitstun=16, blockstun=10, push=3.5, height="mid", knockdown=False, launch=-6.0,
                    chip=0.0, sfx="soco", spark=(255, 240, 120), effects=None, super=False, heavy=False,
                    stun_state=None, projectile=False)


def hit_info(**kw):
    d = dict(HIT_DEFAULTS)
    d.update(kw)
    return d


class Projectile:
    clash = True

    def __init__(self, owner, sp, x, y, vx, vy=0.0):
        self.owner, self.sp = owner, sp
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.alive = True
        self.t = 0
        self.angle = 0
        self.img = art.item(sp["item"])
        self.spin = 0

    def rect(self):
        w, h = self.img.get_size()
        return pygame.Rect(int(self.x - w / 2), int(self.y - h / 2), w, h)

    def info(self):
        return hit_info(dmg=self.sp["dmg"], hitstun=20, blockstun=14, push=self.sp.get("push", 4.5), chip=0.15,
                        sfx="pesado", projectile=True)

    def update(self, scene):
        self.t += 1
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin
        if self.x < -60 or self.x > GAME_W + 60:
            self.alive = False

    def check_hit(self, scene, target):
        if not self.alive:
            return
        hb = target.hurtbox()
        if hb and hb.colliderect(self.rect()):
            res = target.take_hit(self.info(), self.owner, scene, from_x=self.x)
            if res:
                self.on_hit(target, res, scene)

    def on_hit(self, target, result, scene):
        self.alive = False

    def destroy(self, scene):
        self.alive = False
        scene.fx.burst(self.x, self.y, [(255, 255, 255), (255, 220, 120)], n=10, grav=0.15)

    def draw(self, surf, off):
        img = self.img
        if self.spin:
            a = int(self.angle // 45) * 45  # rotação em passos para manter o pixel art
            img = pygame.transform.rotate(img, a)
        if self.vx < 0 and not self.spin:
            img = pygame.transform.flip(img, True, False)
        surf.blit(img, img.get_rect(center=(int(self.x + off[0]), int(self.y + off[1]))))


class Straight(Projectile):
    def __init__(self, owner, sp, x, y, vx):
        super().__init__(owner, sp, x, y, vx)
        self.spin = {"cloroquina": 15, "constituicao": 9}.get(sp["item"], 0) * (1 if vx > 0 else -1)

    def update(self, scene):
        super().update(scene)
        if self.sp["item"] == "picanha" and self.t % 3 == 0:
            scene.fx.add(self.x - self.vx * 2, self.y - 4, 0, -0.6, 14, (200, 200, 200), size=2)
        if self.sp["item"] == "cloroquina" and self.t % 4 == 0:
            scene.fx.add(self.x, self.y, -self.vx * 0.1, 0, 10, (255, 160, 160), size=2)

    def on_hit(self, target, result, scene):
        self.alive = False
        item = self.sp["item"]
        if item == "picanha":
            scene.fx.burst(self.x, self.y, [(150, 40, 35), (245, 228, 190), (200, 60, 50)], n=12)
            audio.sfx("chiado")
        elif item == "constituicao":
            scene.fx.burst(self.x, self.y, [(250, 250, 240), (230, 230, 220)], n=14, grav=0.08)
            scene.shake = max(scene.shake, 6)
        else:
            scene.fx.burst(self.x, self.y, [(215, 40, 45), (255, 255, 255)], n=10)


class Lob(Projectile):
    """Lata de leite condensado: vai em arco e deixa poça grudenta."""

    def __init__(self, owner, sp, x, y, vx):
        super().__init__(owner, sp, x, y, vx, -7.2)
        self.spin = 20 if vx > 0 else -20

    def info(self):
        return hit_info(dmg=self.sp["dmg"], hitstun=18, blockstun=12, push=3, chip=0.1, sfx="soco",
                        projectile=True, effects={"slow": 200})

    def update(self, scene):
        self.vy += 0.32
        super().update(scene)
        if self.y >= FLOOR_Y - 6:
            self.alive = False
            scene.zones.append(Puddle(self.owner, self.x))
            self._splash(scene)

    def _splash(self, scene):
        scene.fx.burst(self.x, min(self.y, FLOOR_Y - 4), [(255, 250, 230), (240, 230, 200)], n=16, power=3.5)
        audio.sfx("soco", 0.5)

    def on_hit(self, target, result, scene):
        self.alive = False
        self._splash(scene)
        if result == "hit":
            scene.fx.text(target.x, target.y - 120, "GRUDOU!", (255, 250, 220), 18)


class Roll(Projectile):
    """Abóbora rolando no chão — golpe baixo, precisa pular."""

    def __init__(self, owner, sp, x, vx):
        super().__init__(owner, sp, x, FLOOR_Y - 11, vx)
        self.dir = 1 if vx > 0 else -1

    def info(self):
        return hit_info(dmg=self.sp["dmg"], hitstun=22, blockstun=14, push=4, chip=0.15, sfx="pesado",
                        height="low", knockdown=True, projectile=True)

    def update(self, scene):
        if abs(self.vx) < 6.5:
            self.vx += 0.09 * self.dir
        self.angle -= self.vx * 7
        super().update(scene)
        if self.t % 5 == 0:
            scene.fx.dust(self.x - self.dir * 8, FLOOR_Y, 1)

    def draw(self, surf, off):
        img = pygame.transform.rotate(self.img, int(self.angle // 30) * 30)
        surf.blit(img, img.get_rect(center=(int(self.x + off[0]), int(self.y + off[1]))))

    def on_hit(self, target, result, scene):
        self.alive = False
        scene.fx.burst(self.x, self.y, [(238, 122, 25), (255, 200, 60), (250, 240, 200)], n=18, power=5)
        scene.shake = max(scene.shake, 5)


class Chain(Projectile):
    """Inquérito preso numa corrente: puxa o rival para perto do Xandão."""

    def __init__(self, owner, sp, x, y, vx):
        super().__init__(owner, sp, x, y, vx)
        self.start_x = x
        self.returning = False
        audio.sfx("corrente")

    def info(self):
        return hit_info(dmg=self.sp["dmg"], hitstun=30, blockstun=12, push=0, chip=0.0, sfx="corrente",
                        projectile=True, stun_state="pulled")

    def update(self, scene):
        self.t += 1
        hand = self.owner.hand_pos()
        if self.owner.state != "special":
            self.alive = False
            return
        if not self.returning:
            self.x += self.vx
            if abs(self.x - self.start_x) > self.sp.get("range", 260) or not (0 < self.x < GAME_W):
                self.returning = True
        else:
            dx = hand[0] - self.x
            step = min(abs(dx), 11)
            self.x += math.copysign(step, dx)
            self.y += (hand[1] - self.y) * 0.3
            if abs(dx) < 12:
                self.alive = False

    def check_hit(self, scene, target):
        if not self.returning:
            super().check_hit(scene, target)

    def on_hit(self, target, result, scene):
        self.returning = True
        if result == "hit":
            target.pull_to = self.owner
            scene.fx.text(target.x, target.y - 120, "INVESTIGADO!", (255, 230, 80), 18)

    def draw(self, surf, off):
        hx, hy = self.owner.hand_pos()
        dx, dy = self.x - hx, self.y - hy
        dist = math.hypot(dx, dy)
        n = int(dist // 6)
        for i in range(n):
            t = i / max(1, n)
            x, y = hx + dx * t + off[0], hy + dy * t + off[1]
            if i % 2:
                pygame.draw.ellipse(surf, (170, 170, 180), (x - 3, y - 2, 7, 4), 2)
            else:
                pygame.draw.ellipse(surf, (120, 120, 130), (x - 2, y - 3, 4, 7), 2)
        super().draw(surf, off)


class Bottle(Projectile):
    """Garrafa de 51 (super do Lula): explode e deixa o rival bêbado."""
    clash = False

    def __init__(self, owner, sp, x, y, vx):
        super().__init__(owner, sp, x, y, vx, -6.0)
        self.spin = 24 if vx > 0 else -24

    def update(self, scene):
        self.vy += 0.28
        super().update(scene)
        if self.y >= FLOOR_Y - 10:
            self.explode(scene)

    def check_hit(self, scene, target):
        hb = target.hurtbox()
        if self.alive and hb and hb.inflate(10, 10).colliderect(self.rect()):
            self.explode(scene)

    def explode(self, scene):
        if not self.alive:
            return
        self.alive = False
        audio.sfx("vidro")
        audio.sfx("explosao", 0.7)
        scene.shake = max(scene.shake, 10)
        scene.fx.ring(self.x, self.y, (250, 240, 200), 60, 18)
        scene.fx.burst(self.x, self.y, [(190, 225, 210), (240, 255, 250), (250, 205, 40)], n=26, power=6)
        scene.fx.burst(self.x, self.y, [(235, 235, 200), (220, 220, 170)], n=14, power=3, grav=0.05, life=(25, 45))
        target = scene.opponent(self.owner)
        hb = target.hurtbox()
        if hb and abs(target.x - self.x) < 70 and target.y - self.y < 140:
            info = hit_info(dmg=self.sp["dmg"], height="unblockable", knockdown=True, sfx="pesado", super=True,
                            launch=-7.0, effects={"drunk": 330}, projectile=True)
            if target.take_hit(info, self.owner, scene, from_x=self.x) == "hit":
                scene.fx.text(target.x, target.y - 130, "BÊBADO!", (255, 210, 60), 22, 70)


class StampStrike(Projectile):
    """Carimbo gigante CENSURADO (super do Xandão). Persegue o alvo e cai do céu."""
    clash = False
    TRACK, FALL, STAY = 30, 48, 80

    def __init__(self, owner, sp, target):
        self.target = target
        super().__init__(owner, sp, target.x, -80, 0)
        self.img = pygame.transform.scale(art.item("carimbo"), (84, 86))
        self.hit_done = False

    def update(self, scene):
        self.t += 1
        if self.t < self.TRACK:
            self.x += (self.target.x - self.x) * 0.09
            self.y = -80 + self.t * 0.8
        elif self.t < self.FALL:
            k = (self.t - self.TRACK) / (self.FALL - self.TRACK)
            self.y = -56 + (FLOOR_Y - 40 + 56) * k * k
        elif self.t == self.FALL:
            self.y = FLOOR_Y - 40
            self.impact(scene)
        elif self.t > self.STAY:
            self.y -= 9
            if self.y < -120:
                self.alive = False

    def impact(self, scene):
        audio.sfx("carimbo")
        scene.shake = max(scene.shake, 12)
        scene.fx.dust(self.x - 30, FLOOR_Y, 8)
        scene.fx.dust(self.x + 30, FLOOR_Y, 8)
        scene.zones.append(GroundStamp(self.x))
        t = self.target
        if abs(t.x - self.x) < 38 and t.y > FLOOR_Y - 120:
            info = hit_info(dmg=self.sp["dmg"], height="unblockable", knockdown=True, sfx="pesado", super=True,
                            launch=-5.0, effects={"silenced": 380, "stamp": 380}, spark=(255, 80, 80))
            if t.take_hit(info, self.owner, scene, from_x=self.x - (1 if t.x < self.x else -1)) == "hit":
                scene.fx.text(t.x, t.y - 135, "CENSURADO!", (230, 30, 40), 26, 80)
        else:
            scene.fx.text(self.x, FLOOR_Y - 70, "ERROU!", (255, 255, 255), 16)

    def check_hit(self, scene, target):
        pass

    def draw(self, surf, off):
        if self.t < self.FALL + 2:
            k = min(1.0, self.t / self.FALL)
            w = int(30 + 50 * k)
            shadow = pygame.Surface((w, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, int(70 + 90 * k)), shadow.get_rect())
            surf.blit(shadow, (int(self.x - w / 2 + off[0]), FLOOR_Y - 5 + off[1]))
        surf.blit(self.img, self.img.get_rect(midbottom=(int(self.x + off[0]), int(self.y + 40 + off[1]))))


# ------------------------------------------------------------------- zonas ---

class Puddle:
    """Poça de leite condensado: deixa lento quem pisa."""

    def __init__(self, owner, x):
        self.owner, self.x = owner, x
        self.life = 330
        self.alive = True

    def update(self, scene):
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        f = scene.opponent(self.owner)
        if f.grounded and abs(f.x - self.x) < 34:
            if f.status["slow"] < 20:
                f.status["slow"] = 20

    def draw(self, surf, off):
        a = min(255, self.life * 4)
        s = pygame.Surface((72, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (250, 244, 220, a), (0, 1, 72, 10))
        pygame.draw.ellipse(s, (255, 255, 250, a), (14, 2, 26, 4))
        pygame.draw.ellipse(s, (220, 205, 170, a), (0, 1, 72, 10), 1)
        surf.blit(s, (int(self.x - 36 + off[0]), FLOOR_Y - 6 + off[1]))


class GroundStamp:
    def __init__(self, x):
        self.x = x
        self.life = 240
        self.alive = True
        mark = art.stamp_mark(18)
        self.img = pygame.transform.scale(mark, (mark.get_width(), max(6, mark.get_height() // 3)))

    def update(self, scene):
        self.life -= 1
        self.alive = self.life > 0

    def draw(self, surf, off):
        img = self.img.copy()
        img.set_alpha(min(200, self.life * 3))
        surf.blit(img, img.get_rect(center=(int(self.x + off[0]), FLOOR_Y + 4 + off[1])))


def spawn_special(owner, sp, scene):
    """Cria o efeito do especial no momento do 'arremesso'."""
    kind = sp["kind"]
    hx, hy = owner.hand_pos()
    d = owner.facing
    if kind == "straight":
        scene.projectiles.append(Straight(owner, sp, owner.x + d * 30, owner.y + sp.get("y", -66), d * sp["speed"]))
    elif kind == "lob":
        scene.projectiles.append(Lob(owner, sp, hx, hy, d * sp["speed"]))
    elif kind == "roll":
        scene.projectiles.append(Roll(owner, sp, owner.x + d * 26, d * sp["speed"]))
    elif kind == "chain":
        scene.projectiles.append(Chain(owner, sp, hx, hy, d * sp["speed"]))
    elif kind == "bottle":
        scene.projectiles.append(Bottle(owner, sp, hx, hy, d * 5.2))
    elif kind == "stamp":
        scene.projectiles.append(StampStrike(owner, sp, scene.opponent(owner)))
    audio.sfx("whoosh", 0.6)
