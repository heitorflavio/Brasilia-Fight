"""Áudio: efeitos sintetizados, vozes (arquivos reais ou "balbucio" sintético) e música chiptune.

Qualquer som sintetizado pode ser substituído por um arquivo real:
  * efeitos:  assets/sons/<nome>.wav|ogg|mp3          (ex.: assets/sons/ko.wav)
  * falas:    assets/personagens/<id>/<fala>.wav|ogg|mp3 (ex.: assets/personagens/lula/picanha.mp3)
  * música:   assets/musica/<qualquer>.ogg|mp3|wav
"""
import random
import re

import numpy as np
import pygame

from .config import ASSETS

SR = 44100
AUDIO_EXTS = (".wav", ".ogg", ".mp3")

_enabled = False
_channels = 2
_cache = {}
_voice_channel = {}
_music_sound = None
_music_channel = None
music_on = True


def init():
    global _enabled, _channels
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(SR, -16, 2, 512)
        _, _, _channels = pygame.mixer.get_init()
        pygame.mixer.set_num_channels(24)
        pygame.mixer.set_reserved(3)  # 0 = música, 1 = voz P1, 2 = voz P2
        _enabled = True
    except pygame.error:
        _enabled = False


def _find_file(base):
    for ext in AUDIO_EXTS:
        p = base.with_suffix(ext)
        if p.exists():
            return p
    return None


def _to_sound(samples, volume=1.0):
    samples = np.asarray(samples, dtype=np.float64) * volume
    samples = np.clip(samples, -1.0, 1.0)
    data = (samples * 32000).astype(np.int16)
    if _channels == 2:
        data = np.column_stack([data, data])
    return pygame.sndarray.make_sound(np.ascontiguousarray(data))


# ---------------------------------------------------------------- síntese ---

def _n(dur):
    return max(1, int(SR * dur))


def osc(freq, dur, kind="square", duty=0.5):
    n = _n(dur)
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    phase = np.cumsum(f) / SR
    p = phase % 1.0
    if kind == "square":
        return np.where(p < duty, 1.0, -1.0)
    if kind == "triangle":
        return 4.0 * np.abs(p - 0.5) - 1.0
    if kind == "saw":
        return 2.0 * p - 1.0
    return np.sin(2 * np.pi * phase)


def noise(dur, seed=None):
    rng = np.random.default_rng(seed)
    return rng.uniform(-1, 1, _n(dur))


def env(n, attack=0.005, release=None, decay_pow=1.0):
    """Envelope simples: ataque linear e decaimento exponencial-ish."""
    e = np.ones(n)
    a = min(n, _n(attack))
    if a > 0:
        e[:a] = np.linspace(0, 1, a)
    rest = n - a
    if rest > 0:
        e[a:] = np.linspace(1, 0, rest) ** decay_pow
    if release:
        r = min(n, _n(release))
        e[-r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, k):
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def sweep(f0, f1, dur):
    return np.geomspace(max(f0, 1), max(f1, 1), _n(dur))


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p
    return out


def _sfx_defs():
    d = {}
    nz = noise(0.08, 1)
    d["soco"] = mix(lowpass(nz, 6) * env(len(nz), 0.001, decay_pow=3) * 0.8,
                    osc(sweep(160, 60, 0.09), 0.09, "sine") * env(_n(0.09), 0.001, decay_pow=2))
    nz = noise(0.12, 2)
    d["chute"] = mix(lowpass(nz, 10) * env(len(nz), 0.001, decay_pow=3) * 0.8,
                     osc(sweep(110, 40, 0.16), 0.16, "sine") * env(_n(0.16), 0.001, decay_pow=2) * 1.1)
    d["pesado"] = mix(lowpass(noise(0.2, 3), 14) * env(_n(0.2), 0.001, decay_pow=2.5),
                      osc(sweep(90, 30, 0.3), 0.3, "sine") * env(_n(0.3), 0.001, decay_pow=1.5) * 1.2)
    d["bloqueio"] = mix(osc(1200, 0.05, "square", 0.3) * env(_n(0.05), 0.001, decay_pow=4) * 0.35,
                        lowpass(noise(0.04, 4), 2) * env(_n(0.04), 0.001, decay_pow=4) * 0.5)
    nz = lowpass(noise(0.18, 5), 8)
    d["whoosh"] = nz * np.sin(np.linspace(0, np.pi, len(nz))) * 0.5
    d["pulo"] = osc(sweep(180, 520, 0.1), 0.1, "square", 0.25) * env(_n(0.1), 0.002, decay_pow=1.5) * 0.25
    d["queda"] = mix(osc(sweep(80, 35, 0.25), 0.25, "sine") * env(_n(0.25), 0.001, decay_pow=1.5),
                     lowpass(noise(0.15, 6), 20) * env(_n(0.15), 0.001, decay_pow=2) * 0.6)
    notes = [523, 659, 784, 1047]
    d["especial"] = np.concatenate([osc(f, 0.045, "square", 0.25) * env(_n(0.045), 0.001) * 0.3 for f in notes])
    sup = mix(*[osc(f, 0.7, "saw") * 0.18 for f in (110, 165, 220, 277)])
    d["super"] = mix(sup * env(len(sup), 0.25, decay_pow=1.2), lowpass(noise(0.7, 7), 30) * env(_n(0.7), 0.3) * 0.5)
    d["explosao"] = mix(lowpass(noise(0.6, 8), 25) * env(_n(0.6), 0.002, decay_pow=1.8) * 1.2,
                        osc(sweep(70, 25, 0.5), 0.5, "sine") * env(_n(0.5), 0.002, decay_pow=1.5))
    pings = [osc(f, 0.35, "sine") * env(_n(0.35), 0.001, decay_pow=4) * 0.25 for f in (2900, 4100, 5300, 3500)]
    glass = mix(*pings, noise(0.12, 9) * env(_n(0.12), 0.001, decay_pow=3) * 0.6)
    d["vidro"] = glass
    d["carimbo"] = mix(osc(sweep(70, 30, 0.35), 0.35, "sine") * env(_n(0.35), 0.001, decay_pow=1.3) * 1.3,
                       lowpass(noise(0.08, 10), 4) * env(_n(0.08), 0.001, decay_pow=2))
    chain = np.zeros(_n(0.35))
    rng = random.Random(11)
    for i in range(7):
        start = _n(i * 0.045)
        ping = osc(rng.uniform(2200, 3800), 0.06, "square", 0.5) * env(_n(0.06), 0.001, decay_pow=5) * 0.2
        chain[start:start + len(ping)] += ping[: len(chain) - start]
    d["corrente"] = chain
    sz = noise(0.45, 12)
    sz = (sz - lowpass(sz, 4)) * (0.6 + 0.4 * np.sin(np.linspace(0, 60, len(sz))))
    d["chiado"] = sz * env(len(sz), 0.01) * 0.6
    d["ko"] = osc(sweep(700, 70, 0.9), 0.9, "square", 0.4) * env(_n(0.9), 0.005) * 0.3
    d["select"] = osc(880, 0.05, "square", 0.25) * env(_n(0.05), 0.001) * 0.25
    d["confirmar"] = np.concatenate([osc(660, 0.06, "square", 0.25), osc(990, 0.1, "square", 0.25)]) * 0.25
    d["comer"] = np.concatenate([osc(sweep(500, 150, 0.08), 0.08, "square", 0.3),
                                 np.zeros(_n(0.04)),
                                 osc(sweep(450, 120, 0.1), 0.1, "square", 0.3)]) * 0.25
    stab = mix(*[osc(f, 0.5, "saw") * 0.2 for f in (196, 247, 294, 392)])
    d["fight"] = stab * env(len(stab), 0.005, decay_pow=1.5)
    d["round"] = mix(*[osc(f, 0.35, "square", 0.3) * 0.15 for f in (330, 415, 494)]) * env(_n(0.35), 0.005)
    d["vitoria"] = np.concatenate([osc(f, 0.12, "square", 0.25) * env(_n(0.12), 0.002) * 0.25
                                   for f in (523, 659, 784, 1047, 784, 1047)])
    return d


def sfx(name, volume=0.8):
    if not _enabled:
        return
    key = ("sfx", name)
    if key not in _cache:
        f = _find_file(ASSETS / "sons" / name)
        if f:
            try:
                _cache[key] = pygame.mixer.Sound(str(f))
            except pygame.error:
                f = None
        if not f:
            defs = _SFX.get(name)
            if defs is None:
                return
            _cache[key] = _to_sound(defs)
    snd = _cache[key]
    snd.set_volume(volume)
    snd.play()


# ------------------------------------------------------------------- vozes ---

_VOWELS = {
    "a": (800, 1250), "á": (800, 1250), "â": (650, 1200), "ã": (700, 1250), "à": (800, 1250),
    "e": (500, 1850), "é": (550, 1800), "ê": (450, 1900),
    "i": (300, 2300), "í": (300, 2300),
    "o": (500, 900), "ó": (550, 950), "ô": (450, 850), "õ": (480, 900),
    "u": (330, 800), "ú": (330, 800),
}
_SYL_RE = re.compile(r"[^aeiouáéíóúâêôãõà\W]*[aeiouáéíóúâêôãõà]+[^aeiouáéíóúâêôãõà\W]?|[\s,.!?]+")


def babble(text, pitch=130.0, rasp=0.0, seed=0):
    """Gera uma 'fala' estilo videogame retrô a partir do texto (sílabas com formantes)."""
    rng = random.Random(seed)
    parts = []
    syllables = _SYL_RE.findall(text.lower())
    exclaim = text.strip().endswith("!")
    real = [s for s in syllables if s.strip(" ,.!?")]
    idx = 0
    for syl in syllables:
        if not syl.strip(" ,.!?"):
            parts.append(np.zeros(_n(0.06 if "," in syl or "." in syl else 0.03)))
            continue
        idx += 1
        last = idx == len(real)
        dur = rng.uniform(0.07, 0.1) * (1.6 if last else 1.0)
        n = _n(dur)
        f0 = pitch * (1 + rng.uniform(-0.1, 0.18))
        if last and exclaim:
            f0s = np.linspace(f0 * 1.15, f0 * 0.8, n)
        else:
            f0s = np.linspace(f0, f0 * rng.uniform(0.9, 1.05), n)
        f0s = f0s * (1 + 0.02 * np.sin(np.arange(n) / SR * 2 * np.pi * 6))
        vowel = next((c for c in syl if c in _VOWELS), "a")
        F1, F2 = _VOWELS[vowel]
        phase = np.cumsum(f0s) / SR
        sig = np.zeros(n)
        k = 1
        while k * f0 < 3800:
            fk = k * f0
            amp = np.exp(-((fk - F1) / 180) ** 2) + 0.6 * np.exp(-((fk - F2) / 260) ** 2) + 0.12 / k
            sig += amp * np.sin(2 * np.pi * k * phase)
            k += 1
        sig /= max(1e-6, np.abs(sig).max())
        if rasp:
            sig = sig * (1 - rasp) + lowpass(noise(dur, rng.randint(0, 999)), 3) * rasp * np.abs(sig)
        sig *= env(n, 0.008, release=0.03, decay_pow=0.6)
        cons = syl[0]
        if cons not in _VOWELS:
            hiss_d = 0.05 if cons in "sxzcç" else 0.018
            hiss = noise(hiss_d, rng.randint(0, 999))
            if cons in "sxzcç":
                hiss = hiss - lowpass(hiss, 3)
            else:
                hiss = lowpass(hiss, 6)
            hiss *= env(len(hiss), 0.002, decay_pow=2) * 0.35
            sig = np.concatenate([hiss, sig])
        parts.append(sig)
        parts.append(np.zeros(_n(0.012)))
    if not parts:
        return np.zeros(_n(0.1))
    out = np.concatenate(parts)
    # leve saturação para soar "rádio AM"
    return np.tanh(out * 1.6) * 0.7


def voice(char_id, line_id, text, pitch=130.0, rasp=0.0, slot=1):
    """Toca a fala de um personagem. Usa o arquivo real se existir, senão sintetiza."""
    if not _enabled:
        return
    key = ("voz", char_id, line_id)
    if key not in _cache:
        f = _find_file(ASSETS / "personagens" / char_id / line_id)
        snd = None
        if f:
            try:
                snd = pygame.mixer.Sound(str(f))
            except pygame.error:
                snd = None
        if snd is None:
            snd = _to_sound(babble(text, pitch, rasp, seed=hash((char_id, line_id)) & 0xFFFF), 0.9)
        _cache[key] = snd
    ch = pygame.mixer.Channel(slot)
    ch.play(_cache[key])


def has_real_voice(char_id, line_id):
    return _find_file(ASSETS / "personagens" / char_id / line_id) is not None


# ------------------------------------------------------------------ música ---

_NOTE_IDX = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def _midi_freq(name):
    m = re.match(r"([A-G]#?)(\d)", name)
    n = _NOTE_IDX[m.group(1)] + 12 * (int(m.group(2)) + 1)
    return 440.0 * 2 ** ((n - 69) / 12)


def _compose():
    bpm = 142
    step = 60 / bpm / 4  # semicolcheia
    bars = [
        ("A2", "A4 - C5 - E5 - D5 C5"), ("A2", "A4 - - G4 A4 - - -"),
        ("F2", "F4 - A4 - C5 - A4 C5"), ("G2", "D5 - B4 - G4 - B4 D5"),
        ("A2", "E5 - - D5 C5 - B4 -"), ("A2", "A4 - C5 - E5 - A5 -"),
        ("D2", "G5 - F5 - E5 - D5 -"), ("E2", "E5 - - - G#4 - B4 -"),
        ("A2", "A4 - C5 - E5 - D5 C5"), ("A2", "A4 - - G4 A4 - - -"),
        ("F2", "F4 - A4 - C5 - A4 C5"), ("G2", "D5 - B4 - G4 - B4 D5"),
        ("F2", "C5 - A4 - F4 - A4 C5"), ("G2", "D5 - - B4 G4 - D5 -"),
        ("E2", "E5 - D5 - C5 - B4 -"), ("E2", "G#4 - B4 - E5 - - -"),
    ]
    bar_len = _n(step * 16)
    total = bar_len * len(bars)
    out = np.zeros(total + _n(1.0))

    def put(sig, pos):
        out[pos:pos + len(sig)] += sig[: len(out) - pos]

    kick = osc(sweep(120, 45, 0.16), 0.16, "sine") * env(_n(0.16), 0.001, decay_pow=1.5) * 0.7
    surdo = osc(sweep(75, 55, 0.35), 0.35, "sine") * env(_n(0.35), 0.002, decay_pow=1.2) * 0.6
    caixa = lowpass(noise(0.07, 21), 2) * env(_n(0.07), 0.001, decay_pow=3) * 0.18
    tamb = osc(1900, 0.03, "square", 0.5) * env(_n(0.03), 0.001, decay_pow=3) * 0.09
    ganza = (noise(0.03, 22) - lowpass(noise(0.03, 22), 3)) * env(_n(0.03), 0.002, decay_pow=2) * 0.12
    tamb_pat = "x.xx.x.x.xx.x.x."
    bass_steps = [0, 3, 6, 8, 11, 14]

    for b, (root, mel) in enumerate(bars):
        base = b * bar_len
        for s in range(16):
            pos = base + _n(step * s)
            if s in (0, 8):
                put(kick, pos)
            if s in (4, 12):
                put(surdo, pos)
            if s in (2, 5, 7, 10, 13, 15):
                put(caixa, pos)
            if tamb_pat[s] == "x":
                put(tamb, pos)
            put(ganza * (1.0 if s % 4 == 0 else 0.6), pos)
        rf = _midi_freq(root)
        for i, s in enumerate(bass_steps):
            f = rf * (2 if s == 6 else 1)
            d = step * (2 if i < len(bass_steps) - 1 else 1.5)
            note = osc(f, d, "triangle") * env(_n(d), 0.003, release=0.02, decay_pow=0.5) * 0.42
            put(note, base + _n(step * s))
        tokens = mel.split()
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            length = 1
            while i + length < len(tokens) and tokens[i + length] == "-":
                length += 1
            if tok not in ("-", "."):
                d = step * 2 * length * 0.95
                f = _midi_freq(tok)
                lead = osc(f, d, "square", 0.25) * 0.6 + osc(f * 1.005, d, "square", 0.5) * 0.4
                put(lead * env(_n(d), 0.004, release=0.03, decay_pow=0.4) * 0.16, base + _n(step * 2 * i))
                # eco
                put(lead * env(_n(d), 0.004, release=0.03, decay_pow=0.4) * 0.05, base + _n(step * 2 * i + step * 3))
            i += length
    out = out[:total]
    return out / max(1e-6, np.abs(out).max()) * 0.8


def play_music():
    global _music_sound, _music_channel
    if not _enabled or not music_on:
        return
    files = sorted(p for p in (ASSETS / "musica").glob("*") if p.suffix.lower() in AUDIO_EXTS)
    if files:
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(str(files[0]))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            return
        except pygame.error:
            pass
    if _music_sound is None:
        _music_sound = _to_sound(_compose(), 0.45)
    _music_channel = pygame.mixer.Channel(0)
    if not _music_channel.get_busy():
        _music_channel.play(_music_sound, loops=-1)


def stop_music():
    if not _enabled:
        return
    pygame.mixer.music.stop()
    pygame.mixer.Channel(0).stop()


def toggle_music():
    global music_on
    music_on = not music_on
    if music_on:
        play_music()
    else:
        stop_music()


_SFX = _sfx_defs()
