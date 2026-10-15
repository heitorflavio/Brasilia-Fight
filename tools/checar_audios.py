"""Lista quais falas já têm áudio real e quais ainda usam a voz sintetizada.

  python tools/checar_audios.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brfight.audio import has_real_voice  # noqa: E402
from brfight.characters import CHARACTERS, ORDER  # noqa: E402
from brfight.config import ASSETS  # noqa: E402


def lines_for(cid):
    d = CHARACTERS[cid]
    yield "nome", d["name"].title() + "!"
    yield d["intro"]["id"], d["intro"]["fala"]
    for sp in d["specials"].values():
        yield sp["id"], sp["fala"]
    for w in d["wins"]:
        yield w["id"], w["fala"]
    yield "ko", "(grito ao ser nocauteado — opcional, sem voz sintetizada)"


def main():
    missing = 0
    for cid in ORDER:
        print(f"\n{CHARACTERS[cid]['full']}  ->  {ASSETS / 'personagens' / cid}")
        for line_id, text in lines_for(cid):
            ok = has_real_voice(cid, line_id)
            missing += not ok and line_id != "ko"
            print(f"  [{'OK' if ok else '--'}] {line_id + '.mp3/.ogg/.wav':28s} \"{text}\"")
    print(f"\n{missing} falas ainda usam voz sintetizada.")


if __name__ == "__main__":
    main()
