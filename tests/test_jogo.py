"""Testes automatizados do Brasília Fight.

Rodam o jogo sem janela e sem som (drivers "dummy" do SDL), enviando eventos de teclado e
conferindo o estado: controles, colisões, limites da arena, regras, pausa, reinício,
encerramento, recursos e desempenho.

Uso (na raiz do projeto):  python -m unittest discover -s tests -v
"""
import os
import random
import sys
import time
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from brfight import gfx  # noqa: E402
from brfight.characters import CHARACTERS, ORDER  # noqa: E402
from brfight.config import ASSETS, FLOOR_Y, KEYMAP_P1, METER_MAX, STAGE_LEFT, STAGE_RIGHT  # noqa: E402
from brfight.controls import HumanController, InputState  # noqa: E402
from brfight.game import Game  # noqa: E402
from brfight.projectiles import Straight  # noqa: E402
from brfight.scenes import FightScene, SelectScene, TitleScene, VSScene  # noqa: E402

FRAME_BUDGET_MS = 1000 / 60  # 16,7 ms por quadro a 60 FPS
_game = None


def game():
    """Uma única instância do jogo para todos os testes (pygame.init só uma vez)."""
    global _game
    if _game is None:
        _game = Game()
    _game.running = True
    return _game


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def new_fight(p1="bolsonaro", p2="lula", mode="2p", seed=1):
    """Cria uma luta e avança até a fase "fight" (depois da introdução e do "FIGHT!")."""
    g = game()
    random.seed(seed)
    sc = FightScene(g, p1, p2, mode, g.stages[0])
    for i, c in enumerate(sc.ctrl):
        if hasattr(c, "rng"):
            c.rng.seed(seed + i)
    sc.fx.rng.seed(seed)
    g.change(sc)
    while sc.phase != "fight":
        g.step([])
    return sc


def face_each_other(sc, xa=300, xb=340):
    a, b = sc.fighters
    a.x, b.x = xa, xb
    a.facing, b.facing = 1, -1
    return a, b


def run_attack(sc, att, dfn, name="punch"):
    """Executa os quadros de preparação e ativos de um golpe, testando a colisão a cada quadro."""
    att.start_attack(name)
    for _ in range(att.attack["startup"] + att.attack["active"]):
        att.t += 1
        sc._melee(att, dfn)


class TestEncerramentoEMenu(unittest.TestCase):
    def test_fechar_janela_encerra_o_laco(self):
        g = game()
        g.step([pygame.event.Event(pygame.QUIT)])
        self.assertFalse(g.running)

    def test_opcao_sair_do_menu_encerra(self):
        g = game()
        t = TitleScene(g)
        g.change(t)
        t.sel = len(t.options) - 1  # SAIR
        g.step([key(pygame.K_RETURN)])
        self.assertFalse(g.running)

    def test_menu_navega_e_abre_selecao(self):
        g = game()
        g.change(TitleScene(g))
        g.step([key(pygame.K_DOWN)])
        g.step([key(pygame.K_UP)])
        g.step([key(pygame.K_RETURN)])  # 1 JOGADOR
        self.assertIsInstance(g.scene, SelectScene)
        self.assertEqual(g.scene.mode, "1p")

    def test_dificuldade_muda_com_setas(self):
        g = game()
        t = TitleScene(g)
        g.change(t)
        t.sel = 3
        antes = g.difficulty
        g.step([key(pygame.K_RIGHT)])
        self.assertEqual(g.difficulty, (antes + 1) % 3)
        g.step([key(pygame.K_LEFT)])
        self.assertEqual(g.difficulty, antes)


class TestControles(unittest.TestCase):
    def test_tecla_j_gera_soco(self):
        c = HumanController(KEYMAP_P1)
        c.handle_event(key(pygame.K_j))
        self.assertIn("punch", c.read().pressed)

    def test_comando_e_consumido_uma_vez(self):
        c = HumanController(KEYMAP_P1)
        c.handle_event(key(pygame.K_k))
        self.assertIn("kick", c.read().pressed)
        self.assertNotIn("kick", c.read().pressed)

    def test_selecao_ignora_enter_repetido(self):
        """Um Enter repetido ao abrir a tela não pode confirmar o lutador (correção do PR #3)."""
        g = game()
        sel = SelectScene(g, "1p")
        g.change(sel)
        g.step([key(pygame.K_RETURN)])
        self.assertFalse(sel.locked[0])

    def test_selecao_cpu_x_cpu_escolhe_os_dois(self):
        g = game()
        sel = SelectScene(g, "cpu")
        g.change(sel)
        for _ in range(SelectScene.GUARD + 1):
            g.step([])
        g.step([key(pygame.K_RETURN)])
        self.assertEqual(sel.locked, [True, False])
        for _ in range(SelectScene.GUARD + 1):
            g.step([])
        g.step([key(pygame.K_RIGHT), key(pygame.K_RETURN)])
        self.assertEqual(sel.locked, [True, True])


class TestColisoes(unittest.TestCase):
    def test_soco_no_alcance_acerta(self):
        sc = new_fight()
        a, b = face_each_other(sc, 300, 340)
        run_attack(sc, a, b)
        self.assertLess(b.hp, 100)

    def test_soco_fora_do_alcance_erra(self):
        sc = new_fight()
        a, b = face_each_other(sc, 300, 380)
        run_attack(sc, a, b)
        self.assertEqual(b.hp, 100)

    def test_golpe_acerta_uma_vez_so(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        run_attack(sc, a, b)
        hp = b.hp
        for _ in range(5):  # quadros ativos restantes não podem acertar de novo
            a.t += 1
            sc._melee(a, b)
        self.assertEqual(b.hp, hp)

    def test_caixa_de_ataque_espelha_com_a_direcao(self):
        sc = new_fight()
        a, _ = sc.fighters
        a.x, a.facing = 300, 1
        a.start_attack("punch")
        a.t = a.attack["startup"]
        direita = a.attack_box()
        a.facing = -1
        esquerda = a.attack_box()
        self.assertGreater(direita.left, a.x)
        self.assertLess(esquerda.right, a.x)

    def test_defesa_segurando_para_tras(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        b.holding_back = True
        run_attack(sc, a, b)
        self.assertEqual(b.state, "block")
        self.assertEqual(b.hp, 100)

    def test_rasteira_passa_pela_defesa_em_pe(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        b.holding_back, b.holding_down = True, False
        run_attack(sc, a, b, "c_kick")
        self.assertLess(b.hp, 100)

    def test_cloroquina_passa_por_cima_de_quem_agacha(self):
        sc = new_fight()
        a, b = sc.fighters
        sp = CHARACTERS["bolsonaro"]["specials"]["s1"]
        b.x = 400
        p = Straight(a, sp, 400, FLOOR_Y + sp["y"], 0)
        b.set_state("crouch")
        self.assertFalse(b.hurtbox().colliderect(p.rect()))
        b.set_state("idle")
        self.assertTrue(b.hurtbox().colliderect(p.rect()))

    def test_projeteis_opostos_se_anulam(self):
        sc = new_fight()
        a, b = sc.fighters
        p1 = Straight(a, CHARACTERS["bolsonaro"]["specials"]["s1"], 300, 260, 0)
        p2 = Straight(b, CHARACTERS["lula"]["specials"]["s1"], 305, 262, 0)
        sc.projectiles = [p1, p2]
        sc._projectile_clash()
        self.assertFalse(p1.alive or p2.alive)

    def test_lutadores_nao_se_atravessam(self):
        sc = new_fight()
        a, b = face_each_other(sc, 300, 310)
        sc._push_apart(a, b)
        self.assertGreaterEqual(abs(b.x - a.x), 33)

    def test_lutadores_presos_na_parede_se_separam(self):
        sc = new_fight()
        a, b = face_each_other(sc, STAGE_LEFT, STAGE_LEFT + 5)
        sc._push_apart(a, b)
        self.assertGreaterEqual(abs(b.x - a.x), 33)
        self.assertGreaterEqual(min(a.x, b.x), STAGE_LEFT)

    def test_caido_nao_pode_ser_atingido(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        b.set_state("down")
        self.assertIsNone(b.hurtbox())
        run_attack(sc, a, b)
        self.assertEqual(b.hp, 100)


class TestLimites(unittest.TestCase):
    def _empurra_contra_parede(self, esquerda):
        sc = new_fight()
        a, b = sc.fighters
        b.x = STAGE_RIGHT if esquerda else STAGE_LEFT
        inp = InputState()
        for i in range(400):
            inp.left, inp.right = esquerda, not esquerda
            inp.up = i % 40 == 0  # pula de vez em quando
            a.update(inp, b, sc)
            self.assertTrue(STAGE_LEFT <= a.x <= STAGE_RIGHT, f"x={a.x}")
        return a

    def test_parede_esquerda(self):
        self.assertEqual(self._empurra_contra_parede(True).x, STAGE_LEFT)

    def test_parede_direita(self):
        self.assertEqual(self._empurra_contra_parede(False).x, STAGE_RIGHT)

    def test_pulo_volta_ao_chao(self):
        sc = new_fight()
        a, b = sc.fighters
        inp = InputState()
        inp.up = True
        a.update(inp, b, sc)
        inp.up = False
        alturas = []
        for _ in range(80):
            a.update(inp, b, sc)
            alturas.append(a.y)
        self.assertLess(min(alturas), FLOOR_Y - 80)  # subiu
        self.assertEqual(a.y, FLOOR_Y)                # e voltou ao chão
        self.assertEqual(a.state, "idle")


class TestRegras(unittest.TestCase):
    def test_tempo_esgotado_vence_quem_tem_mais_vida(self):
        sc = new_fight(mode="cpu")
        a, b = sc.fighters
        a.hp, b.hp = 60, 40
        sc.timer = 1
        game().step([])
        self.assertEqual(sc.phase, "timeup")
        self.assertIs(sc.winner, a)

    def test_tempo_esgotado_com_vida_igual_empata(self):
        sc = new_fight(mode="cpu")
        a, b = sc.fighters
        a.hp = b.hp = 50
        sc.timer = 1
        game().step([])
        self.assertIsNone(sc.winner)

    def test_vida_zerada_e_nocaute(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        b.hp = 1
        run_attack(sc, a, b)
        self.assertEqual(sc.phase, "ko")
        self.assertIs(sc.winner, a)

    def test_melhor_de_3(self):
        sc = new_fight()
        a, _ = sc.fighters
        sc.winner = a
        sc._award()
        self.assertEqual((sc.round, sc.phase), (2, "call"))
        sc.winner = a
        sc._award()
        self.assertEqual(sc.phase, "end")
        self.assertIs(sc.match_winner, a)

    def test_combo_reduz_o_dano(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        a.start_attack("punch")
        info = a.make_hit_info()
        b.take_hit(info, a, sc)
        d1 = 100 - b.hp
        hp = b.hp
        b.take_hit(info, a, sc)  # segundo golpe com o rival ainda atordoado
        d2 = hp - b.hp
        self.assertEqual(a.combo, 2)
        self.assertAlmostEqual(d2, d1 * 0.88, places=5)

    def test_super_exige_barra_cheia(self):
        sc = new_fight()
        a, _ = sc.fighters
        a.meter = METER_MAX - 1
        self.assertFalse(a.can_special("s3", sc)[0])
        a.meter = METER_MAX
        self.assertTrue(a.can_special("s3", sc)[0])

    def test_censurado_nao_usa_especiais(self):
        sc = new_fight()
        a, _ = sc.fighters
        a.status["silenced"] = 100
        self.assertFalse(a.can_special("s1", sc)[0])

    def test_bebado_inverte_os_controles(self):
        sc = new_fight()
        a, b = face_each_other(sc)
        a.status["drunk"] = 100
        inp = InputState()
        inp.right = True  # para a frente...
        a.update(inp, b, sc)
        self.assertLess(a.vx, 0)  # ...mas anda para trás


class TestPausaEReinicio(unittest.TestCase):
    def test_esc_pausa_e_congela_a_partida(self):
        g = game()
        sc = new_fight(mode="cpu")
        g.step([key(pygame.K_ESCAPE)])
        timer, vidas = sc.timer, [f.hp for f in sc.fighters]
        for _ in range(300):
            g.step([])
        self.assertTrue(sc.paused)
        self.assertEqual(sc.timer, timer)
        self.assertEqual([f.hp for f in sc.fighters], vidas)

    def test_esc_retoma_a_partida(self):
        g = game()
        sc = new_fight(mode="cpu")
        g.step([key(pygame.K_ESCAPE)])
        timer = sc.timer
        g.step([key(pygame.K_ESCAPE)])
        g.step([])
        self.assertFalse(sc.paused)
        self.assertLess(sc.timer, timer)

    def test_pausa_menu_principal(self):
        g = game()
        sc = new_fight(mode="cpu")
        g.step([key(pygame.K_p)])
        g.step([key(pygame.K_DOWN), key(pygame.K_DOWN), key(pygame.K_RETURN)])
        self.assertIsInstance(g.scene, TitleScene)

    def _fim(self):
        sc = new_fight()
        sc.phase = "end"
        return sc

    def test_fim_enter_revanche(self):
        g = game()
        g.change(self._fim())
        g.step([key(pygame.K_RETURN)])
        self.assertIsInstance(g.scene, VSScene)

    def test_fim_s_troca_personagens(self):
        g = game()
        g.change(self._fim())
        g.step([key(pygame.K_s)])
        self.assertIsInstance(g.scene, SelectScene)

    def test_fim_esc_volta_ao_menu(self):
        g = game()
        g.change(self._fim())
        g.step([key(pygame.K_ESCAPE)])
        self.assertIsInstance(g.scene, TitleScene)


class TestPartidasCompletas(unittest.TestCase):
    """Três partidas CPU x CPU do início ao fim; os resultados são usados por vários testes."""

    @classmethod
    def setUpClass(cls):
        g = game()
        cls.resultados = []
        cls.tempos = []
        cls.fora_da_arena = 0
        for i, (p1, p2) in enumerate((("bolsonaro", "lula"), ("lula", "xandao"), ("xandao", "bolsonaro"))):
            g.difficulty = i
            random.seed(i)
            sc = FightScene(g, p1, p2, "cpu", g.stages[0])
            for j, c in enumerate(sc.ctrl):
                c.rng.seed(10 * i + j)
            g.change(sc)
            for _ in range(60 * 60 * 8):  # no máximo 8 minutos de jogo
                t0 = time.perf_counter()
                g.step([])
                cls.tempos.append((time.perf_counter() - t0) * 1000)
                cls.fora_da_arena += sum(1 for f in sc.fighters if not STAGE_LEFT <= f.x <= STAGE_RIGHT)
                if sc.phase == "end":
                    break
            cls.resultados.append(sc)
        cls.tempos.sort()

    def test_todas_as_partidas_terminam(self):
        self.assertTrue(all(sc.phase == "end" for sc in self.resultados))

    def test_vencedor_tem_2_rounds(self):
        for sc in self.resultados:
            if sc.match_winner is not None:
                self.assertEqual(sc.match_winner.round_wins, 2)

    def test_ninguem_sai_da_arena(self):
        self.assertEqual(self.fora_da_arena, 0)

    def test_desempenho_60_fps(self):
        p99 = self.tempos[int(len(self.tempos) * 0.99)]
        media = sum(self.tempos) / len(self.tempos)
        print(f"\n    {len(self.tempos)} quadros: média {media:.2f} ms, p99 {p99:.2f} ms, "
              f"máx {self.tempos[-1]:.1f} ms (limite {FRAME_BUDGET_MS:.1f} ms)", file=sys.stderr)
        self.assertLess(p99, FRAME_BUDGET_MS)


class TestRecursos(unittest.TestCase):
    def test_cenario_e_fonte_existem(self):
        self.assertTrue(any(p.suffix.lower() in (".jpg", ".png") for p in (ASSETS / "bg").iterdir()))
        self.assertTrue(gfx.UI_FONT.exists())

    def test_todos_os_personagens_tem_dados_completos(self):
        for cid in ORDER:
            data = CHARACTERS[cid]
            self.assertEqual(set(data["specials"]), {"s1", "s2", "s3"})
            self.assertTrue(data["specials"]["s3"].get("super"))
            self.assertEqual(len(data["wins"]), 3)

    def test_codigo_sem_caminhos_absolutos(self):
        for py in list((ROOT / "brfight").glob("*.py")) + [ROOT / "main.py"]:
            texto = py.read_text(encoding="utf-8")
            for proibido in ("/Users/", "/home/", "C:\\"):
                self.assertNotIn(proibido, texto, f"{py.name} contém {proibido}")

    def test_quantizacao_respeita_a_paleta(self):
        rng = random.Random(0)
        s = pygame.Surface((40, 30))
        for x in range(40):
            for y in range(30):
                s.set_at((x, y), (rng.randrange(256), rng.randrange(256), rng.randrange(256)))
        q = gfx.quantize(s, colors=8)
        cores = {tuple(q.get_at((x, y)))[:3] for x in range(40) for y in range(30)}
        self.assertLessEqual(len(cores), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
