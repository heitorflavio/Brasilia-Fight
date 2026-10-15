"""Dados dos personagens: estilo visual, atributos, habilidades (comidas!) e falas.

Cada habilidade tem um `id` que também é o nome do arquivo de áudio opcional em
assets/personagens/<personagem>/<id>.wav|ogg|mp3 — coloque lá o áudio real da fala.
Os textos das falas abaixo acompanham os áudios reais que já estão em assets/ (troque os dois juntos).
"""

CHARACTERS = {
    "bolsonaro": {
        "name": "BOLSONARO",
        "full": "Jair Bolsonaro",
        "meme": "Bolsonaro",
        "nick": "O Capitão",
        "voice": {"pitch": 150, "rasp": 0.08},
        "walk": 2.6, "jump": -12.0, "power": 1.1, "defense": 0.95,
        "style": {
            "head": "bolsonaro", "outfit": "jersey",
            "skin": (238, 190, 158), "shirt": (252, 214, 30), "trim": (0, 140, 62),
            "pants": (36, 42, 66), "shoes": (28, 24, 22),
        },
        "alt": {"shirt": (40, 90, 200), "trim": (252, 214, 30), "pants": (240, 240, 240)},
        "intro": {"id": "intro", "fala": "Acabou, porra!"},
        "wins": [
            {"id": "vitoria1", "fala": "Chega de frescura, de mimimi!"},
            {"id": "vitoria2", "fala": "Obrigado, meu Deus!"},
            {"id": "vitoria3", "fala": "Já expliquei? Explica!"},
        ],
        "specials": {
            "s1": {"id": "cloroquina", "nome": "Cloroquina", "kind": "straight", "item": "cloroquina",
                   "fala": "Jacaré!", "dmg": 10, "speed": 7.0, "y": -84, "cooldown": 45,
                   "desc": "Cápsula na altura da cabeça (agache!)"},
            "s2": {"id": "leite_condensado", "nome": "Leite Condensado", "kind": "lob", "item": "leite",
                   "fala": "Popcorn and ice cream!", "dmg": 8, "speed": 4.4, "cooldown": 100,
                   "desc": "Lata em arco; poça grudenta deixa lento"},
            "s3": {"id": "viagra", "nome": "Viagra", "kind": "buff", "item": "viagra",
                   "fala": "IMBROCHÁVEL!", "super": True,
                   "desc": "Modo Imbrochável: +dano, +veloz, sem recuo"},
        },
    },
    "lula": {
        "name": "LULA",
        "full": "Luiz Inácio Lula da Silva",
        "meme": "Lula",
        "nick": "O Companheiro",
        "voice": {"pitch": 112, "rasp": 0.35},
        "walk": 2.25, "jump": -11.4, "power": 1.02, "defense": 0.95,
        "style": {
            "head": "lula", "outfit": "suit",
            "skin": (226, 172, 138), "jacket": (44, 50, 72), "shirt": (240, 240, 238), "tie": (205, 28, 40),
            "pants": (44, 50, 72), "shoes": (22, 18, 18),
        },
        "alt": {"jacket": (112, 30, 36), "pants": (112, 30, 36), "tie": (240, 200, 40)},
        "intro": {"id": "intro", "fala": "Agora, companheiros!"},
        "wins": [
            {"id": "vitoria1", "fala": "Tchau, querida!"},
            {"id": "vitoria2", "fala": "Eu vou comer picanha e vou tomar uma cerveja!"},
            {"id": "vitoria3", "fala": "Eu não sabia!"},
        ],
        "specials": {
            "s1": {"id": "picanha", "nome": "Picanha", "kind": "straight", "item": "picanha",
                   "fala": "Eu vou comer picanha!", "dmg": 10, "speed": 5.6, "y": -62, "cooldown": 60,
                   "desc": "Espeto de picanha na altura do peito"},
            "s2": {"id": "abobora", "nome": "Abóbora", "kind": "roll", "item": "abobora",
                   "fala": "E agora vai entrar o grosso!", "dmg": 12, "speed": 3.0, "cooldown": 120,
                   "desc": "Rola pelo chão (pule!) e derruba"},
            "s3": {"id": "pinga51", "nome": "51", "kind": "bottle", "item": "pinga51",
                   "fala": "Chupa que a cana é doce, meu filho!", "dmg": 16, "super": True,
                   "desc": "Garrafa explode e deixa o rival bêbado"},
        },
    },
    "xandao": {
        "name": "XANDÃO",
        "full": "Alexandre de Moraes",
        "meme": "Alexandre de Moraes",
        "nick": "O Supremo",
        "voice": {"pitch": 96, "rasp": 0.12},
        "walk": 2.3, "jump": -11.6, "power": 1.04, "defense": 1.0,
        "style": {
            "head": "xandao", "outfit": "toga",
            "skin": (232, 188, 162), "robe": (20, 20, 26), "robe_hi": (62, 62, 80), "collar": (245, 245, 245),
            "pants": (22, 22, 28), "shoes": (12, 12, 12),
        },
        "alt": {"robe": (95, 16, 28), "robe_hi": (150, 40, 55)},
        "intro": {"id": "intro", "fala": "Censura máxima!"},
        "wins": [
            {"id": "vitoria1", "fala": "Tu é patético e medíocre!"},
            {"id": "vitoria2", "fala": "Inconstitucional!"},
            {"id": "vitoria3", "fala": "Isso é inconstitucional! Isso precisa cessar imediatamente!"},
        ],
        "specials": {
            "s1": {"id": "constituicao", "nome": "Constituição", "kind": "straight", "item": "constituicao",
                   "fala": "Inconstitucional!", "dmg": 12, "speed": 4.6, "y": -66, "cooldown": 75,
                   "push": 7, "desc": "Livro pesado que empurra pra longe"},
            "s2": {"id": "inquerito", "nome": "Inquérito", "kind": "chain", "item": "inquerito",
                   "fala": "Vai pra cadeia!", "dmg": 5, "speed": 9.0, "cooldown": 150,
                   "range": 270, "desc": "Corrente que puxa e atordoa o rival"},
            "s3": {"id": "censurado", "nome": "Censurado", "kind": "stamp", "item": "carimbo",
                   "fala": "Censura máxima!", "dmg": 18, "super": True,
                   "desc": "Carimbo do céu: dano e cala o rival"},
        },
    },
}

ORDER = ["bolsonaro", "lula", "xandao"]


def style_for(char_id, alt=False):
    st = dict(CHARACTERS[char_id]["style"])
    if alt:
        st.update(CHARACTERS[char_id]["alt"])
    st["id"] = char_id
    return st
