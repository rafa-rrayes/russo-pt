#!/usr/bin/env python3
"""
russo_pt.py - converte texto russo (cirílico) em sílabas que um falante de
português consegue ler em voz alta e que soam próximas do russo.

Uso:
    python russo_pt.py "Москва́ спаси́бо"     # texto direto
    python russo_pt.py -f texto.txt           # arquivo
    echo "хорошо́" | python russo_pt.py       # entrada padrão
    python russo_pt.py                        # modo interativo

Sílaba tônica:
    O russo escrito normalmente não marca a tônica, mas ela muda o som das
    vogais (o "o" fraco vira "a", o "e" fraco vira "i"...). Marque a vogal
    tônica com acento agudo (а́) ou com + logo depois dela (спаси+бо).
    Palavras de uma sílaba e palavras com ё já são reconhecidas sozinhas.
    Sem marca, a palavra sai sem redução de vogais: dá para entender,
    mas soa menos natural.

Como ler o resultado:
    MAIÚSCULAS  sílaba tônica, com acento na vogal (sa-IÚS)
    rr          "r" raspado de garganta, como o "r" carioca de "rato" (х)
    r           "r" batido de "caro", sempre, mesmo no começo da palavra
    y           "i" com a língua puxada para trás (ы)
    lh, nh      "l" e "n" suaves (ль, нь), como em "olho" e "ninho"
    ch / chch   "ch" de "chá" (ш) / "ch" mais longo e chiado (щ)
    tch, ts     como em "tchau" (ч) e "tsunami" (ц)
    ss          sempre "s" de "sapo", nunca "z"
"""

import argparse
import re
import sys

ACUTE = "́"
VOWELS = set("аеёиоуыэюя")
SIGNS = set("ьъ")
VOICED_TO_VOICELESS = {"б": "п", "в": "ф", "г": "к", "д": "т", "ж": "ш", "з": "с"}
VOICELESS_TO_VOICED = {"п": "б", "ф": "в", "к": "г", "т": "д", "ш": "ж", "с": "з"}
VOICELESS = set("пфктшсхцчщ")
VOICING_TRIGGERS = set("бгджз")  # "в" não sonoriza a consoante anterior
HARD_SIBILANTS = set("жшц")
OBSTRUENTS = set("бпвфгкдт")
PT_VOWELS = set("aeiouyéAEIOUYÉ")

CONSONANTS = {
    "б": "b", "в": "v", "г": "g", "д": "d", "ж": "j", "з": "z", "й": "i",
    "к": "k", "л": "l", "м": "m", "н": "n", "п": "p", "р": "r", "с": "s",
    "т": "t", "ф": "f", "х": "rr", "ц": "ts", "ч": "tch", "ш": "ch",
    "щ": "chch", "ь": "", "ъ": "",
}

# Grupos em que uma letra não é pronunciada ou o som muda.
CLUSTER_RULES = [
    ("вств", "ств"),  # здравствуйте: o primeiro в é mudo
    ("стн", "сн"),    # честно
    ("здн", "зн"),    # поздно
    ("лнц", "нц"),    # солнце
    ("стл", "сл"),    # счастливый
    ("сч", "щ"),      # счастье
    ("зч", "щ"),
    ("ться", "ца"),   # учиться
    ("тся", "ца"),    # учится
]

# Palavras com pronúncia irregular.
WORD_RULES = {"что": "што", "чтобы": "штобы", "ничто": "ништо"}

# No genitivo -ого/-его o г soa como в; estas palavras são exceções.
GENITIVE_EXCEPTIONS = {"много", "немного", "строго", "дорого", "убого"}
SHORT_GENITIVES = {"его", "него", "кого", "того", "чего", "сего"}

WORD_RE = re.compile(r"[а-яёА-ЯЁ́+]+")


def parse_word(raw):
    """Separa letras e marcas de tônica: lista de [letra, é_tônica]."""
    letters = []
    for ch in raw.lower():
        if ch in (ACUTE, "+"):
            if letters and letters[-1][0] in VOWELS:
                letters[-1][1] = True
        else:
            letters.append([ch, ch == "ё"])
    return letters


def text_of(letters):
    return "".join(c for c, _ in letters)


def replace_all(letters, old, new):
    """Substitui uma sequência de letras, levando a tônica junto."""
    out, i = [], 0
    while i < len(letters):
        segment = letters[i:i + len(old)]
        if text_of(segment) == old:
            flags = [False] * len(new)
            if any(f for _, f in segment):
                for k in range(len(new) - 1, -1, -1):
                    if new[k] in VOWELS:
                        flags[k] = True
                        break
            out.extend([c, f] for c, f in zip(new, flags))
            i += len(old)
        else:
            out.append(letters[i])
            i += 1
    return out


def apply_spelling_rules(letters):
    word = text_of(letters)
    if word in WORD_RULES:
        letters = replace_all(letters, word, WORD_RULES[word])
    for old, new in CLUSTER_RULES:
        letters = replace_all(letters, old, new)
    word = text_of(letters)
    if (word.endswith(("ого", "его")) and word not in GENITIVE_EXCEPTIONS
            and (len(word) >= 5 or word in SHORT_GENITIVES)):
        letters[-2][0] = "в"
    return letters


def next_real_letter(letters, i):
    """Próxima letra depois de i, pulando ь/ъ. None = fim da palavra."""
    j = i + 1
    while j < len(letters) and letters[j][0] in SIGNS:
        j += 1
    return letters[j][0] if j < len(letters) else None


def assimilate(letters):
    """Ensurdece no fim da palavra e antes de surdas; sonoriza antes de sonoras."""
    if not any(c in VOWELS for c, _ in letters):
        return  # preposições como в, к, с se juntam à palavra seguinte
    for i in range(len(letters) - 1, -1, -1):
        c = letters[i][0]
        nxt = next_real_letter(letters, i)
        if c in VOICED_TO_VOICELESS and (nxt is None or nxt in VOICELESS):
            letters[i][0] = VOICED_TO_VOICELESS[c]
        elif c in VOICELESS_TO_VOICED and nxt in VOICING_TRIGGERS:
            letters[i][0] = VOICELESS_TO_VOICED[c]


def find_stress(letters):
    marked = [i for i, (_, f) in enumerate(letters) if f]
    if marked:
        return marked[0]
    vowels = [i for i, (c, _) in enumerate(letters) if c in VOWELS]
    return vowels[0] if len(vowels) == 1 else None


def render_vowel(letters, i, stress):
    c = letters[i][0]
    prev = letters[i - 1][0] if i > 0 else None
    unstressed = stress is not None and i != stress
    iotated = prev is None or prev in VOWELS or prev in SIGNS
    last = i == len(letters) - 1

    if c == "а":
        return "i" if unstressed and prev in ("ч", "щ") else "a"
    if c == "о":
        return "a" if unstressed else "o"
    if c == "у":
        return "u"
    if c == "ы":
        return "y"
    if c == "э":
        return "e"
    if c == "и":
        return "y" if prev in HARD_SIBILANTS else "i"
    if c == "е":
        if prev in HARD_SIBILANTS:
            return "y" if unstressed else "e"
        if unstressed:
            return "ie" if iotated and last and prev is not None else "i"
        return "ie"
    if c == "ё":
        return "o" if prev in ("ж", "ш", "ч", "щ") else "io"
    if c == "я":
        return "i" if unstressed and not last else "ia"
    if c == "ю":
        return "u" if prev in ("ж", "ш") else "iu"
    return c


def render_pieces(letters, stress):
    pieces = []
    for i, (c, _) in enumerate(letters):
        if c in VOWELS:
            pieces.append(render_vowel(letters, i, stress))
        else:
            pieces.append(CONSONANTS.get(c, c))

    def next_piece(i):
        for p in pieces[i + 1:]:
            if p:
                return p
        return ""

    for i, (c, _) in enumerate(letters):
        nxt = next_piece(i)
        prev = pieces[i - 1] if i > 0 else ""
        if c == "г" and nxt[:1] in ("e", "i", "y", "é"):
            pieces[i] = "gu"  # para não virar "j" como em "gente"
        elif c == "с" and prev[-1:] in PT_VOWELS and nxt[:1] in PT_VOWELS:
            pieces[i] = "ss"  # para não virar "z" como em "casa"
        elif c == "ь" and i > 0 and letters[i - 1][0] in ("л", "н"):
            following = letters[i + 1][0] if i + 1 < len(letters) else None
            if following is None or following not in VOWELS:
                pieces[i - 1] = "lh" if letters[i - 1][0] == "л" else "nh"
    return pieces


ACCENTS = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}


def accent_vowel(piece):
    """Acentua a última vogal do som tônico: "iu" -> "iú" (y fica sem acento)."""
    for k in range(len(piece) - 1, -1, -1):
        if piece[k] in ACCENTS:
            return piece[:k] + ACCENTS[piece[k]] + piece[k + 1:]
    return piece


def syllable_starts(letters):
    vowels = [i for i, (c, _) in enumerate(letters) if c in VOWELS]
    starts = [0]
    for a, b in zip(vowels, vowels[1:]):
        cons = list(range(a + 1, b))
        real = [k for k in cons if letters[k][0] not in SIGNS]
        if not cons:
            cut = b
        elif letters[cons[0]][0] == "й":
            cut = cons[0] + 1
        elif len(real) <= 1:
            cut = real[0] if real else b
        elif letters[real[-1]][0] in "рл" and letters[real[-2]][0] in OBSTRUENTS:
            cut = real[-2]  # "pu-blik", "si-stra": consoante + r/l ficam juntas
        else:
            cut = cons[0] + 1
            while cut < b and letters[cut][0] in SIGNS:
                cut += 1
        starts.append(cut)
    return starts


def convert_word(raw):
    if not re.search(r"[а-яёА-ЯЁ]", raw):
        return raw
    letters = apply_spelling_rules(parse_word(raw))
    assimilate(letters)
    stress = find_stress(letters)
    pieces = render_pieces(letters, stress)
    starts = syllable_starts(letters)
    if stress is not None and len(starts) > 1:
        pieces[stress] = accent_vowel(pieces[stress])
    ends = starts[1:] + [len(letters)]

    syllables = []
    for s, e in zip(starts, ends):
        text = "".join(pieces[s:e])
        if stress is not None and len(starts) > 1 and s <= stress < e:
            text = text.upper()
        if text:
            syllables.append(text)
    return "-".join(syllables)


def convert_text(text):
    return WORD_RE.sub(lambda m: convert_word(m.group()), text)


def main():
    parser = argparse.ArgumentParser(
        description="Converte russo em sílabas legíveis em português.")
    parser.add_argument("texto", nargs="*", help="texto em russo")
    parser.add_argument("-f", "--arquivo", help="arquivo de texto em russo")
    args = parser.parse_args()

    if args.texto:
        print(convert_text(" ".join(args.texto)))
    elif args.arquivo:
        with open(args.arquivo, encoding="utf-8") as fh:
            for line in fh:
                print(convert_text(line.rstrip("\n")))
    elif not sys.stdin.isatty():
        for line in sys.stdin:
            print(convert_text(line.rstrip("\n")))
    else:
        print("Digite texto em russo (marque a tônica com ´ ou +). Ctrl+C para sair.")
        try:
            while True:
                print("  " + convert_text(input("> ")))
        except (KeyboardInterrupt, EOFError):
            print()


if __name__ == "__main__":
    main()
