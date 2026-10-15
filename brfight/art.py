"""Pixel art procedural: cabeças caricatas, corpo articulado ("boneco") e itens/comidas.

Convenção dos ângulos dos membros (graus): 0 = apontando para baixo, +90 = para frente
(direção em que o lutador olha), 180 = para cima, -90 = para trás.
Todo desenho é feito olhando para a direita; o lutador espelha quando olha para a esquerda.
"""
import math
import random

import pygame

from . import gfx
from .config import ASSETS

CW, CH = 190, 190          # tela de desenho de um lutador
AX, AY = CW // 2, CH - 14  # âncora (centro dos pés) dentro da tela

L_THIGH, L_SHIN = 21, 21
L_UP, L_FORE = 15, 15
L_TORSO = 34
HIP_AIR = 40
OUTLINE = (16, 12, 22)

_head_cache = {}
_item_cache = {}
_face_img_cache = {}


def shade(c, k=0.72):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def _vec(a, length):
    r = math.radians(a)
    return math.sin(r) * length, math.cos(r) * length


def _add(a, b, k=1.0):
    return a[0] + b[0] * k, a[1] + b[1] * k


def _ip(p):
    return int(round(p[0])), int(round(p[1]))


def _limb(s, a, b, w, color):
    a, b = _ip(a), _ip(b)
    pygame.draw.line(s, color, a, b, w)
    r = max(1, w // 2)
    pygame.draw.circle(s, color, a, r)
    pygame.draw.circle(s, color, b, r)


# ------------------------------------------------------------- esqueleto ---

DEFAULT_POSE = {
    "lean": 6, "fa": (35, 95), "ba": (15, 105), "fl": (18, 22), "bl": (-16, 6),
    "head": (0, 0), "expr": "normal", "hold": None, "lift": 0, "dx": 0, "cape": 0,
}


def skeleton(pose, grounded=True):
    p = DEFAULT_POSE.copy()
    p.update(pose)
    fl_h, fl_k = p["fl"]
    bl_h, bl_k = p["bl"]
    knee_f = _vec(fl_h, L_THIGH)
    foot_f = _add(knee_f, _vec(fl_h - fl_k, L_SHIN))
    knee_b = _vec(bl_h, L_THIGH)
    foot_b = _add(knee_b, _vec(bl_h - bl_k, L_SHIN))
    hip_h = max(foot_f[1], foot_b[1]) if grounded else HIP_AIR
    hip = (AX + p["dx"], AY - hip_h - p["lift"])
    lean = math.radians(p["lean"])
    u = (math.sin(lean), -math.cos(lean))
    neck = _add(hip, u, L_TORSO)
    shoulder = _add(hip, u, L_TORSO * 0.86)
    perp = (-u[1], u[0])
    sh_f = _add(shoulder, perp, 3)
    sh_b = _add(shoulder, perp, -3)
    fa_s, fa_e = p["fa"]
    ba_s, ba_e = p["ba"]
    elbow_f = _add(sh_f, _vec(fa_s, L_UP))
    hand_f = _add(elbow_f, _vec(fa_s + fa_e, L_FORE))
    elbow_b = _add(sh_b, _vec(ba_s, L_UP))
    hand_b = _add(elbow_b, _vec(ba_s + ba_e, L_FORE))
    hx, hy = p["head"]
    head = (neck[0] + u[0] * 14 + hx, neck[1] + u[1] * 14 + hy)
    return {
        "pose": p, "hip": hip, "u": u, "perp": perp, "neck": neck, "shoulder": shoulder,
        "knee_f": _add(hip, knee_f), "foot_f": _add(hip, foot_f),
        "knee_b": _add(hip, knee_b), "foot_b": _add(hip, foot_b),
        "sh_f": sh_f, "sh_b": sh_b, "elbow_f": elbow_f, "hand_f": hand_f,
        "elbow_b": elbow_b, "hand_b": hand_b, "head": head,
        "shin_f": fl_h - fl_k, "shin_b": bl_h - bl_k,
    }


# ----------------------------------------------------------------- cabeças ---

def _eyes(s, expr, y=16, brow=None, back_x=15, front_x=22):
    if expr == "ko":
        for x in (back_x, front_x):
            pygame.draw.line(s, OUTLINE, (x, y - 1), (x + 3, y + 2))
            pygame.draw.line(s, OUTLINE, (x + 3, y - 1), (x, y + 2))
        return
    if expr in ("hurt", "eat"):
        pygame.draw.line(s, OUTLINE, (back_x, y), (back_x + 3, y + 1))
        pygame.draw.line(s, OUTLINE, (front_x, y + 1), (front_x + 3, y))
        return
    for x in (back_x, front_x):
        pygame.draw.rect(s, (250, 250, 250), (x, y, 4, 3))
        pygame.draw.rect(s, OUTLINE, (x + 2, y, 2, 3))


def _mouth(s, expr, y=26, x0=18, x1=25, lip=(170, 90, 80)):
    if expr in ("shout", "hurt"):
        pygame.draw.ellipse(s, (60, 15, 20), (x0, y - 2, x1 - x0 + 2, 6))
        pygame.draw.line(s, (245, 245, 245), (x0 + 1, y - 1), (x1, y - 1))
    elif expr == "ko":
        pygame.draw.ellipse(s, (60, 15, 20), (x0 + 2, y - 1, 4, 4))
    elif expr == "happy":
        pygame.draw.polygon(s, (90, 20, 25), [(x0, y - 1), (x1 + 1, y - 1), (x1 - 1, y + 2), (x0 + 2, y + 2)])
        pygame.draw.line(s, (250, 250, 250), (x0 + 1, y - 1), (x1, y - 1))
    elif expr == "eat":
        pygame.draw.circle(s, (60, 15, 20), ((x0 + x1) // 2, y), 2)
        pygame.draw.circle(s, (240, 150, 140), (x1 + 1, y - 3), 3)
    else:
        pygame.draw.line(s, lip, (x0, y), (x1, y), 1)


def _nose(s, skin, big=False):
    d = shade(skin, 0.8)
    if big:
        pygame.draw.polygon(s, d, [(24, 16), (30, 22), (24, 23)])
    else:
        pygame.draw.polygon(s, d, [(24, 17), (28, 22), (24, 22)])


def _draw_bolsonaro(s, st, expr):
    skin = st["skin"]
    hair = (72, 64, 58)
    gray = (138, 132, 126)
    pygame.draw.ellipse(s, skin, (4, 4, 25, 30))
    pygame.draw.rect(s, skin, (8, 20, 19, 12), border_radius=4)  # mandíbula larga
    pygame.draw.ellipse(s, shade(skin, 0.85), (4, 15, 6, 9))      # orelha
    pygame.draw.polygon(s, hair, [(3, 18), (3, 8), (8, 2), (17, 1), (26, 3), (29, 9), (26, 9),
                                  (20, 7), (14, 9), (10, 12), (9, 17), (6, 15)])
    pygame.draw.line(s, gray, (5, 9), (8, 5))
    pygame.draw.line(s, gray, (4, 14), (5, 11))
    pygame.draw.line(s, shade(hair, 0.6), (14, 3), (12, 8))       # risca lateral
    pygame.draw.line(s, (60, 50, 45), (14, 14), (19, 14), 1)
    pygame.draw.line(s, (60, 50, 45), (21, 14), (26, 13), 1)
    _eyes(s, expr, 16)
    _nose(s, skin)
    _mouth(s, expr, 27, 18, 25)


def _draw_lula(s, st, expr):
    skin = st["skin"]
    hair = (226, 226, 222)
    beard = (212, 212, 208)
    beard_d = (170, 170, 168)
    pygame.draw.ellipse(s, skin, (3, 4, 27, 30))
    pygame.draw.ellipse(s, shade(skin, 0.85), (3, 15, 6, 9))
    pygame.draw.polygon(s, hair, [(2, 20), (2, 9), (7, 3), (14, 1), (20, 2), (17, 5), (11, 7), (8, 12), (7, 17)])
    pygame.draw.ellipse(s, hair, (14, 1, 11, 4))
    # barba cheia
    pygame.draw.polygon(s, beard, [(6, 17), (9, 20), (14, 22), (19, 23), (27, 22), (30, 24), (29, 30),
                                   (24, 35), (15, 35), (8, 31), (5, 24)])
    pygame.draw.line(s, beard_d, (10, 30), (14, 33))
    pygame.draw.line(s, beard_d, (20, 33), (25, 31))
    pygame.draw.rect(s, beard, (18, 22, 11, 3))  # bigode
    pygame.draw.line(s, (130, 120, 115), (13, 13), (19, 14), 2)
    pygame.draw.line(s, (130, 120, 115), (21, 14), (27, 13), 2)
    _eyes(s, expr, 16)
    _nose(s, skin, big=True)
    _mouth(s, expr, 27, 19, 25, lip=(150, 90, 85))


def _draw_xandao(s, st, expr):
    skin = st["skin"]
    pygame.draw.ellipse(s, skin, (3, 1, 27, 33))
    pygame.draw.rect(s, skin, (8, 22, 19, 11), border_radius=5)
    pygame.draw.arc(s, shade(skin, 0.86), (3, 1, 27, 33), 2.0, 3.6, 2)  # sombra da careca
    pygame.draw.ellipse(s, shade(skin, 0.85), (3, 15, 6, 9))
    pygame.draw.line(s, (255, 244, 232), (11, 5), (17, 3), 2)          # brilho da careca
    pygame.draw.line(s, (255, 244, 232), (20, 4), (21, 4), 1)
    brow = (25, 20, 20)
    if expr in ("normal", "shout"):
        pygame.draw.line(s, brow, (13, 12), (19, 15), 2)
        pygame.draw.line(s, brow, (21, 15), (27, 11), 2)
    else:
        pygame.draw.line(s, brow, (13, 13), (19, 13), 2)
        pygame.draw.line(s, brow, (21, 13), (27, 13), 2)
    pygame.draw.line(s, shade(skin, 0.8), (15, 20), (18, 20))           # olheiras
    pygame.draw.line(s, shade(skin, 0.8), (22, 20), (25, 20))
    _eyes(s, expr, 16)
    _nose(s, skin)
    if expr == "normal":
        pygame.draw.lines(s, (130, 70, 65), False, [(18, 28), (19, 27), (24, 27), (25, 28)])
    else:
        _mouth(s, expr, 28, 18, 25)


_HEADS = {"bolsonaro": _draw_bolsonaro, "lula": _draw_lula, "xandao": _draw_xandao}


def _face_image(char_id):
    """Rosto real opcional: assets/personagens/<id>/rosto.png (fundo transparente)."""
    if char_id in _face_img_cache:
        return _face_img_cache[char_id]
    img = None
    path = ASSETS / "personagens" / char_id / "rosto.png"
    if path.exists():
        try:
            raw = pygame.image.load(str(path)).convert_alpha()
            img = gfx.pixelate(raw, (32, 36), pixel=1, colors=20, saturation=1.15)
        except pygame.error:
            img = None
    _face_img_cache[char_id] = img
    return img


def head(style, expr="normal", silenced=False, drunk=False):
    key = (style["head"], style.get("skin"), expr, silenced, drunk)
    if key in _head_cache:
        return _head_cache[key]
    s = pygame.Surface((32, 37), pygame.SRCALPHA)
    real = _face_image(style["head"])
    if real is not None:
        s.blit(real, (0, 0))
        if expr == "ko":
            _eyes(s, "ko", 15)
    else:
        _HEADS[style["head"]](s, style, expr)
    if drunk:
        pygame.draw.circle(s, (240, 90, 90), (26, 22), 2)
        pygame.draw.circle(s, (240, 120, 120), (17, 22), 2)
    if silenced:
        pygame.draw.rect(s, (8, 8, 8), (11, 14, 20, 6))
    s = gfx.outlined(s, OUTLINE)
    _head_cache[key] = s
    return s


def portrait(style, scale=3, expr="normal"):
    h = head(style, expr)
    return pygame.transform.scale(h, (h.get_width() * scale, h.get_height() * scale))


# ------------------------------------------------------------------- corpo ---

def _shoe(s, foot, shin_angle, color):
    a = math.radians(shin_angle + 90)
    d = (math.sin(a), math.cos(a))
    heel = _add(foot, d, -3)
    toe = _add(foot, d, 8)
    _limb(s, heel, toe, 5, color)


def _leg(s, sk, side, st, k=1.0):
    pants = shade(st["pants"], k)
    hip, knee, foot = sk["hip"], sk["knee_" + side], sk["foot_" + side]
    _limb(s, hip, knee, 10, pants)
    _limb(s, knee, foot, 8, pants)
    _shoe(s, foot, sk["shin_" + side], shade(st["shoes"], k))


def _arm(s, sk, side, st, k=1.0):
    sh, el, ha = sk["sh_" + side], sk["elbow_" + side], sk["hand_" + side]
    skin = shade(st["skin"], k)
    outfit = st["outfit"]
    if outfit == "jersey":
        _limb(s, sh, el, 7, skin)
        _limb(s, el, ha, 6, skin)
        cuff = _add(sh, (el[0] - sh[0], el[1] - sh[1]), 0.65)
        _limb(s, sh, cuff, 9, shade(st["shirt"], k))
        pygame.draw.circle(s, shade(st["trim"], k), _ip(cuff), 3)
    elif outfit == "suit":
        _limb(s, sh, el, 8, shade(st["jacket"], k))
        _limb(s, el, ha, 7, shade(st["jacket"], k))
        cuff = _add(el, (ha[0] - el[0], ha[1] - el[1]), 0.8)
        pygame.draw.circle(s, shade(st["shirt"], k), _ip(cuff), 3)
    else:  # toga: mangas largas
        _limb(s, sh, el, 11, shade(st["robe"], k))
        _limb(s, el, ha, 10, shade(st["robe"], k))
        pygame.draw.line(s, shade(st["robe_hi"], k), _ip(sh), _ip(el), 1)
    pygame.draw.circle(s, skin, _ip(ha), 4)


def _torso(s, sk, st):
    hip, sh, neck = sk["hip"], sk["shoulder"], sk["neck"]
    u, p = sk["u"], sk["perp"]
    girth = 11 if st["outfit"] == "suit" else 10
    pts = [_add(_add(hip, p, -girth + 1), u, -2), _add(_add(hip, p, girth + 1), u, -2),
           _add(_add(sh, p, girth + 2), u, 3), _add(_add(sh, p, -girth - 1), u, 3)]
    outfit = st["outfit"]
    if outfit == "jersey":
        pygame.draw.polygon(s, st["shirt"], [_ip(q) for q in pts])
        pygame.draw.polygon(s, st["trim"], [_ip(_add(neck, p, -4)), _ip(_add(neck, p, 5)),
                                            _ip(_add(_add(neck, u, -7), p, 1))])
        pygame.draw.line(s, shade(st["shirt"], 0.8), _ip(_add(_add(hip, p, -girth + 2), u, 3)),
                         _ip(_add(_add(hip, p, girth), u, 3)), 2)
        crest = _add(_add(sh, p, 5), u, -6)
        pygame.draw.circle(s, st["trim"], _ip(crest), 3)
        pygame.draw.circle(s, (40, 80, 180), _ip(crest), 1)
    elif outfit == "suit":
        pygame.draw.polygon(s, st["jacket"], [_ip(q) for q in pts])
        v = [_add(neck, p, -3), _add(neck, p, 6), _add(_add(neck, u, -14), p, 3)]
        pygame.draw.polygon(s, st["shirt"], [_ip(q) for q in v])
        tie = [_add(_add(neck, u, -1), p, 1), _add(_add(neck, u, -1), p, 4),
               _add(_add(neck, u, -17), p, 4), _add(_add(neck, u, -19), p, 2), _add(_add(neck, u, -17), p, 0)]
        pygame.draw.polygon(s, st["tie"], [_ip(q) for q in tie])
        pygame.draw.circle(s, (220, 30, 40), _ip(_add(_add(neck, u, -8), p, -5)), 1)  # broche
        for k in (13, 20):
            pygame.draw.circle(s, shade(st["jacket"], 0.6), _ip(_add(_add(neck, u, -k), p, 5)), 1)
    else:
        pygame.draw.polygon(s, st["pants"], [_ip(q) for q in pts])


def _robe(s, sk, st):
    hip, sh, neck = sk["hip"], sk["shoulder"], sk["neck"]
    u, p = sk["u"], sk["perp"]
    cape = sk["pose"]["cape"]
    hem_y = min(AY - 6, hip[1] + 36)
    kf = sk["knee_f"]
    front_flare = max(14, (kf[0] - hip[0]) * 0.7 + 8)
    pts = [
        _add(_add(sh, p, -14), u, 4),
        _add(_add(sh, p, 14), u, 4),
        (hip[0] + front_flare, hip[1] + 4),
        (hip[0] + front_flare + 2, hem_y),
        (hip[0] - 4, hem_y + 2),
        (hip[0] - 20 - cape, hem_y - 2 - cape * 0.3),
        _add(_add(hip, p, -13), u, 6),
    ]
    pygame.draw.polygon(s, st["robe"], [_ip(q) for q in pts])
    pygame.draw.line(s, st["robe_hi"], _ip(_add(_add(sh, p, 6), u, 2)), _ip((hip[0] + front_flare - 2, hem_y - 2)), 1)
    pygame.draw.line(s, st["robe_hi"], _ip(_add(hip, p, -6)), _ip((hip[0] - 12 - cape * 0.6, hem_y - 2)), 1)
    col = [_add(neck, p, -5), _add(neck, p, 6), _add(_add(neck, u, -5), p, 4), _add(_add(neck, u, -5), p, -3)]
    pygame.draw.polygon(s, st["collar"], [_ip(q) for q in col])


def render(style, pose, grounded=True, silenced=False, drunk=False):
    """Desenha o lutador olhando para a direita. Retorna (surface, esqueleto)."""
    sk = skeleton(pose, grounded)
    s = pygame.Surface((CW, CH), pygame.SRCALPHA)
    st = style
    _arm(s, sk, "b", st, 0.72)
    _leg(s, sk, "b", st, 0.72)
    if st["outfit"] == "toga":
        _leg(s, sk, "f", st)
        _torso(s, sk, st)
        _robe(s, sk, st)
        if sk["pose"]["fl"][0] > 60:
            _leg(s, sk, "f", st)
    else:
        _torso(s, sk, st)
        _leg(s, sk, "f", st)
    neck_top = _add(sk["neck"], sk["u"], 4)
    _limb(s, sk["neck"], neck_top, 7, shade(st["skin"], 0.9))
    h = head(st, sk["pose"]["expr"], silenced, drunk)
    hc = _ip(sk["head"])
    s.blit(h, (hc[0] - 16, hc[1] - 18))
    _arm(s, sk, "f", st)
    hold = sk["pose"]["hold"]
    if hold:
        it = item(hold)
        hp = _ip(sk["hand_f"])
        s.blit(it, (hp[0] - it.get_width() // 2, hp[1] - it.get_height() // 2))
    return gfx.outlined(s, OUTLINE), sk


# ------------------------------------------------------------------- itens ---

def _cloroquina():
    s = pygame.Surface((22, 11), pygame.SRCALPHA)
    pygame.draw.rect(s, (215, 40, 45), (0, 0, 11, 11), border_top_left_radius=5, border_bottom_left_radius=5)
    pygame.draw.rect(s, (250, 250, 250), (11, 0, 11, 11), border_top_right_radius=5, border_bottom_right_radius=5)
    pygame.draw.line(s, (255, 150, 150), (3, 2), (9, 2))
    pygame.draw.line(s, (255, 255, 255), (12, 2), (18, 2))
    pygame.draw.line(s, (120, 20, 25), (11, 0), (11, 10))
    return s


def _viagra():
    s = pygame.Surface((16, 12), pygame.SRCALPHA)
    pygame.draw.polygon(s, (70, 120, 235), [(8, 0), (15, 6), (8, 11), (0, 6)])
    pygame.draw.line(s, (170, 200, 255), (5, 4), (8, 2))
    return s


def _leite():
    s = pygame.Surface((15, 19), pygame.SRCALPHA)
    pygame.draw.rect(s, (35, 85, 190), (1, 2, 13, 15))
    pygame.draw.rect(s, (250, 250, 245), (1, 7, 13, 5))
    pygame.draw.circle(s, (35, 85, 190), (7, 9), 2)
    pygame.draw.ellipse(s, (190, 190, 200), (0, 0, 15, 4))
    pygame.draw.ellipse(s, (160, 160, 170), (0, 15, 15, 4))
    pygame.draw.line(s, (120, 160, 240), (3, 3), (3, 6))
    return s


def _picanha():
    s = pygame.Surface((30, 16), pygame.SRCALPHA)
    pygame.draw.line(s, (150, 105, 60), (0, 9), (29, 9), 2)
    pygame.draw.ellipse(s, (150, 45, 38), (6, 3, 18, 12))
    pygame.draw.ellipse(s, (245, 228, 190), (7, 1, 16, 5))
    for x in (11, 15, 19):
        pygame.draw.line(s, (80, 25, 20), (x, 7), (x - 2, 12))
    return s


def _pinga51():
    s = pygame.Surface((11, 28), pygame.SRCALPHA)
    glass = (190, 225, 210)
    pygame.draw.rect(s, glass, (3, 0, 5, 9))
    pygame.draw.rect(s, (20, 20, 20), (3, 0, 5, 2))
    pygame.draw.rect(s, glass, (1, 8, 9, 19), border_radius=2)
    pygame.draw.rect(s, (238, 236, 205), (1, 13, 9, 14), border_radius=2)
    pygame.draw.rect(s, (250, 205, 40), (1, 14, 9, 9))
    t = gfx.font(11).render("51", False, (210, 25, 30))
    s.blit(t, (5 - t.get_width() // 2 + 1, 15))
    pygame.draw.line(s, (240, 255, 250), (2, 9), (2, 12))
    return s


def _abobora():
    s = pygame.Surface((24, 22), pygame.SRCALPHA)
    o, d = (238, 122, 25), (190, 85, 15)
    pygame.draw.ellipse(s, d, (0, 4, 13, 18))
    pygame.draw.ellipse(s, d, (11, 4, 13, 18))
    pygame.draw.ellipse(s, o, (4, 3, 16, 19))
    pygame.draw.line(s, d, (12, 6), (12, 20))
    pygame.draw.rect(s, (60, 120, 40), (10, 0, 4, 5))
    pygame.draw.line(s, (255, 190, 110), (7, 8), (7, 13))
    return s


def _constituicao():
    s = pygame.Surface((22, 26), pygame.SRCALPHA)
    pygame.draw.rect(s, (250, 248, 235), (3, 1, 19, 24))
    pygame.draw.rect(s, (20, 105, 55), (0, 0, 19, 26), border_radius=2)
    pygame.draw.rect(s, (10, 70, 35), (0, 0, 4, 26))
    pygame.draw.circle(s, (232, 192, 50), (11, 10), 5)
    pygame.draw.circle(s, (20, 70, 160), (11, 10), 3)
    pygame.draw.line(s, (232, 192, 50), (6, 18), (16, 18))
    pygame.draw.line(s, (232, 192, 50), (7, 21), (15, 21))
    return s


def _inquerito():
    s = pygame.Surface((22, 16), pygame.SRCALPHA)
    pygame.draw.rect(s, (215, 175, 100), (0, 0, 9, 4), border_radius=1)
    pygame.draw.rect(s, (228, 192, 120), (0, 2, 22, 14), border_radius=1)
    pygame.draw.rect(s, (200, 30, 35), (4, 6, 14, 6), 1)
    pygame.draw.line(s, (200, 30, 35), (6, 9), (16, 9))
    return s


def _carimbo():
    s = pygame.Surface((64, 66), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (160, 95, 45), (22, 0, 20, 14))
    pygame.draw.rect(s, (140, 82, 38), (28, 11, 8, 22))
    pygame.draw.rect(s, (120, 70, 35), (6, 31, 52, 15), border_radius=3)
    pygame.draw.line(s, (170, 110, 60), (9, 34), (54, 34))
    pygame.draw.rect(s, (205, 25, 35), (4, 46, 56, 10))
    return s


_ITEMS = {
    "cloroquina": _cloroquina, "viagra": _viagra, "leite": _leite, "picanha": _picanha,
    "pinga51": _pinga51, "abobora": _abobora, "constituicao": _constituicao,
    "inquerito": _inquerito, "carimbo": _carimbo,
}


def item(kind):
    if kind not in _item_cache:
        _item_cache[kind] = gfx.outlined(_ITEMS[kind](), OUTLINE)
    return _item_cache[kind]


def stamp_mark(size=22):
    key = ("stamp", size)
    if key not in _item_cache:
        red = (210, 25, 35)
        t = gfx.font(size).render("CENSURADO", False, red)
        w, h = t.get_size()
        s = pygame.Surface((w + 10, h + 8), pygame.SRCALPHA)
        s.blit(t, (5, 5))
        pygame.draw.rect(s, red, s.get_rect(), 2)
        rng = random.Random(3)
        for _ in range(int(w * h * 0.12)):
            s.set_at((rng.randrange(s.get_width()), rng.randrange(s.get_height())), (0, 0, 0, 0))
        s = pygame.transform.rotate(s, 14)
        s.set_alpha(225)
        _item_cache[key] = s
    return _item_cache[key]
