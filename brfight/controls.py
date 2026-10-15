"""Entrada: teclado, joystick e a CPU (IA)."""
import random

import pygame

from .config import PAD_BUTTONS

ACTIONS = ("punch", "kick", "s1", "s2", "s3")


class InputState:
    __slots__ = ("up", "down", "left", "right", "pressed")

    def __init__(self):
        self.up = self.down = self.left = self.right = False
        self.pressed = set()


NEUTRAL = InputState()


class HumanController:
    """Teclado (keymap) + joystick opcional."""

    def __init__(self, keymap, joystick=None):
        self.keymap = keymap
        self.joy = joystick
        self.pending = set()

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            for action in ACTIONS:
                if e.key in self.keymap[action]:
                    self.pending.add(action)
        elif e.type == pygame.JOYBUTTONDOWN and self.joy is not None and e.instance_id == self.joy.get_instance_id():
            for action, buttons in PAD_BUTTONS.items():
                if e.button in buttons:
                    self.pending.add(action)

    def read(self, me=None, opp=None, scene=None):
        keys = pygame.key.get_pressed()
        inp = InputState()
        km = self.keymap
        inp.up = any(keys[k] for k in km["up"])
        inp.down = any(keys[k] for k in km["down"])
        inp.left = any(keys[k] for k in km["left"])
        inp.right = any(keys[k] for k in km["right"])
        if self.joy is not None:
            try:
                ax = self.joy.get_axis(0) if self.joy.get_numaxes() > 0 else 0
                ay = self.joy.get_axis(1) if self.joy.get_numaxes() > 1 else 0
                hx, hy = self.joy.get_hat(0) if self.joy.get_numhats() > 0 else (0, 0)
            except pygame.error:
                ax = ay = hx = hy = 0
            inp.left |= ax < -0.5 or hx < 0
            inp.right |= ax > 0.5 or hx > 0
            inp.up |= ay < -0.6 or hy > 0
            inp.down |= ay > 0.6 or hy < 0
        inp.pressed = self.pending
        self.pending = set()
        return inp


# Parâmetros por dificuldade: (reação em frames, chance de defender, agressividade)
AI_LEVELS = [(26, 0.18, 0.45), (15, 0.45, 0.6), (8, 0.75, 0.75)]


class AIController:
    def __init__(self, level=1):
        self.react, self.block_p, self.aggr = AI_LEVELS[level]
        self.level = level
        self.timer = 0
        self.plan = "idle"
        self.plan_t = 0
        self.flee_dir = 1
        self.rng = random.Random()

    def handle_event(self, e):
        pass

    def _threat(self, me, scene):
        for p in scene.projectiles:
            if p.owner is me or not p.alive:
                continue
            kind = p.sp["kind"]
            if kind == "stamp":
                if abs(p.x - me.x) < 70 and p.t < p.FALL - 2:
                    away = 1 if me.x >= p.x else -1
                    if not (60 < me.x + away * 70 < 580):
                        away = -away
                    self.flee_dir = away
                    return "stamp"
                continue
            toward = (p.x - me.x) * p.vx < 0
            if toward and abs(p.x - me.x) < 170:
                return "low" if kind == "roll" else "high" if p.y < me.y - 74 else "mid"
        return None

    def decide(self, me, opp, scene):
        r = self.rng.random
        dist = abs(opp.x - me.x)
        threat = self._threat(me, scene)
        if threat:
            if threat == "stamp":
                return "flee", 26
            if threat == "low":
                return ("jump_up", 10) if r() < 0.4 + self.block_p * 0.5 else ("block_low", 18)
            if threat == "high" and r() < 0.5:
                return "crouch", 20
            if r() < self.block_p + 0.15:
                return "block", 20
            if r() < 0.3:
                return "jump_in", 30
        opp_attacking = opp.state == "attack" or (opp.state == "special" and dist < 120)
        if opp_attacking and dist < 95 and r() < self.block_p:
            low = opp.state == "attack" and opp.attack and opp.attack["height"] == "low"
            return ("block_low" if low else "block"), 14
        if opp.state == "jump" and dist < 110 and r() < self.block_p:
            return ("anti_air", 6) if r() < 0.5 else ("block", 16)
        sp3 = me.data["specials"]["s3"]
        if me.meter >= 100 and not me.status["silenced"]:
            if sp3["kind"] == "buff" and dist < 260:
                return "s3", 4
            if sp3["kind"] == "bottle" and 90 < dist < 260:
                return "s3", 4
            if sp3["kind"] == "stamp" and r() < 0.5:
                return "s3", 4
        if opp.state in ("dizzy", "down", "getup") and dist < 70:
            return "kick", 8
        can = lambda slot: me.can_special(slot, scene)[0]
        kind2 = me.data["specials"]["s2"]["kind"]
        if dist > 210:
            roll = r()
            if roll < 0.35 and can("s1"):
                return "s1", 6
            if roll < 0.5 and can("s2") and kind2 != "chain":
                return "s2", 6
            if roll < 0.55 + self.aggr * 0.35:
                return "approach", 24
            return ("jump_in", 40) if r() < 0.3 else ("idle", 14)
        if dist > 75:
            roll = r()
            if kind2 == "chain" and roll < 0.25 and can("s2") and dist < 250:
                return "s2", 6
            if roll < 0.15 and can("s1"):
                return "s1", 6
            if roll < 0.2 + self.aggr * 0.5:
                return "approach", 16
            if roll < 0.8:
                return "jump_in", 40
            return "retreat", 14
        roll = r()
        if roll < 0.3:
            return "punch", 6
        if roll < 0.52:
            return "kick", 8
        if roll < 0.66:
            return "sweep", 8
        if roll < 0.66 + self.block_p * 0.3:
            return "block", 14
        if roll < 0.9:
            return "retreat", 12
        return "jump_back", 20

    def read(self, me, opp, scene):
        inp = InputState()
        self.timer -= 1
        self.plan_t += 1
        if self.timer <= 0:
            self.plan, dur = self.decide(me, opp, scene)
            self.plan_t = 0
            self.timer = dur + self.rng.randint(0, self.react)
        fwd_right = opp.x > me.x
        plan = self.plan

        def hold_fwd():
            inp.right, inp.left = fwd_right, not fwd_right

        def hold_back():
            inp.right, inp.left = not fwd_right, fwd_right

        first = self.plan_t == 0
        if plan == "approach":
            hold_fwd()
        elif plan == "retreat":
            hold_back()
        elif plan == "flee":
            inp.right, inp.left = self.flee_dir > 0, self.flee_dir < 0
        elif plan == "block":
            hold_back()
        elif plan == "block_low":
            hold_back()
            inp.down = True
        elif plan == "crouch":
            inp.down = True
        elif plan in ("jump_in", "jump_up", "jump_back"):
            if first:
                inp.up = True
                if plan == "jump_in":
                    hold_fwd()
                elif plan == "jump_back":
                    hold_back()
            if plan == "jump_in" and me.state == "jump" and me.vy > 0 and abs(opp.x - me.x) < 70:
                inp.pressed.add("kick" if self.rng.random() < 0.7 else "punch")
        elif plan in ("punch", "kick", "anti_air") and first:
            inp.pressed.add("kick" if plan == "kick" else "punch")
        elif plan == "sweep":
            inp.down = True
            if first:
                inp.pressed.add("kick")
        elif plan in ("s1", "s2", "s3") and first:
            inp.pressed.add(plan)
        # combo: emenda especial depois de acertar um soco
        if me.state == "attack" and me.attack_hit and self.level > 0 and self.rng.random() < 0.08 * (self.level + 1):
            inp.pressed.add("s1")
        return inp
