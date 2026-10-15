"""Lutador: máquina de estados, física, golpes, especiais e desenho."""
import math
import random
from collections import defaultdict

import pygame

from . import art, audio, gfx
from .characters import CHARACTERS, style_for
from .config import FLOOR_Y, GRAVITY, METER_MAX, STAGE_LEFT, STAGE_RIGHT
from .projectiles import hit_info, spawn_special

FREE = ("idle", "walk", "crouch")
STUNNED = ("hit", "air_hit", "pulled", "dizzy")

# reach = alcance horizontal a partir do centro; box_y = faixa vertical relativa aos pés
NORMALS = {
    "punch": dict(startup=4, active=3, recovery=9, dmg=5, reach=(8, 42), box_y=(-86, -64), hitstun=16,
                  blockstun=9, push=3.2, height="mid", sfx="soco"),
    "kick": dict(startup=7, active=4, recovery=14, dmg=8, reach=(10, 52), box_y=(-64, -38), hitstun=19,
                 blockstun=11, push=4.6, height="mid", sfx="chute", heavy=True),
    "c_punch": dict(startup=4, active=3, recovery=9, dmg=4, reach=(8, 42), box_y=(-62, -44), hitstun=15,
                    blockstun=8, push=3.0, height="mid", sfx="soco"),
    "c_kick": dict(startup=7, active=4, recovery=18, dmg=7, reach=(10, 54), box_y=(-20, 0), hitstun=20,
                   blockstun=12, push=4.0, height="low", sfx="chute", knockdown=True, heavy=True),
    "j_punch": dict(startup=3, active=10, recovery=3, dmg=6, reach=(4, 40), box_y=(-72, -44), hitstun=17,
                    blockstun=10, push=3.0, height="high", sfx="soco"),
    "j_kick": dict(startup=4, active=12, recovery=3, dmg=9, reach=(2, 44), box_y=(-44, -8), hitstun=19,
                   blockstun=11, push=4.0, height="high", sfx="chute", heavy=True),
}

STANCE = dict(lean=6, fa=(20, 140), ba=(10, 150), fl=(18, 22), bl=(-16, 6), expr="normal")
CROUCH = dict(lean=22, fl=(60, 125), bl=(40, 120), fa=(25, 135), ba=(15, 145))
JUMP = dict(lean=2, fl=(55, 110), bl=(15, 95), fa=(60, 90), ba=(20, 110))
HURT = dict(lean=-18, head=(-2, 0), fa=(-30, 40), ba=(-50, 30), expr="hurt")
BLOCK = dict(lean=-6, fa=(55, 145), ba=(45, 150))

ATTACK_POSES = {
    "punch": (dict(lean=4, fa=(5, 150)), dict(lean=16, fa=(88, 0), ba=(5, 140), expr="shout")),
    "kick": (dict(lean=-4, fl=(60, 90)), dict(lean=-14, fl=(100, 0), bl=(-6, 0), fa=(40, 120), ba=(-30, 60))),
    "c_punch": ({**CROUCH, "fa": (0, 150)}, {**CROUCH, "lean": 26, "fa": (85, 0), "expr": "shout"}),
    "c_kick": (CROUCH, {**CROUCH, "lean": 26, "bl": (40, 120), "fl": (86, 0), "fa": (30, 120)}),
    "j_punch": ({**JUMP, "fa": (10, 150)}, {**JUMP, "lean": 10, "fa": (62, 0), "expr": "shout"}),
    "j_kick": (JUMP, {**JUMP, "lean": -8, "fl": (55, 0), "bl": (10, 100)}),
}

# tempo (frames) do momento de soltar e da duração total de cada tipo de especial
SPECIAL_TIMING = {
    "straight": (14, 34), "lob": (14, 34), "roll": (16, 38), "bottle": (16, 40),
    "chain": (10, 72), "buff": (24, 58), "stamp": (14, 46),
}


def blend(a, b, k):
    k = max(0.0, min(1.0, k))
    out = dict(a)
    for key, v in b.items():
        av = a.get(key)
        if isinstance(v, (int, float)) and isinstance(av, (int, float)):
            out[key] = av + (v - av) * k
        elif isinstance(v, tuple) and isinstance(av, tuple):
            out[key] = tuple(x + (y - x) * k for x, y in zip(av, v))
        else:
            out[key] = v if k >= 0.5 or av is None else av
    return out


class Fighter:
    def __init__(self, char_id, player, alt=False):
        self.id = char_id
        self.data = CHARACTERS[char_id]
        self.style = style_for(char_id, alt)
        self.player = player
        self.meter = 0.0
        self.round_wins = 0
        self.reset(200, 1)

    # ------------------------------------------------------------ estado ---
    def reset(self, x, facing):
        self.x, self.y = float(x), float(FLOOR_Y)
        self.vx = self.vy = 0.0
        self.facing = facing
        self.hp = self.hp_trail = 100.0
        self.trail_delay = 0
        self.state, self.t = "idle", 0
        self.anim_t = 0
        self.attack = None
        self.attack_hit = False
        self.air_attack_used = False
        self.stun = 0
        self.status = defaultdict(int)
        self.cool = {"s1": 0, "s2": 0}
        self.combo = 0
        self.combo_timer = 0
        self.flash = 0
        self.invuln = 0
        self.special = None
        self.spawned = False
        self.bubble = None
        self.bubble_t = 0
        self.holding_back = False
        self.holding_down = False
        self.pull_to = None
        self.dead = False
        self.buf = {}
        self.walk_ph = 0.0

    def set_state(self, st):
        if st != self.state:
            self.state = st
            self.t = 0

    @property
    def grounded(self):
        return self.y >= FLOOR_Y and self.vy >= 0

    @property
    def crouching(self):
        if self.state == "crouch" or (self.state == "attack" and self.attack["name"].startswith("c_")):
            return True
        return self.state == "block" and self.holding_down

    def say(self, line_id, text):
        self.bubble = text
        self.bubble_t = 110
        v = self.data["voice"]
        audio.voice(self.id, line_id, text, v["pitch"], v["rasp"], slot=1 + self.player)

    def consume(self, action):
        if self.buf.get(action, 0) > 0:
            del self.buf[action]
            return True
        return False

    def walk_speed(self):
        sp = self.data["walk"]
        if self.status["slow"]:
            sp *= 0.5
        if self.status["buff"]:
            sp *= 1.3
        return sp

    # ---------------------------------------------------------- atualizar ---
    def update(self, inp, opp, scene):
        self.t += 1
        self.anim_t += 1
        for k in list(self.status):
            if self.status[k] > 0:
                self.status[k] -= 1
        for k in self.cool:
            if self.cool[k] > 0:
                self.cool[k] -= 1
        self.flash = max(0, self.flash - 1)
        self.invuln = max(0, self.invuln - 1)
        self.bubble_t = max(0, self.bubble_t - 1)
        self.combo_timer = max(0, self.combo_timer - 1)
        if self.trail_delay > 0:
            self.trail_delay -= 1
        elif self.hp_trail > self.hp:
            self.hp_trail = max(self.hp, self.hp_trail - 0.6)

        for a in list(self.buf):
            self.buf[a] -= 1
            if self.buf[a] <= 0:
                del self.buf[a]
        for a in inp.pressed:
            self.buf[a] = 8

        left, right = inp.left, inp.right
        if self.status["drunk"]:
            left, right = right, left
            if self.status["drunk"] % 50 == 0:
                scene.fx.text(self.x, self.y - 128, "HIC!", (255, 230, 150), 14, 30)

        st = self.state
        if st in ("intro", "win", "ko"):
            self.physics(scene)
            return

        if st in FREE:
            self.facing = 1 if opp.x >= self.x else -1
        fwd = right if self.facing == 1 else left
        back = left if self.facing == 1 else right
        self.holding_back = back and not fwd
        self.holding_down = inp.down

        if st in FREE:
            if self._try_specials(scene):
                pass
            elif self.consume("punch"):
                self.start_attack("c_punch" if inp.down else "punch")
            elif self.consume("kick"):
                self.start_attack("c_kick" if inp.down else "kick")
            elif inp.up:
                self.jump(fwd, back)
            elif inp.down:
                self.set_state("crouch")
                self.vx = 0
            elif fwd or back:
                self.set_state("walk")
                sp = self.walk_speed()
                self.vx = self.facing * (sp if fwd else -sp * 0.8)
                self.walk_ph += abs(self.vx) * 0.11
            else:
                self.set_state("idle")
                self.vx = 0
        elif st == "jump":
            if not self.air_attack_used:
                if self.consume("punch"):
                    self.start_attack("j_punch", air=True)
                elif self.consume("kick"):
                    self.start_attack("j_kick", air=True)
        elif st == "attack":
            a = self.attack
            if self.attack_hit and not a["air"] and self.t >= a["startup"] + 2 and self._try_specials(scene):
                pass
            elif self.t >= a["total"]:
                if a["air"]:
                    self.state = "jump"
                else:
                    self.set_state("crouch" if inp.down else "idle")
        elif st == "special":
            self.update_special(scene)
        elif st == "hit":
            if self.t >= self.stun:
                self.set_state("idle")
        elif st == "block":
            if self.t >= self.stun:
                self.set_state("crouch" if inp.down else "idle")
        elif st == "pulled":
            tgt = self.pull_to
            if tgt is None:
                self.set_state("idle")
            else:
                goal = tgt.x + tgt.facing * 46
                dx = goal - self.x
                self.x += max(-12, min(12, dx * 0.3))
                if abs(dx) < 4 or self.t > 22:
                    self.set_state("dizzy")
                    self.stun = 28
                    self.pull_to = None
        elif st == "dizzy":
            if self.t >= self.stun:
                self.set_state("idle")
        elif st == "down":
            if self.t >= 38:
                self.set_state("getup")
                self.invuln = 22
        elif st == "getup":
            if self.t >= 16:
                self.set_state("idle")
        self.physics(scene)

    def physics(self, scene):
        if self.y < FLOOR_Y or self.vy < 0:
            self.vy += GRAVITY
            self.y += self.vy
            self.x += self.vx
            if self.y >= FLOOR_Y:
                self.y = FLOOR_Y
                self.vy = 0
                self.on_land(scene)
        else:
            self.x += self.vx
            if self.state not in ("walk",):
                self.vx *= 0.8
                if abs(self.vx) < 0.05:
                    self.vx = 0
        self.x = max(STAGE_LEFT, min(STAGE_RIGHT, self.x))

    def on_land(self, scene):
        st = self.state
        if st == "jump" or (st == "attack" and self.attack["air"]):
            self.set_state("idle")
            self.vx = 0
            scene.fx.dust(self.x, FLOOR_Y, 4)
        elif st == "air_hit":
            audio.sfx("queda", 0.8)
            scene.fx.dust(self.x, FLOOR_Y, 10)
            scene.shake = max(scene.shake, 4)
            self.vx *= 0.3
            self.set_state("ko" if self.dead else "down")
        elif st in ("hit", "dizzy", "pulled"):
            pass

    def jump(self, fwd, back):
        self.set_state("jump")
        self.vy = self.data["jump"] * (0.86 if self.status["slow"] else 1.0)
        mult = 1.25 if self.status["buff"] else 1.0
        self.vx = self.facing * (3.1 if fwd else -2.7 if back else 0.0) * mult
        if self.status["slow"]:
            self.vx *= 0.6
        self.air_attack_used = False
        audio.sfx("pulo", 0.5)

    # ------------------------------------------------------------- golpes ---
    def start_attack(self, name, air=False):
        a = dict(NORMALS[name])
        a["name"] = name
        a["air"] = air
        a["total"] = a["startup"] + a["active"] + a["recovery"]
        if self.status["buff"]:
            a["recovery"] = int(a["recovery"] * 0.7)
            a["total"] = a["startup"] + a["active"] + a["recovery"]
        self.attack = a
        self.attack_hit = False
        self.set_state("attack")
        if air:
            self.air_attack_used = True
        else:
            self.vx = 0
        audio.sfx("whoosh", 0.25)

    def attack_box(self):
        if self.state != "attack" or self.attack_hit:
            return None
        a = self.attack
        if not (a["startup"] <= self.t < a["startup"] + a["active"]):
            return None
        r0, r1 = a["reach"]
        y0, y1 = a["box_y"]
        if self.facing == 1:
            x0, x1 = self.x + r0, self.x + r1
        else:
            x0, x1 = self.x - r1, self.x - r0
        return pygame.Rect(int(x0), int(self.y + y0), int(x1 - x0), int(y1 - y0))

    def hurtbox(self):
        if self.state in ("down", "ko") or self.dead:
            return None
        if self.crouching:
            h = 70
        elif not self.grounded:
            return pygame.Rect(int(self.x - 15), int(self.y - 98), 30, 88)
        else:
            h = 108
        return pygame.Rect(int(self.x - 15), int(self.y - h), 30, h)

    def make_hit_info(self):
        a = self.attack
        dmg = a["dmg"] * self.data["power"] * (1.6 if self.status["buff"] else 1.0)
        return hit_info(dmg=dmg, hitstun=a["hitstun"], blockstun=a["blockstun"], push=a["push"],
                        height=a["height"], knockdown=a.get("knockdown", False), sfx=a["sfx"],
                        heavy=a.get("heavy", False))

    # ---------------------------------------------------------- especiais ---
    def owns_projectile(self, scene):
        return any(p.owner is self and p.alive and not p.sp.get("super") for p in scene.projectiles)

    def can_special(self, slot, scene):
        sp = self.data["specials"][slot]
        if self.status["silenced"]:
            return False, "CALADO!"
        if sp.get("super"):
            return (self.meter >= METER_MAX), None
        if self.cool[slot] > 0 or self.owns_projectile(scene):
            return False, None
        return True, None

    def _try_specials(self, scene):
        for slot in ("s3", "s2", "s1"):
            if self.buf.get(slot):
                ok, why = self.can_special(slot, scene)
                self.consume(slot)
                if ok:
                    self.start_special(slot, scene)
                    return True
                if why:
                    scene.fx.text(self.x, self.y - 130, why, (255, 80, 80), 14, 35)
        return False

    def start_special(self, slot, scene):
        sp = self.data["specials"][slot]
        self.set_state("special")
        self.special = sp
        self.spawned = False
        self.vx = 0
        self.say(sp["id"], sp["fala"])
        if sp.get("super"):
            self.meter = 0
            self.invuln = 34
            audio.sfx("super")
            scene.super_flash(self, sp)
        else:
            self.cool[slot] = sp.get("cooldown", 60)
            audio.sfx("especial", 0.5)

    def update_special(self, scene):
        sp = self.special
        kind = sp["kind"]
        release, total = SPECIAL_TIMING[kind]
        if self.t >= release and not self.spawned:
            self.spawned = True
            if kind == "buff":
                self.status["buff"] = 540
                self.hp = min(100.0, self.hp + 10)
                self.hp_trail = max(self.hp_trail, self.hp)
                audio.sfx("comer")
                scene.fx.ring(self.x, self.y - 60, (110, 160, 255), 60, 20)
                scene.fx.text(self.x, self.y - 140, "IMBROCHÁVEL!", (120, 180, 255), 24, 80)
            else:
                spawn_special(self, sp, scene)
        if kind == "chain" and self.spawned and self.t > release + 2:
            if not any(p.owner is self and p.alive for p in scene.projectiles):
                self.set_state("idle")
                return
        if self.t >= total:
            self.set_state("idle")

    # ------------------------------------------------------------ dano ---
    def take_hit(self, info, attacker, scene, from_x=None, at=None):
        if self.state in ("down", "ko") or self.dead or self.invuln > 0:
            return None
        from_x = attacker.x if from_x is None else from_x
        direction = 1 if self.x >= from_x else -1
        hb = self.hurtbox()
        if at is None:
            at = (self.x - direction * 12, (hb.top + 30) if hb else self.y - 70)

        can_block = (self.state in FREE + ("block",) and self.grounded and self.holding_back
                     and info["height"] != "unblockable")
        if info["height"] == "low" and not self.holding_down:
            can_block = False
        if info["height"] == "high" and self.holding_down:
            can_block = False
        if can_block:
            self.set_state("block")
            self.stun = info["blockstun"]
            self.vx = direction * info["push"] * 0.9
            self.hp = max(1.0, self.hp - info["dmg"] * info["chip"])
            self.trail_delay = 25
            self.meter = min(METER_MAX, self.meter + 2)
            attacker.meter = min(METER_MAX, attacker.meter + 2)
            audio.sfx("bloqueio")
            scene.fx.block(*at)
            scene.hitstop = 4
            return "block"

        dmg = info["dmg"] * self.data["defense"]
        if self.state in STUNNED or (self.state == "attack" and not self.grounded and attacker.combo):
            attacker.combo += 1
        else:
            attacker.combo = 1
        dmg *= max(0.45, 1 - 0.12 * (attacker.combo - 1))
        attacker.combo_timer = 70
        self.hp = max(0.0, self.hp - dmg)
        self.trail_delay = 30
        attacker.meter = min(METER_MAX, attacker.meter + dmg * 1.3)
        self.meter = min(METER_MAX, self.meter + dmg * 0.8)
        for k, v in (info["effects"] or {}).items():
            self.status[k] = max(self.status[k], v)
        if info["effects"] and "drunk" in info["effects"]:
            self.status["buff"] = 0
        self.flash = 7
        audio.sfx(info["sfx"], 0.9 if info["heavy"] else 0.75)
        scene.fx.spark(at[0], at[1], info["spark"], n=14 if info["heavy"] else 9, power=5 if info["heavy"] else 3.5)
        scene.hitstop = 8 if (info["heavy"] or info["super"]) else 5
        if info["heavy"] or info["super"]:
            scene.shake = max(scene.shake, 5)

        if self.hp <= 0:
            self.dead = True
            self.set_state("air_hit")
            self.vy = -7.5
            self.vx = direction * 4.2
            self.facing = -direction
            scene.on_ko(self, attacker)
            return "hit"

        armor = self.status["buff"] and not info["knockdown"] and not info["super"] and info["stun_state"] is None
        if armor:
            scene.fx.text(self.x, self.y - 120, "NEM SENTIU!", (140, 190, 255), 13, 30)
            return "hit"

        self.facing = -direction
        self.attack = None if self.state != "attack" else self.attack
        if info["stun_state"] == "pulled" and self.grounded:
            self.set_state("pulled")
            self.pull_to = attacker
        elif info["knockdown"] or not self.grounded:
            self.set_state("air_hit")
            self.vy = info["launch"]
            self.vx = direction * 3.2
        else:
            self.set_state("hit")
            self.stun = info["hitstun"]
            self.vx = direction * info["push"]
        return "hit"

    def hand_pos(self):
        sk = art.skeleton(self.pose(), self.state not in ("jump", "air_hit") and self.grounded)
        hx, hy = sk["hand_f"]
        return self.x + (hx - art.AX) * self.facing, self.y + (hy - art.AY)

    # ------------------------------------------------------------- poses ---
    def pose(self):
        st, t = self.state, self.t
        breath = math.sin(self.anim_t * 0.08)
        base = dict(STANCE)
        base["fl"] = (18, 22 + 5 * breath)
        base["bl"] = (-16, 6 + 5 * breath)
        base["lean"] = 6 + breath
        if self.style["outfit"] == "toga":
            base["cape"] = max(-4, min(10, -self.vx * self.facing * 3 + math.sin(self.anim_t * 0.1) * 1.5))
        p = base
        if st == "idle":
            pass
        elif st == "walk":
            ph = self.walk_ph
            p = {**base, "fl": (4 + 26 * math.sin(ph), 10 + 28 * max(0, math.cos(ph))),
                 "bl": (4 - 26 * math.sin(ph), 10 + 28 * max(0, -math.cos(ph))), "lean": 8}
        elif st == "crouch":
            p = {**base, **CROUCH}
        elif st == "getup":
            p = {**base, **CROUCH} if t < 8 else base
        elif st == "jump":
            p = {**base, **JUMP} if self.vy > -4 else {**base, **JUMP, "fl": (30, 60), "bl": (-10, 40)}
        elif st == "attack":
            a = self.attack
            wind, act = ATTACK_POSES[a["name"]]
            start = {**base, **(JUMP if a["air"] else CROUCH if a["name"].startswith("c_") else {})}
            w = {**start, **wind}
            h = {**start, **act}
            if t < a["startup"]:
                p = blend(start, w, t / max(1, a["startup"] - 1))
            elif t < a["startup"] + a["active"] or a["air"]:
                p = h
            else:
                p = blend(h, start, (t - a["startup"] - a["active"]) / max(1, a["recovery"]))
        elif st == "special":
            p = self._special_pose(base)
        elif st in ("hit", "pulled"):
            p = {**base, **HURT}
        elif st == "block":
            p = {**base, **(CROUCH if self.holding_down else {}), **BLOCK}
        elif st == "dizzy":
            p = {**base, "lean": 4 + math.sin(self.anim_t * 0.2) * 7, "fa": (5, 10), "ba": (-5, 10), "expr": "hurt"}
        elif st == "air_hit":
            p = {**base, **HURT, "fl": (30, 20), "bl": (-20, 10)}
        elif st in ("down", "ko"):
            p = {**base, **HURT, "lean": 0, "fl": (8, 0), "bl": (-4, 0), "fa": (165, 10), "ba": (150, 10),
                 "expr": "ko" if st == "ko" else "hurt"}
        elif st == "win":
            bounce = abs(math.sin(self.anim_t * 0.12))
            p = {**base, "lean": -4, "fa": (165 + bounce * 10, 10), "ba": (20, 30), "expr": "happy",
                 "lift": bounce * 3}
        elif st == "intro":
            p = {**base, "fa": (50, 120), "ba": (45, 125)}
        if self.bubble_t > 0 and p.get("expr", "normal") == "normal":
            p = {**p, "expr": "shout" if (self.anim_t // 5) % 2 else "normal"}
        return p

    def _special_pose(self, base):
        sp = self.special
        kind = sp["kind"]
        t = self.t
        release, _ = SPECIAL_TIMING[kind]
        before = t < release
        if kind in ("straight", "lob", "bottle"):
            if before:
                return {**base, "lean": -6, "fa": (-150, 30), "ba": (30, 100), "hold": sp["item"], "expr": "shout"}
            return {**base, "lean": 18, "fa": (100, -10), "ba": (-20, 40), "expr": "shout"}
        if kind == "roll":
            low = {**base, **CROUCH, "lean": 30}
            if before:
                return {**low, "fa": (-60, 0), "hold": sp["item"], "expr": "shout"}
            return {**low, "fa": (70, 0), "expr": "shout"}
        if kind == "chain":
            if before:
                return {**base, "fa": (-40, 60), "expr": "shout"}
            return {**base, "lean": 12, "fa": (90, 0), "expr": "shout"}
        if kind == "buff":
            if before:
                return {**base, "fa": (150, 120), "hold": sp["item"] if t < release - 6 else None, "expr": "eat"}
            return {**base, "lean": -4, "fa": (90, 90), "ba": (-90, -90), "expr": "shout"}
        if kind == "stamp":
            return {**base, "lean": -6, "fa": (175, 0), "ba": (20, 40), "expr": "shout"}
        return base

    # ----------------------------------------------------------- desenho ---
    def draw(self, surf, off):
        pose = self.pose()
        grounded = self.state not in ("jump", "air_hit") and not (self.state == "attack" and self.attack["air"])
        img, _ = art.render(self.style, pose, grounded, silenced=self.status["silenced"] > 0,
                            drunk=self.status["drunk"] > 0)
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        wob = math.sin(self.anim_t * 0.15) * 3 if self.status["drunk"] else 0
        x = self.x + off[0] + wob
        y = self.y + off[1]

        height = FLOOR_Y - self.y
        sw = int(46 * max(0.5, 1 - height / 220))
        shadow = pygame.Surface((sw, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surf.blit(shadow, (int(self.x + off[0] - sw / 2), FLOOR_Y - 4 + off[1]))

        if self.state in ("down", "ko"):
            r = pygame.transform.rotate(img, 90 if self.facing == 1 else -90)
            br = r.get_bounding_rect()
            body_x = max(56, min(584, x - self.facing * 22))
            dest = (int(body_x - br.centerx), int(FLOOR_Y + off[1] + 3 - br.bottom))
        elif self.state == "air_hit":
            ang = min(70, self.t * 4) * self.facing
            r = pygame.transform.rotate(img, ang)
            dest = r.get_rect(center=(int(x), int(y - 60)))
            dest = dest.topleft
        else:
            r = img
            dest = (int(x - art.AX), int(y - art.AY))

        if self.status["buff"]:
            pulse = 110 + int(60 * math.sin(self.anim_t * 0.3))
            aura = gfx.silhouette(r, (90, 150, 255, pulse))
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                surf.blit(aura, (dest[0] + dx, dest[1] + dy))
        surf.blit(r, dest)
        if self.flash > 0:
            surf.blit(gfx.silhouette(r, (255, 255, 255, 130 if self.flash > 4 else 60)), dest)

        top = self.y - (80 if self.crouching else 112) + off[1]
        if self.status["stamp"] and self.state not in ("down", "ko"):
            m = art.stamp_mark(16)
            surf.blit(m, m.get_rect(center=(int(x), int(self.y - 55 + off[1]))))
        if self.state == "dizzy" or self.state == "pulled":
            for i in range(3):
                a = self.anim_t * 0.15 + i * 2.09
                sx, sy = x + math.cos(a) * 16, top - 8 + math.sin(a) * 4
                pygame.draw.polygon(surf, (255, 230, 60), [(sx, sy - 3), (sx + 1, sy - 1), (sx + 3, sy),
                                                          (sx + 1, sy + 1), (sx, sy + 3), (sx - 1, sy + 1),
                                                          (sx - 3, sy), (sx - 1, sy - 1)])
        if self.status["slow"]:
            for i in range(3):
                dy = (self.anim_t * 0.5 + i * 7) % 18
                pygame.draw.rect(surf, (250, 244, 220), (int(x - 10 + i * 9), int(y - 22 + dy), 3, 4))

    def draw_bubble(self, surf, off, avoid=None):
        """Balão de fala acima da cabeça. `avoid` = retângulo de outro balão para não sobrepor."""
        if self.bubble_t <= 0 or not self.bubble or self.state in ("down", "ko"):
            return None
        txt = gfx.text_surface(self.bubble, 15, (20, 20, 30), outline=None)
        w, h = txt.get_width() + 12, txt.get_height() + 4
        cx = int(self.x + off[0])
        top = int(self.y - (90 if self.crouching else 124) - h + off[1])
        bx = max(4, min(surf.get_width() - w - 4, cx - w // 2))
        rect = pygame.Rect(bx, top, w, h)
        tail = 8
        if avoid is not None and rect.colliderect(avoid.inflate(4, 4)):
            rect.bottom = avoid.top - 6
            tail = 8 + (top - rect.top)
        cx = max(rect.left + 8, min(rect.right - 8, cx))
        tip = (cx, rect.bottom + tail)
        pygame.draw.polygon(surf, (255, 255, 255), [(cx - 4, rect.bottom - 1), (cx + 4, rect.bottom - 1), tip])
        pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=6)
        pygame.draw.rect(surf, (20, 20, 30), rect, 2, border_radius=6)
        pygame.draw.lines(surf, (20, 20, 30), False, [(cx - 4, rect.bottom), tip, (cx + 4, rect.bottom)], 2)
        surf.blit(txt, (rect.left + 6, rect.top + 2))
        return rect


def random_win_line(fighter):
    return random.choice(fighter.data["wins"])
