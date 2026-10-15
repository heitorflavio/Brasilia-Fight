"""Telas do jogo: título, seleção de personagem, VS, luta e resultado."""
import math
import random

import pygame

from . import art, audio, gfx
from .characters import CHARACTERS, ORDER, style_for
from .config import (DIFFICULTIES, GAME_H, GAME_W, KEYMAP_P1, KEYMAP_P2, ROUND_TIME, ROUNDS_TO_WIN,
                     STAGE_LEFT, STAGE_RIGHT)
from .controls import NEUTRAL, AIController, HumanController
from .fighter import FREE, Fighter, random_win_line
from .fx import FX
from .hud import HUD

CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def _dark(surf, alpha=150, color=(0, 0, 0)):
    s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    s.fill((*color, alpha))
    surf.blit(s, (0, 0))


class Scene:
    def __init__(self, game):
        self.game = game
        self.t = 0

    def handle(self, events):
        pass

    def update(self):
        self.t += 1

    def draw(self, surf):
        pass


# ------------------------------------------------------------------ título ---

class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.sel = 0
        audio.play_music()
        self.styles = [style_for(c) for c in ORDER]

    @property
    def options(self):
        return ["1 JOGADOR (vs CPU)", "2 JOGADORES", "CPU x CPU", f"DIFICULDADE: {DIFFICULTIES[self.game.difficulty]}",
                "SAIR"]

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = (self.sel - 1) % len(self.options)
                    audio.sfx("select")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = (self.sel + 1) % len(self.options)
                    audio.sfx("select")
                elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) and self.sel == 3:
                    step = 1 if e.key in (pygame.K_RIGHT, pygame.K_d) else -1
                    self.game.difficulty = (self.game.difficulty + step) % len(DIFFICULTIES)
                    audio.sfx("select")
                elif e.key in CONFIRM_KEYS + (pygame.K_j,):
                    self.choose()
                elif e.key == pygame.K_ESCAPE:
                    self.game.running = False
            elif e.type == pygame.JOYBUTTONDOWN and e.button == 0:
                self.choose()
            elif e.type == pygame.JOYHATMOTION and e.value[1]:
                self.sel = (self.sel - e.value[1]) % len(self.options)

    def choose(self):
        audio.sfx("confirmar")
        if self.sel == 0:
            self.game.change(SelectScene(self.game, "1p"))
        elif self.sel == 1:
            self.game.change(SelectScene(self.game, "2p"))
        elif self.sel == 2:
            self.game.change(SelectScene(self.game, "cpu"))
        elif self.sel == 3:
            self.game.difficulty = (self.game.difficulty + 1) % len(DIFFICULTIES)
        else:
            self.game.running = False

    def draw(self, surf):
        st = self.game.stages[0]
        st.update()
        st.draw(surf)
        _dark(surf, 120, (10, 0, 30))
        logo1 = gfx.gradient_text("BRASÍLIA", 64, (120, 255, 140), (10, 140, 60), ow=3)
        logo2 = gfx.gradient_text("FIGHT", 78, (255, 250, 150), (255, 150, 20), ow=3)
        y = 18 + int(math.sin(self.t * 0.05) * 3)
        surf.blit(logo1, logo1.get_rect(midtop=(GAME_W // 2, y)))
        surf.blit(logo2, logo2.get_rect(midtop=(GAME_W // 2, y + 46)))
        gfx.draw_text(surf, "Edição Sátira Política  •  Turbo Pamonha", 15, (GAME_W // 2, y + 112),
                      (255, 255, 255), "midtop")
        positions = [(60, 200), (130, 214), (GAME_W - 134, 200)]
        for i, s in enumerate(self.styles):
            p = art.portrait(s, 2, "shout" if (self.t // 30 + i) % 3 == 0 else "normal")
            if i == 2:
                p = pygame.transform.flip(p, True, False)
            bob = int(abs(math.sin(self.t * 0.07 + i)) * 6)
            x, y = positions[i]
            surf.blit(p, (x, y - bob))
        for i, opt in enumerate(self.options):
            active = i == self.sel
            col = (255, 230, 60) if active else (220, 220, 230)
            label = f"> {opt} <" if active and (self.t // 15) % 2 else opt
            gfx.draw_text(surf, label, 22, (GAME_W // 2, 178 + i * 26), col, "midtop", ow=2)
        gfx.draw_text(surf, "Setas/WASD + Enter  •  F11 tela cheia  •  M música", 13, (GAME_W // 2, GAME_H - 38),
                      (200, 200, 210), "midtop")
        if st.credit:
            gfx.draw_text(surf, st.credit, 12, (GAME_W // 2, GAME_H - 19), (170, 170, 180), "midtop")


# --------------------------------------------------------------- seleção ---

class SelectScene(Scene):
    CARD_W, CARD_H = 124, 160
    # quadros (~0,25 s) em que o cursor ignora entrada: um Enter repetido (ou "tremido" pelo
    # teclado) não pode confirmar ao entrar na tela nem travar o adversário junto com o P1
    GUARD = 15

    def __init__(self, game, mode):
        super().__init__(game)
        self.mode = mode
        self.cur = [0, 2]
        self.locked = [False, False]
        self.wait = [self.GUARD, self.GUARD]
        self.done_t = 0
        self.styles = {c: style_for(c) for c in ORDER}

    def _move(self, who, d):
        if not self.locked[who] and not self.wait[who]:
            self.cur[who] = (self.cur[who] + d) % len(ORDER)
            audio.sfx("select")

    def _confirm(self, who):
        if not self.locked[who] and not self.wait[who]:
            self.locked[who] = True
            if who == 0 and self.mode != "2p":
                self.wait[1] = self.GUARD  # o mesmo teclado passa a escolher o adversário
            audio.sfx("confirmar")
            cid = ORDER[self.cur[who]]
            audio.voice(cid, "nome", CHARACTERS[cid]["name"].title() + "!",
                        CHARACTERS[cid]["voice"]["pitch"], CHARACTERS[cid]["voice"]["rasp"], slot=1 + who)

    def _active(self):
        """Quem está escolhendo com o teclado do P1 nos modos 1 jogador e CPU x CPU."""
        return 0 if not self.locked[0] else 1

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.mode != "2p" and self.locked[0] and not self.locked[1]:
                        self.locked[0] = False
                    elif self.mode == "2p" and any(self.locked) and not all(self.locked):
                        self.locked = [False, False]
                    else:
                        self.game.change(TitleScene(self.game))
                    continue
                if self.mode != "2p":
                    who = self._active()
                    if e.key in (pygame.K_a, pygame.K_LEFT):
                        self._move(who, -1)
                    elif e.key in (pygame.K_d, pygame.K_RIGHT):
                        self._move(who, 1)
                    elif e.key in CONFIRM_KEYS + (pygame.K_j,):
                        self._confirm(who)
                    elif e.key == pygame.K_r and (who == 1 or self.mode == "cpu") and not self.wait[who]:
                        self.cur[who] = random.randrange(len(ORDER))
                        self._confirm(who)
                elif self.mode == "2p":
                    if e.key == pygame.K_a:
                        self._move(0, -1)
                    elif e.key == pygame.K_d:
                        self._move(0, 1)
                    elif e.key in (pygame.K_j, pygame.K_SPACE):
                        self._confirm(0)
                    elif e.key == pygame.K_LEFT:
                        self._move(1, -1)
                    elif e.key == pygame.K_RIGHT:
                        self._move(1, 1)
                    elif e.key in KEYMAP_P2["punch"] or e.key in (pygame.K_KP_ENTER,):
                        self._confirm(1)
                    elif e.key == pygame.K_RETURN:
                        if not self.locked[0]:
                            self._confirm(0)
                            if self.locked[0]:
                                self.wait[1] = self.GUARD  # o mesmo Enter não confirma os dois
                        else:
                            self._confirm(1)
            elif e.type == pygame.JOYHATMOTION or e.type == pygame.JOYBUTTONDOWN:
                joys = self.game.joysticks
                idx = next((i for i, j in enumerate(joys) if j.get_instance_id() == e.instance_id), None)
                if idx is None:
                    continue
                who = idx if self.mode == "2p" else self._active()
                if e.type == pygame.JOYHATMOTION and e.value[0]:
                    self._move(who, e.value[0])
                elif e.type == pygame.JOYBUTTONDOWN and e.button in (0, 2):
                    self._confirm(who)

    def update(self):
        super().update()
        self.wait = [max(0, w - 1) for w in self.wait]
        if all(self.locked):
            self.done_t += 1
            if self.done_t > 45:
                p1, p2 = ORDER[self.cur[0]], ORDER[self.cur[1]]
                self.game.change(VSScene(self.game, p1, p2, self.mode))

    def draw(self, surf):
        surf.fill((18, 14, 40))
        for i in range(0, GAME_W, 32):
            pygame.draw.line(surf, (28, 22, 60), (i + (self.t // 2) % 32, 0), (i - 120 + (self.t // 2) % 32, GAME_H),
                             12)
        title = gfx.gradient_text("ESCOLHA SEU POLÍTICO", 34, (255, 255, 200), (255, 160, 30), ow=2)
        surf.blit(title, title.get_rect(midtop=(GAME_W // 2, 8)))
        x0 = (GAME_W - (3 * self.CARD_W + 2 * 26)) // 2
        for i, cid in enumerate(ORDER):
            r = pygame.Rect(x0 + i * (self.CARD_W + 26), 48, self.CARD_W, self.CARD_H)
            pygame.draw.rect(surf, (40, 34, 80), r, border_radius=6)
            sel_by = [w for w in (0, 1) if self.cur[w] == i]
            expr = "happy" if any(self.locked[w] for w in sel_by) else "normal"
            p = art.portrait(self.styles[cid], 3, expr)
            surf.blit(p, p.get_rect(midtop=(r.centerx, r.top + 6)))
            gfx.draw_text(surf, CHARACTERS[cid]["name"], 20, (r.centerx, r.bottom - 42), (255, 230, 80), "midtop")
            gfx.draw_text(surf, CHARACTERS[cid]["nick"], 13, (r.centerx, r.bottom - 20), (210, 210, 230), "midtop")
            for w in sel_by:
                blink = self.locked[w] or (self.t // 8) % 2
                col = (60, 140, 255) if w == 0 else (255, 60, 70)
                if blink:
                    pygame.draw.rect(surf, col, r.inflate(4 + w * 6, 4 + w * 6), 3, border_radius=8)
                tag = "1P" if w == 0 else ("CPU" if self.mode != "2p" else "2P")
                if self.mode == "cpu":
                    tag = f"CPU {w + 1}"
                gfx.draw_text(surf, tag, 16, (r.left + 4, r.top + 4) if w == 0 else (r.right - 4, r.top + 4),
                              (255, 255, 255), "topleft" if w == 0 else "topright", outline=col, ow=2)
        for w in (0, 1):
            self._info(surf, ORDER[self.cur[w]], w)
        if self.mode == "1p":
            msg = "Escolha seu lutador" if not self.locked[0] else "Agora escolha o adversário (R = aleatório)"
        elif self.mode == "2p":
            msg = "P1: A/D + J   •   P2: setas + vírgula (ou Num1)   •   Enter confirma"
        else:
            msg = ("Escolha a CPU 1" if not self.locked[0] else "Agora escolha a CPU 2") + " (R = aleatório)"
        gfx.draw_text(surf, msg, 15, (GAME_W // 2, GAME_H - 18), (255, 255, 255), "midtop")

    def _info(self, surf, cid, w):
        data = CHARACTERS[cid]
        r = pygame.Rect(8 if w == 0 else GAME_W // 2 + 4, 214, GAME_W // 2 - 12, 126)
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        s.fill((0, 0, 0, 120))
        surf.blit(s, r)
        pygame.draw.rect(surf, (60, 140, 255) if w == 0 else (255, 60, 70), r, 1)
        gfx.draw_text(surf, data["full"], 15, (r.left + 6, r.top + 4), (255, 255, 255))
        human = self.mode == "2p" or (self.mode == "1p" and w == 0)
        keys = (["L", "U", "I"] if w == 0 else ["/", ";", "'"]) if human else ["", "", ""]
        for i, slot in enumerate(("s1", "s2", "s3")):
            sp = data["specials"][slot]
            y = r.top + 24 + i * 34
            ic = art.item(sp["item"])
            if ic.get_height() > 28:
                ic = pygame.transform.scale(ic, (ic.get_width() * 28 // ic.get_height(), 28))
            surf.blit(ic, ic.get_rect(center=(r.left + 20, y + 13)))
            label = sp["nome"].upper() + ("  [SUPER]" if sp.get("super") else "")
            k = f" ({keys[i]})" if keys[i] else ""
            gfx.draw_text(surf, label + k, 15, (r.left + 40, y), (255, 220, 80) if sp.get("super") else (140, 230, 140))
            gfx.draw_text(surf, sp["desc"], 13, (r.left + 40, y + 15), (220, 220, 230), outline=None)


# --------------------------------------------------------------------- VS ---

class VSScene(Scene):
    def __init__(self, game, p1, p2, mode):
        super().__init__(game)
        self.p1, self.p2, self.mode = p1, p2, mode
        self.stage = game.next_stage()
        self.s1 = style_for(p1)
        self.s2 = style_for(p2, alt=(p1 == p2))
        self.name2_at = 70  # quando o locutor chama o 2º nome (espera o 1º terminar)
        self.end_at = 190
        audio.sfx("round")

    def handle(self, events):
        for e in events:
            if (e.type == pygame.KEYDOWN and e.key in CONFIRM_KEYS + (pygame.K_j, pygame.K_ESCAPE)) or \
                    e.type == pygame.JOYBUTTONDOWN:
                self.start()

    def start(self):
        self.game.change(FightScene(self.game, self.p1, self.p2, self.mode, self.stage))

    def update(self):
        super().update()
        if self.t == 20:
            v = CHARACTERS[self.p1]["voice"]
            length = audio.voice(self.p1, "nome", CHARACTERS[self.p1]["name"].title() + "!", v["pitch"], v["rasp"], 1)
            self.name2_at = 20 + max(50, int(length * 60) + 8)
        if self.t == self.name2_at:
            v = CHARACTERS[self.p2]["voice"]
            length = audio.voice(self.p2, "nome", CHARACTERS[self.p2]["name"].title() + "!", v["pitch"], v["rasp"], 2)
            self.end_at = max(190, self.t + int(length * 60) + 30)
        if self.t > self.end_at:
            self.start()

    def draw(self, surf):
        self.stage.draw(surf)
        _dark(surf, 170, (10, 0, 20))
        k = min(1.0, self.t / 25)
        ease = 1 - (1 - k) ** 3
        p1 = art.portrait(self.s1, 4, "shout" if 20 < self.t < 50 else "normal")
        p2 = pygame.transform.flip(art.portrait(self.s2, 4, "shout" if 70 < self.t < 100 else "normal"), True, False)
        surf.blit(p1, p1.get_rect(midbottom=(int(-100 + 250 * ease), 290)))
        surf.blit(p2, p2.get_rect(midbottom=(int(GAME_W + 100 - 250 * ease), 290)))
        for i, (cid, x) in enumerate(((self.p1, 150), (self.p2, GAME_W - 150))):
            if self.t > 20 + i * 50:
                gfx.draw_text(surf, CHARACTERS[cid]["name"], 30, (x, 296), (255, 230, 70), "midtop", ow=2)
                gfx.draw_text(surf, CHARACTERS[cid]["nick"], 16, (x, 324), (230, 230, 240), "midtop")
        if self.t > 30:
            scale = 1 + max(0, (45 - self.t) / 15)
            vs = gfx.gradient_text("VS", int(72 * scale), (255, 255, 180), (230, 40, 40), ow=3)
            surf.blit(vs, vs.get_rect(center=(GAME_W // 2, 170)))
        # faixa estilo "vídeo de meme"
        for i, txt in enumerate((CHARACTERS[self.p1]["meme"], "vs", CHARACTERS[self.p2]["meme"])):
            s = gfx.text_surface(txt, 20, (10, 10, 10), outline=None)
            r = s.get_rect(midtop=(GAME_W // 2, 10 + i * 22))
            pygame.draw.rect(surf, (255, 255, 255), r.inflate(10, 4), border_radius=4)
            surf.blit(s, r)
        gfx.draw_text(surf, f"Cenário: {self.stage.name}", 14, (GAME_W // 2, GAME_H - 18), (220, 220, 230), "midtop")


# ------------------------------------------------------------------- luta ---

class FightScene(Scene):
    def __init__(self, game, p1, p2, mode, stage):
        super().__init__(game)
        self.p1_id, self.p2_id, self.mode = p1, p2, mode
        self.stage = stage
        self.fighters = [Fighter(p1, 0), Fighter(p2, 1, alt=(p1 == p2))]
        joys = game.joysticks
        j1 = joys[0] if joys else None
        j2 = joys[1] if len(joys) > 1 else None
        if mode == "cpu":
            self.ctrl = [AIController(game.difficulty), AIController(game.difficulty)]
        elif mode == "2p":
            self.ctrl = [HumanController(KEYMAP_P1, j1), HumanController(KEYMAP_P2, j2)]
        else:
            self.ctrl = [HumanController(KEYMAP_P1, j1), AIController(game.difficulty)]
        self.hud = HUD()
        self.fx = FX()
        self.projectiles = []
        self.zones = []
        self.round = 1
        self.hitstop = 0
        self.shake = 0
        self.freeze = 0
        self.freeze_info = None
        self.slowmo = 0
        self.excite = 0.0
        self.paused = False
        self.pause_sel = 0
        self.winner = None
        self.match_winner = None
        self.end_quote = None
        self.start_round(first=True)

    # ---------------------------------------------------------- rounds ---
    def start_round(self, first=False):
        a, b = self.fighters
        a.reset(200, 1)
        b.reset(GAME_W - 200, -1)
        self.projectiles.clear()
        self.zones.clear()
        self.fx.clear()
        self.timer = ROUND_TIME * 60
        self.winner = None
        self.phase = "intro" if first else "call"
        self.phase_t = 0
        self.fight_at = 70
        self.next_at = 0
        self.intro_step = 0
        self.quote_end = 0
        if first:
            a.set_state("intro")
            b.set_state("intro")

    def opponent(self, f):
        return self.fighters[1] if f is self.fighters[0] else self.fighters[0]

    def super_flash(self, f, sp):
        self.freeze = 46
        self.freeze_info = (f, sp)

    def on_ko(self, loser, attacker):
        if self.phase != "fight":
            return
        self.phase = "ko"
        self.phase_t = 0
        self.slowmo = 75
        self.shake = 10
        a, b = self.fighters
        if a.hp <= 0 and b.hp <= 0:
            self.winner = None
        else:
            self.winner = self.opponent(loser)
        audio.sfx("ko")

    # -------------------------------------------------------- eventos ---
    def handle(self, events):
        for e in events:
            for c in self.ctrl:
                c.handle_event(e)
            if e.type != pygame.KEYDOWN:
                continue
            if self.paused:
                self._pause_key(e.key)
            elif self.phase == "end":
                if e.key in CONFIRM_KEYS:
                    self.game.change(VSScene(self.game, self.p1_id, self.p2_id, self.mode))
                elif e.key == pygame.K_s:
                    self.game.change(SelectScene(self.game, self.mode))
                elif e.key == pygame.K_ESCAPE:
                    self.game.change(TitleScene(self.game))
            elif e.key in (pygame.K_ESCAPE, pygame.K_p):
                self.paused = True
                self.pause_sel = 0
                audio.sfx("select")
            elif self.phase == "intro" and e.key in CONFIRM_KEYS:
                self._begin_call()

    def _pause_key(self, key):
        opts = 3
        if key in (pygame.K_UP, pygame.K_w):
            self.pause_sel = (self.pause_sel - 1) % opts
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.pause_sel = (self.pause_sel + 1) % opts
        elif key in (pygame.K_ESCAPE, pygame.K_p):
            self.paused = False
        elif key in CONFIRM_KEYS + (pygame.K_j,):
            if self.pause_sel == 0:
                self.paused = False
            elif self.pause_sel == 1:
                self.game.change(SelectScene(self.game, self.mode))
            else:
                self.game.change(TitleScene(self.game))

    def _begin_call(self):
        self.phase = "call"
        self.phase_t = 0
        for f in self.fighters:
            if f.state == "intro":
                f.set_state("idle")
            f.bubble_t = 0

    # ---------------------------------------------------------- update ---
    def update(self):
        if self.paused:
            return
        self.t += 1
        self.stage.update()
        self.fx.update()
        self.excite = max(0.0, self.excite - 0.004)
        if self.shake > 0:
            self.shake -= 0.5
        if self.freeze > 0:
            self.freeze -= 1
            return
        if self.hitstop > 0:
            self.hitstop -= 1
            return
        if self.slowmo > 0:
            self.slowmo -= 1
            if self.slowmo % 3:
                return
        self.phase_t += 1
        self._phase_logic()

        active = self.phase in ("fight", "ko")
        a, b = self.fighters
        for i, f in enumerate(self.fighters):
            opp = self.opponent(f)
            inp = self.ctrl[i].read(f, opp, self) if self.phase == "fight" else NEUTRAL
            f.update(inp, opp, self)
        self._push_apart(a, b)

        if active:
            for p in self.projectiles:
                p.update(self)
            self._projectile_clash()
            for p in self.projectiles:
                if p.alive:
                    p.check_hit(self, self.opponent(p.owner))
            self.projectiles = [p for p in self.projectiles if p.alive]
            for z in self.zones:
                z.update(self)
            self.zones = [z for z in self.zones if z.alive]
            if self.phase == "fight":
                self._melee(a, b)
                self._melee(b, a)

        if self.phase == "fight":
            self.timer -= 1
            if self.timer <= 0:
                self._time_up()

    def _phase_logic(self):
        a, b = self.fighters
        pt = self.phase_t
        if self.phase == "intro":
            # um fala, depois o outro (esperando o áudio real terminar), depois começa o round
            if pt == 15:
                self.next_at = 15 + max(80, a.say(a.data["intro"]["id"], a.data["intro"]["fala"]) + 12)
                self.intro_step = 1
            elif self.intro_step == 1 and pt >= self.next_at:
                self.next_at = pt + max(90, b.say(b.data["intro"]["id"], b.data["intro"]["fala"]) + 20)
                self.intro_step = 2
            elif self.intro_step == 2 and pt >= self.next_at:
                self._begin_call()
        elif self.phase == "call":
            if pt == 1:
                # locutor por round (assets/sons/round1, round2, round3) ou o som sintetizado
                length = audio.sfx(f"round{self.round}", 1.0, fallback="round")
                self.fight_at = max(70, int(length * 60) + 6)
            if pt == self.fight_at:
                audio.sfx("fight", 1.0)
            if pt >= self.fight_at + 40:
                self.phase = "fight"
                self.phase_t = 0
        elif self.phase == "ko":
            loser_down = all(f.state != "air_hit" for f in self.fighters)
            if pt > 70 and loser_down and self.winner is not None and self.winner.state != "win":
                if self.winner.state in FREE or self.winner.state in ("block", "hit"):
                    self.winner.set_state("win")
                    line = random_win_line(self.winner)
                    self.quote_end = pt + self.winner.say(line["id"], line["fala"])
                    self.round_quote = line
                    self.excite = 1.0
                    audio.sfx("vitoria", 0.6)
            if pt > max(230, self.quote_end + 30) or (self.winner is None and pt > 120):
                self._award()
        elif self.phase == "timeup":
            if pt == 100 and self.winner is not None:
                self.winner.set_state("win")
                line = random_win_line(self.winner)
                self.quote_end = pt + self.winner.say(line["id"], line["fala"])
            if pt > max(240, self.quote_end + 30):
                self._award()

    def _time_up(self):
        a, b = self.fighters
        self.phase = "timeup"
        self.phase_t = 0
        if abs(a.hp - b.hp) < 0.5:
            self.winner = None
        else:
            self.winner = a if a.hp > b.hp else b
        audio.sfx("ko", 0.6)

    def _award(self):
        a, b = self.fighters
        if self.winner is None:
            a.round_wins += 1
            b.round_wins += 1
        else:
            self.winner.round_wins += 1
        if a.round_wins >= ROUNDS_TO_WIN or b.round_wins >= ROUNDS_TO_WIN:
            self.phase = "end"
            self.phase_t = 0
            if a.round_wins >= ROUNDS_TO_WIN and b.round_wins >= ROUNDS_TO_WIN:
                self.match_winner = None
            else:
                self.match_winner = a if a.round_wins >= ROUNDS_TO_WIN else b
            if self.match_winner:
                self.end_quote = random_win_line(self.match_winner)
                self.match_winner.say(self.end_quote["id"], self.end_quote["fala"])
                self.match_winner.bubble_t = 0
            audio.sfx("vitoria")
            return
        self.round += 1
        self.start_round()

    # ---------------------------------------------------------- colisão ---
    def _push_apart(self, a, b):
        if a.state in ("down", "ko") or b.state in ("down", "ko"):
            return
        if abs(a.y - b.y) > 70:
            return
        dx = b.x - a.x
        min_d = 34
        if abs(dx) < min_d:
            push = (min_d - abs(dx)) / 2
            sign = 1 if dx > 0 else -1 if dx < 0 else (1 if a.facing == 1 else -1)
            a.x -= push * sign
            b.x += push * sign
            for f in (a, b):
                f.x = max(STAGE_LEFT, min(STAGE_RIGHT, f.x))
            if abs(b.x - a.x) < min_d - 1:  # preso na parede
                if a.x <= STAGE_LEFT + 1 or b.x <= STAGE_LEFT + 1:
                    (b if b.x > a.x else a).x = STAGE_LEFT + min_d
                elif a.x >= STAGE_RIGHT - 1 or b.x >= STAGE_RIGHT - 1:
                    (b if b.x < a.x else a).x = STAGE_RIGHT - min_d

    def _melee(self, att, dfn):
        box = att.attack_box()
        if not box:
            return
        hb = dfn.hurtbox()
        if hb and box.colliderect(hb):
            att.attack_hit = True
            clip = box.clip(hb)
            res = dfn.take_hit(att.make_hit_info(), att, self, at=clip.center)
            if res == "hit":
                self.excite = min(1.0, self.excite + 0.25)

    def _projectile_clash(self):
        ps = [p for p in self.projectiles if p.alive and p.clash]
        for i, p in enumerate(ps):
            for q in ps[i + 1:]:
                if p.owner is not q.owner and p.alive and q.alive and p.rect().colliderect(q.rect()):
                    p.destroy(self)
                    q.destroy(self)
                    audio.sfx("bloqueio")

    # ----------------------------------------------------------- desenho ---
    def draw(self, surf):
        sh = int(self.shake)
        off = (random.randint(-sh, sh), random.randint(-sh, sh)) if sh > 0 else (0, 0)
        self.stage.draw(surf, off, self.excite)
        for z in self.zones:
            z.draw(surf, off)
        order = sorted(self.fighters, key=lambda f: 1 if f.state in ("attack", "special") else 0)
        for f in order:
            f.draw(surf, off)
        for p in self.projectiles:
            p.draw(surf, off)
        self.fx.draw(surf, off)

        if self.freeze > 0 and self.freeze_info:
            self._draw_super(surf, off)

        r0 = self.fighters[0].draw_bubble(surf, off)
        self.fighters[1].draw_bubble(surf, off, avoid=r0)
        self.hud.draw(surf, self.fighters, (self.timer + 59) // 60, ROUNDS_TO_WIN)
        for i, f in enumerate(self.fighters):
            self.hud.combo(surf, f, i)
        self._draw_banners(surf)
        if self.paused:
            self._draw_pause(surf)

    def _draw_super(self, surf, off):
        f, sp = self.freeze_info
        _dark(surf, 150, (20, 0, 40))
        f.draw(surf, off)
        k = 1 - self.freeze / 46
        band_y = 120
        band = pygame.Surface((GAME_W, 74), pygame.SRCALPHA)
        band.fill((120, 30, 160, 200))
        for i in range(0, GAME_W, 16):
            pygame.draw.line(band, (170, 70, 210, 200), (i, 0), (i - 20, 74), 3)
        slide = int((1 - min(1, k * 4)) * GAME_W) * (-1 if f.player == 0 else 1)
        surf.blit(band, (slide, band_y))
        big = gfx.gradient_text(sp["fala"].upper(), 40, (255, 255, 220), (255, 120, 40), ow=3)
        surf.blit(big, big.get_rect(center=(GAME_W // 2 + slide, band_y + 30)))
        gfx.draw_text(surf, f"SUPER  {sp['nome'].upper()}", 16, (GAME_W // 2 + slide, band_y + 54),
                      (255, 230, 255), "midtop")
        ic = art.item(sp["item"])
        ic = pygame.transform.scale(ic, (ic.get_width() * 2, ic.get_height() * 2)) if ic.get_width() < 40 else ic
        x = 60 if f.player == 0 else GAME_W - 60
        surf.blit(ic, ic.get_rect(center=(x + slide, band_y + 37)))

    def _banner(self, surf, text, size=64, top=(255, 250, 160), bottom=(255, 110, 20), y=150):
        s = gfx.gradient_text(text, size, top, bottom, ow=3)
        surf.blit(s, s.get_rect(center=(GAME_W // 2, y)))

    def _draw_banners(self, surf):
        pt = self.phase_t
        if self.phase == "call":
            if pt < self.fight_at:
                self._banner(surf, f"ROUND {self.round}", 56)
            else:
                scale = 1 + max(0, (self.fight_at + 10 - pt) / 10) * 0.4
                self._banner(surf, "FIGHT!", int(74 * scale), (255, 255, 140), (240, 140, 0))
        elif self.phase == "ko":
            if pt < 160:
                self._banner(surf, "K.O.", 90, (255, 245, 120), (220, 40, 30))
            if self.winner is None and pt > 40:
                self._banner(surf, "DUPLO K.O.!", 36, y=210)
        elif self.phase == "timeup":
            self._banner(surf, "TEMPO!", 70)
            if pt > 60:
                txt = "EMPATE!" if self.winner is None else f"{self.winner.data['name']} VENCE O ROUND"
                self._banner(surf, txt, 30, y=210)
        elif self.phase == "end":
            self._draw_end(surf)

    def _draw_end(self, surf):
        _dark(surf, min(170, self.phase_t * 4), (10, 0, 25))
        w = self.match_winner
        if w is None:
            self._banner(surf, "EMPATE TÉCNICO!", 48, y=110)
        else:
            p = art.portrait(w.style, 4, "happy")
            if w.player == 1:
                p = pygame.transform.flip(p, True, False)
            surf.blit(p, p.get_rect(midbottom=(GAME_W // 2, 210)))
            self._banner(surf, f"{w.data['name']} VENCEU!", 46, y=46)
            if self.mode == "1p":
                sub = "VOCÊ VENCEU!" if w.player == 0 else "VOCÊ PERDEU!"
                gfx.draw_text(surf, sub, 20, (GAME_W // 2, 72), (255, 255, 255), "midtop", ow=2)
            if self.end_quote:
                txt = gfx.text_surface(f"“{self.end_quote['fala']}”", 20, (20, 20, 30), outline=None)
                r = txt.get_rect(midtop=(GAME_W // 2, 222))
                pygame.draw.rect(surf, (255, 255, 255), r.inflate(16, 10), border_radius=8)
                surf.blit(txt, r)
        if self.phase_t > 40:
            gfx.draw_text(surf, "ENTER revanche   •   S trocar personagens   •   ESC menu", 15,
                          (GAME_W // 2, GAME_H - 40), (255, 230, 80), "midtop", ow=2)

    def _draw_pause(self, surf):
        _dark(surf, 170)
        self._banner(surf, "PAUSA", 56, y=50)
        for i, opt in enumerate(("CONTINUAR", "TROCAR PERSONAGENS", "MENU PRINCIPAL")):
            col = (255, 230, 60) if i == self.pause_sel else (220, 220, 230)
            gfx.draw_text(surf, opt, 22, (GAME_W // 2, 92 + i * 24), col, "midtop", ow=2)
        lines = [
            "P1: WASD mover/pular/agachar • J soco • K chute • L / U especiais • I super",
            "P2: setas • , soco • . chute • / e ; especiais • ' super (ou Num 1-5)",
            "Segure para TRÁS para defender (agachado defende golpes baixos)",
            "A barra roxa enche batendo e apanhando — cheia libera o SUPER",
        ]
        for i, ln in enumerate(lines):
            gfx.draw_text(surf, ln, 14, (GAME_W // 2, 180 + i * 21), (230, 230, 240), "midtop")
        if self.stage.credit:
            gfx.draw_text(surf, self.stage.credit, 12, (GAME_W // 2, GAME_H - 16), (170, 170, 180), "midtop")

