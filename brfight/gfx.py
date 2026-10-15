"""Utilidades de desenho: texto pixelado, contornos e conversão de fotos em pixel art."""
import numpy as np
import pygame

from .config import ASSETS

_fonts = {}
UI_FONT = ASSETS / "fontes" / "VT323-Regular.ttf"

BLACK = (12, 10, 18)
WHITE = (250, 250, 245)
YELLOW = (255, 214, 40)
GREEN = (20, 155, 70)
BLUE = (30, 70, 160)
RED = (215, 35, 40)


def font(size):
    """Fonte grossa (padrão do pygame) para letreiros grandes."""
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def ui_font(size):
    """Fonte pixel (VT323) para textos de interface; tamanhos equivalentes aos da fonte padrão."""
    key = ("ui", size)
    if key not in _fonts:
        if UI_FONT.exists():
            px = 16 if size <= 13 else 18 if size <= 15 else 20 if size <= 17 else 22 if size <= 21 else \
                26 if size <= 24 else int(size * 1.15)
            _fonts[key] = pygame.font.Font(str(UI_FONT), px)
        else:
            _fonts[key] = pygame.font.Font(None, size)
    return _fonts[key]


_text_cache = {}


def _cached(fn):
    """Memoriza superfícies de texto (o HUD redesenha os mesmos textos todo quadro)."""
    def wrapper(*args, **kw):
        key = (fn.__name__, args, tuple(sorted(kw.items())))
        surf = _text_cache.get(key)
        if surf is None:
            if len(_text_cache) > 600:
                _text_cache.clear()
            surf = _text_cache[key] = fn(*args, **kw)
        return surf
    return wrapper


@_cached
def text_surface(text, size, color=WHITE, outline=BLACK, ow=1, shadow=False):
    f = ui_font(size)
    base = f.render(text, False, color)
    if outline is None and not shadow:
        return base
    w, h = base.get_size()
    pad = ow + (2 if shadow else 0)
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    if outline is not None:
        o = f.render(text, False, outline)
        if shadow:
            surf.blit(o, (pad + 2, pad + 2))
        for dx in range(-ow, ow + 1):
            for dy in range(-ow, ow + 1):
                if dx or dy:
                    surf.blit(o, (pad + dx, pad + dy))
    surf.blit(base, (pad, pad))
    return surf


def draw_text(dst, text, size, pos, color=WHITE, anchor="topleft", outline=BLACK, ow=1, shadow=False, alpha=255):
    s = text_surface(text, size, color, outline, ow, shadow)
    if alpha < 255:
        s = s.copy()
        s.set_alpha(alpha)
    r = s.get_rect(**{anchor: pos})
    dst.blit(s, r)
    return r


@_cached
def gradient_text(text, size, top=(255, 245, 120), bottom=(255, 120, 20), outline=BLACK, ow=3):
    """Texto grande estilo arcade: preenchimento em degradê + contorno grosso."""
    f = font(size)
    mask_s = f.render(text, False, (255, 255, 255))
    w, h = mask_s.get_size()
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        c = [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
        # faixa de brilho
        if abs(t - 0.35) < 0.06:
            c = [min(255, v + 50) for v in c]
        pygame.draw.line(grad, c, (0, y), (w, y))
    grad.blit(mask_s, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf = pygame.Surface((w + ow * 2 + 3, h + ow * 2 + 3), pygame.SRCALPHA)
    o = f.render(text, False, outline)
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            surf.blit(o, (ow + dx + 3, ow + dy + 3))
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            surf.blit(o, (ow + dx, ow + dy))
    surf.blit(grad, (ow, ow))
    return surf


def outlined(surf, color=BLACK):
    """Adiciona contorno de 1px ao redor dos pixels opacos (visual de sprite)."""
    mask = pygame.mask.from_surface(surf, 10)
    w, h = surf.get_size()
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    sil = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        out.blit(sil, (dx, dy))
    out.blit(surf, (0, 0))
    return out


def silhouette(surf, color):
    mask = pygame.mask.from_surface(surf, 10)
    return mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))


# ------------------------------------------------ foto -> pixel art -----

def quantize(surface, colors=32, iters=8, seed=0):
    """Reduz a paleta da imagem com k-means (numpy), mantendo o alfa."""
    rgb = pygame.surfarray.array3d(surface).astype(np.float32)
    w, h, _ = rgb.shape
    pix = rgb.reshape(-1, 3)
    rng = np.random.default_rng(seed)
    sample = pix[rng.choice(len(pix), size=min(len(pix), 6000), replace=False)]
    centers = sample[rng.choice(len(sample), size=colors, replace=False)].copy()
    for _ in range(iters):
        d = ((sample[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for k in range(colors):
            sel = sample[lab == k]
            if len(sel):
                centers[k] = sel.mean(0)
    # atribui todos os pixels em blocos para economizar memória
    out = np.empty_like(pix)
    for i in range(0, len(pix), 20000):
        chunk = pix[i:i + 20000]
        d = ((chunk[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
        out[i:i + 20000] = centers[d.argmin(1)]
    out = out.reshape(w, h, 3).astype(np.uint8)
    has_alpha = bool(surface.get_flags() & pygame.SRCALPHA)
    alpha = pygame.surfarray.array_alpha(surface) if has_alpha else None
    result = surface.copy()
    px = pygame.surfarray.pixels3d(result)
    px[:] = out
    del px
    if has_alpha:
        a = pygame.surfarray.pixels_alpha(result)
        a[:] = np.where(alpha > 128, 255, 0)
        del a
    return result


def boost(surface, saturation=1.25, contrast=1.1):
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    gray = arr.mean(axis=2, keepdims=True)
    arr = gray + (arr - gray) * saturation
    arr = (arr - 128) * contrast + 128
    out = surface.copy()
    px = pygame.surfarray.pixels3d(out)
    px[:] = np.clip(arr, 0, 255).astype(np.uint8)
    del px
    return out


def pixelate(surface, size, pixel=2, colors=32, saturation=1.25, contrast=1.08):
    """Converte uma imagem qualquer em pixel art no tamanho `size`.

    pixel = tamanho de cada 'pixel' grande; colors = cores da paleta.
    """
    w, h = size
    src = surface.convert_alpha() if surface.get_flags() & pygame.SRCALPHA else surface.convert()
    small = pygame.transform.smoothscale(src, (max(1, w // pixel), max(1, h // pixel)))
    small = boost(small, saturation, contrast)
    small = quantize(small, colors)
    return pygame.transform.scale(small, (w, h))


def crop_to_aspect(surface, aspect, focus_y=0.5, focus_x=0.5):
    w, h = surface.get_size()
    if w / h > aspect:
        nw = int(h * aspect)
        x = int((w - nw) * focus_x)
        return surface.subsurface((x, 0, nw, h)).copy()
    nh = int(w / aspect)
    y = int((h - nh) * focus_y)
    return surface.subsurface((0, y, w, nh)).copy()
