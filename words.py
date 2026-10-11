"""Every modelling choice about words: which words, which idioms they are counted in, how they get masked.

A word is counted only inside fixed idioms ("be damned", "what the hell"). Inside an idiom the
masked form ("be d--d") can only mean that word, which removes the hyphenated-notation noise
that swamps bare forms like "s-t" or "n-r".

Each frame is written with the word in braces: "be {damned}". The frame is queried as written
and with its first letter capitalised. Masks are built from the word's first and last letters
with one to four dashes, plus any extra masks listed for the word. A frame that ends on the
word can also pick up asterisk masks ("what the f***"), through a wildcard query.
"""
import re
from dataclasses import dataclass, field

DASH_RUNS = (1, 2, 3, 4)


@dataclass(frozen=True)
class Word:
    key: str                # file-safe id
    label: str              # how figures print it
    group: str              # profanity, blasphemy, sexual, slur, control
    forms: dict             # surface form -> extra masks for that form
    frames: tuple           # idioms with the form in braces
    trail: tuple = ()       # frames where a bare trailing mask ("be d--") is unambiguous
    note: str = ""


def W(key, label, group, forms, frames, trail=(), note=""):
    return Word(key, label, group, forms, tuple(frames), tuple(trail), note)


WORDS = [
    W("damn", "damn", "blasphemy",
      {"damn": [], "damned": ["d-mn-d", "d--n'd", "d-n'd", "d--ned", "d-ned"]},
      ["be {damned}", "{damned} fool", "{damned} thing", "God {damn}", "{damn} you", "{damn} it",
       "give a {damn}", "care a {damn}"],
      trail=["be {damned}", "God {damn}", "{damn} you", "{damn} it"]),
    W("hell", "hell", "blasphemy",
      {"hell": ["h-ll", "h--ll"]},
      ["what the {hell}", "go to {hell}", "{hell} of a", "the {hell} out", "the {hell} is"],
      trail=["what the {hell}", "go to {hell}"]),
    W("devil", "devil", "blasphemy",
      {"devil": ["d-v-l", "d-vil", "de-l", "de--l"]},
      ["what the {devil}", "go to the {devil}", "the {devil} take", "{devil} take it", "the {devil} you"],
      trail=["what the {devil}", "go to the {devil}"]),
    W("bloody", "bloody", "profanity",
      {"bloody": ["bl-dy", "bl--dy", "bl-y", "b-----y"]},
      ["{bloody} fool", "{bloody} well", "not {bloody} likely", "you {bloody}", "{bloody} idiot"],
      trail=["not {bloody} likely"]),
    W("bugger", "bugger", "sexual",
      {"bugger": ["b-gg-r", "b-gger", "bu--er"]},
      ["{bugger} off", "silly {bugger}", "poor {bugger}", "{bugger} it", "you {bugger}"]),
    W("bastard", "bastard", "profanity",
      {"bastard": ["b-st-rd", "b-stard", "b-----d"], "bastards": ["b-st-rds", "b-----s"]},
      ["you {bastard}", "poor {bastard}", "the {bastards}", "lucky {bastard}", "you {bastards}"]),
    W("bitch", "bitch", "profanity",
      {"bitch": ["b-tch", "bi-ch"]},
      ["son of a {bitch}", "you {bitch}", "little {bitch}", "{bitch} !"],
      trail=["son of a {bitch}"]),
    W("whore", "whore", "sexual",
      {"whore": ["wh-re", "wh--e", "w-h-re", "wh-e"]},
      ["a {whore}", "the {whore}", "son of a {whore}", "{whore} of Babylon", "common {whore}"],
      trail=["son of a {whore}", "common {whore}"]),
    W("piss", "piss", "profanity",
      {"piss": ["p-ss", "pi-s"], "pissed": ["p-ssed", "p--sed", "p-ss-d"]},
      ["{piss} off", "take the {piss}", "{pissed} off", "{piss} on"],
      trail=["take the {piss}"]),
    W("arse", "arse", "profanity",
      {"arse": ["a-se", "ar-e", "a**e"]},
      ["my {arse}", "your {arse}", "kiss my {arse}", "his {arse}", "up your {arse}"],
      trail=["kiss my {arse}", "up your {arse}"]),
    W("shit", "shit", "profanity",
      {"shit": ["sh-t", "sh--", "s**t", "sh*t"]},
      ["holy {shit}", "piece of {shit}", "the {shit} out", "give a {shit}", "full of {shit}"],
      trail=["holy {shit}", "piece of {shit}", "give a {shit}", "full of {shit}"]),
    W("fuck", "fuck", "sexual",
      {"fuck": ["f-ck", "f--k", "f**k", "f*ck", "f---"], "fucking": ["f-cking", "f--king", "f---ing", "f-ing", "f**king"]},
      ["what the {fuck}", "{fuck} you", "{fuck} off", "the {fucking}", "give a {fuck}", "{fucking} idiot"],
      trail=["what the {fuck}", "give a {fuck}"],
      note="before about 1820 'fuck' is mostly OCR of long-s 'suck'; frames keep this out"),
    W("cunt", "cunt", "sexual",
      {"cunt": ["c-nt", "c**t", "c*nt"]},
      ["you {cunt}", "the {cunt}", "stupid {cunt}", "a {cunt}"],
      trail=["you {cunt}", "stupid {cunt}"]),
    W("nword", "n-word", "slur",
      {"nigger": ["n-gger", "n--ger", "n-g-er", "n****r", "n*****"], "niggers": ["n-ggers", "n--gers"]},
      ["a {nigger}", "the {nigger}", "the {niggers}", "{nigger} in the woodpile", "damned {nigger}"],
      note="printed in full through the 19th century; included because it is the clearest case of taboo rising"),
    # Controls: insults that were never taboo, in idioms about as common as the swear frames.
    # Their masked forms should essentially never occur; whatever does is the background of
    # abbreviation, OCR and notation at these frequencies.
    W("ctl_rascal", "rascal (control)", "control",
      {"rascal": []}, ["you {rascal}", "the {rascal}", "a {rascal}", "young {rascal}"],
      trail=["you {rascal}"]),
    W("ctl_scoundrel", "scoundrel (control)", "control",
      {"scoundrel": []}, ["you {scoundrel}", "the {scoundrel}", "a {scoundrel}"],
      trail=["you {scoundrel}"]),
    W("ctl_villain", "villain (control)", "control",
      {"villain": []}, ["you {villain}", "the {villain}", "a {villain}"],
      trail=["you {villain}"]),
    W("ctl_fool", "fool (control)", "control",
      {"fool": []}, ["you {fool}", "a {fool}", "the {fool}", "old {fool}"]),
]

BY_KEY = {w.key: w for w in WORDS}

# Before these years the word's frames are dominated by OCR errors, not the word.
START = {"fuck": 1830}  # long s: "the sucking" read as "the fucking"


def dash_masks(form):
    """first letter, one to four dashes, last letter: damn -> d-n, d--n, d---n, d----n."""
    if len(form) < 3:
        return []
    return [form[0] + "-" * k + form[-1] for k in DASH_RUNS]


def trail_masks(form):
    """first letter then dashes only: damn -> d--, d---. Single dash is left out (initials)."""
    return [form[0] + "-" * k for k in (2, 3, 4)]


# After these words a single-hyphen "x-y" is mostly notation ("the n-s transition", "the s-l
# curve"), not a masked word. In such frames only longer masks count. Checked on the controls.
DETERMINERS = {"the", "a", "an", "his", "her", "my", "your", "their", "our"}


def notation_prone(frame):
    rest = re.sub(r"\{\w+\}", "", frame).split()
    return bool(rest) and all(t.lower() in DETERMINERS for t in rest)


def masks_for(form, extra, frame=""):
    out = []
    for m in dash_masks(form) + list(extra):
        if notation_prone(frame) and re.fullmatch(r"\w-\w", m):
            continue
        if "*" in m:
            continue  # asterisks cannot be queried directly; handled by wildcard frames
        if m not in out:
            out.append(m)
    return out


def capitalise(s):
    return s[:1].upper() + s[1:]


def norm(s):
    """the API's spelling of an n-gram: dash runs become separate tokens."""
    s = re.sub(r"(-+)", r" \1 ", s)
    s = re.sub(r"(\*+)", r" * ", s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class Query:
    word: str
    frame: str       # frame template with braces
    form: str
    kind: str        # full, dash, trail, star
    text: str        # what is sent to the API
    variants: list = field(default_factory=list)


def frame_forms(word, frame):
    m = re.search(r"\{(\w+)\}", frame)
    return m.group(1)


def queries(word):
    """every n-gram to fetch for one word, grouped by frame."""
    out = []
    for frame in word.frames:
        form = frame_forms(word, frame)
        extra = word.forms[form]
        fill = lambda x: frame.replace("{" + form + "}", x)
        out.append(Query(word.key, frame, form, "full", fill(form)))
        for m in masks_for(form, extra, frame):
            out.append(Query(word.key, frame, form, "dash", fill(m)))
        if frame in word.trail:
            for m in trail_masks(form):
                out.append(Query(word.key, frame, form, "trail", fill(m)))
        if frame in word.trail and frame.rstrip().endswith("{" + form + "}"):
            out.append(Query(word.key, frame, form, "star", fill(form[0] + " *")))
    for q in out:
        q.variants = [q.text] if q.kind == "star" else sorted({q.text, capitalise(q.text)})
    return out


def star_hit(query_text, ngram):
    """does a wildcard expansion fill the wildcard with an asterisk run, in the same letter case?

    "what the f *" -> "What the f *" counts (sentence start); "the N *" for "the n *" does not,
    because a capital after a lower-case word is notation, not a masked swear.
    """
    q = query_text.split()
    g = ngram.split()
    if len(q) != len(g) or g[-1].strip("*") != "":
        return False
    if g[-2] != q[-2]:
        return False  # the masked letter must keep its case
    return all(a.lower() == b.lower() for a, b in zip(q[:-2], g[:-2]))


# Euphemism channel. Late-20th-century taboo shows up as talking around the word ("the n-word")
# more than as masking it. Share = euphemism / (euphemism + the word's own forms), from 1-grams.
# Only the n-word is used. Hand checks of Hansard showed "the c-word" is mostly cancer, cuts,
# corruption or Christmas, "the r-word" recession or regionalism, "the f-word" federalism, and
# "the b-word" and "the s-word" point to several words; none of them can be read as the swear.
EUPHEMISMS = {
    "nword": (["the n-word", "The n-word", "the N-word", "The N-word"], ["nigger", "niggers", "Nigger", "Niggers"]),
}

# Hansard: every inflection counted, anywhere in a speech. Swears plus the insults the Chair
# has historically ruled out of order (Erskine May's list of unparliamentary terms).
HANSARD = {
    "damn": ["damn", "damned", "goddamn", "goddamned", "damnit"],
    "hell": ["hell"],
    "devil": ["devil", "devils"],
    "bloody": ["bloody"],
    "bugger": ["bugger", "buggers", "buggered", "buggery"],
    "bastard": ["bastard", "bastards"],
    "bitch": ["bitch", "bitches"],
    "piss": ["piss", "pissed", "pissing"],
    "arse": ["arse", "arses", "arsehole", "arseholes"],
    "shit": ["shit", "shits", "shitty", "bullshit"],
    "fuck": ["fuck", "fucking", "fucked", "fucker", "fuckers"],
    "cunt": ["cunt", "cunts"],
    "nword": ["nigger", "niggers"],
    "liar": ["liar", "liars"],
    "hypocrite": ["hypocrite", "hypocrites"],
    "coward": ["coward", "cowards"],
    "swine": ["swine"],
    "guttersnipe": ["guttersnipe", "guttersnipes"],
    "blackguard": ["blackguard", "blackguards"],
    "traitor": ["traitor", "traitors"],
    "git": ["git", "gits"],
    "scum": ["scum"],
    "idiot": ["idiot", "idiots"],
}
HANSARD_GROUP = {k: ("insult" if k in {"liar", "hypocrite", "coward", "swine", "guttersnipe", "blackguard",
                                         "traitor", "git", "scum", "idiot"} else
                     BY_KEY[k].group) for k in HANSARD}
HANSARD_EUPHEMISM = {"n": "nword"}  # see EUPHEMISMS for why the other letters are not used
# Left out of HANSARD after reading hits: "whore" is mostly OCR of "where", "cad" of "can",
# and "retard" is nearly always the verb.


# A dash followed by one of these is a sentence break ("the nation's—it is"), not a mask.
FUNCTION_TAILS = {"a", "an", "and", "as", "at", "be", "by", "he", "if", "in", "is", "it", "no", "of", "on",
                  "or", "so", "to", "we", "the", "but", "not", "was", "are"}


def resolve_mask(token):
    """which Hansard word a masked token stands for, or None if none or several fit.

    "b*****d" -> bastard (letters and length agree); "f***" -> fuck; "b***" -> None (bloody,
    bitch, bastard and bugger all fit). Dash masks carry no length (an em dash is one character
    for any number of letters), so they need a matching last letter instead.
    """
    m = re.fullmatch(r"([a-z]{1,3})(\*+|[-—–]{2,}|[—–])([a-z]{0,6})", token.lower())
    if not m:
        return None
    pre, run, suf = m.groups()
    star = run[0] == "*"
    if not star and suf in FUNCTION_TAILS:
        return None
    hits = set()
    for key, forms in HANSARD.items():
        for f in forms:
            if not f.startswith(pre) or not f.endswith(suf) or len(pre) + len(suf) >= len(f):
                continue
            if star and len(pre) + len(run) + len(suf) != len(f):
                continue
            if not star and not suf:
                continue  # "d--" is an interrupted word as often as a masked one
            hits.add(key)
    return hits.pop() if len(hits) == 1 else None
