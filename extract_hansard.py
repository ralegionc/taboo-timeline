"""One pass over every Commons speech: word hits, masked hits, euphemisms, and Chair challenges.

A speech by the Chair (Speaker, Deputy Speaker, Chairman of Ways and Means and so on) that calls
language unparliamentary or asks for something to be withdrawn is a challenge. A word hit is
"challenged" if a challenge comes in the same day within the next three speeches.

Writes data/hansard_hits.csv (one row per hit, with context) and data/hansard_days.csv (words,
speeches, and the baseline: how many ordinary speeches were followed by a challenge).
"""
import gzip
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from words import HANSARD, HANSARD_EUPHEMISM, resolve_mask

PARTS = Path("data/hansard/parts")
AHEAD = 3

FORM_TO_KEY = {f: k for k, forms in HANSARD.items() for f in forms}
FULL = re.compile(r"\b(" + "|".join(sorted(FORM_TO_KEY, key=len, reverse=True)) + r")\b", re.I)
MASK = re.compile(r"(?<![\w*\-—–'’.])([a-z]{1,3}(?:\*+|[-—–]{2,}|[—–])[a-z]{0,6})(?![\w*\-—–])", re.I)
EUPH = re.compile(r"\bthe (n)[-‐‑–]word\b", re.I)
CHAIR = re.compile(r"speaker|chairman|chairwoman|\bchair\b|deputy speaker", re.I)
# Procedural things a Chair asks to have withdrawn; a "withdraw" next to one of these is not a challenge.
PROCEDURAL = (r"amendment|motion|clause|schedule|bill|application|prayer|question|instruction|objection|"
              r"petition|proposal|nomination|request|notice")
CHALLENGE = re.compile(
    r"unparliamentary|"
    r"\bwithdraw\b(?! quietly| its| their| a name)(?![^.?!]{0,50}\b(?:" + PROCEDURAL + r")s?\b)|"
    r"\b(?:coarse|offensive|intemperate|immoderate|unacceptable|inappropriate|disorderly|abusive|insulting|"
    r"unseemly|foul|bad|strong) (?:language|word|words|expression|expressions|remark|remarks|term|terms)\b|"
    r"\b(?:language|word|words|expression|remark|remarks|term)\b[^.?!]{0,50}\b(?:unacceptable|not acceptable|"
    r"inappropriate|not appropriate|distasteful|offensive|not in order|out of order|not parliamentary)|"
    r"\bwords? like that\b|\bthat (?:sort|kind) of (?:language|remark|expression|comment)\b|\brephrase\b|"
    r"\b(?:accuse|accusing|call|calling)\b[^.?!]{0,50}\b(?:of lying|a liar|liars|dishonest|hypocri\w*|"
    r"coward\w*|traitor\w*)|"
    r"\bnot (?:be )?(?:a )?(?:legitimate|proper|parliamentary|in order) (?:to |for \w+ to )?(?:make|accuse|call|describe|"
    r"suggest|impute|use|refer)\b|"
    r"\bhypocritical\b[^.?!]{0,60}\bnot (?:individual |hon\. )?(?:Members|Member|Gentlemen|Gentleman|Ladies|Lady)\b",
    re.I)


def context(text, a, b, width=90):
    return text[max(0, a - width):b + width].replace("\t", " ").replace("\n", " ")


def process(path):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 4:
                rows.append(parts)
    date = path.name[:10]
    chair = [bool(CHAIR.search(r[2])) for r in rows]
    challenge = [c and bool(CHALLENGE.search(r[3])) for c, r in zip(chair, rows)]
    followed = [any(challenge[i + 1:i + 1 + AHEAD]) for i in range(len(rows))]
    # the Chair's words, kept for checking by hand whether the challenge was about this word
    said = ["" if not followed[i] else
            next(rows[j][3][:300] for j in range(i + 1, min(i + 1 + AHEAD, len(rows))) if challenge[j])
            for i in range(len(rows))]

    hits = []
    for i, (_, sid, who, text) in enumerate(rows):
        if chair[i]:
            continue  # the Chair quoting a word back is not a use of it
        for m in FULL.finditer(text):
            hits.append((date, i, sid, FORM_TO_KEY[m.group(1).lower()], "full", m.group(1), followed[i],
                         context(text, m.start(), m.end()), said[i]))
        for m in MASK.finditer(text):
            key = resolve_mask(m.group(1))
            if key:
                hits.append((date, i, sid, key, "masked", m.group(1), followed[i],
                             context(text, m.start(), m.end()), said[i]))
            elif "**" in m.group(1):
                hits.append((date, i, sid, "", "masked_ambiguous", m.group(1), followed[i],
                             context(text, m.start(), m.end()), said[i]))
        for m in EUPH.finditer(text):
            hits.append((date, i, sid, HANSARD_EUPHEMISM[m.group(1).lower()], "euphemism", m.group(0), followed[i],
                         context(text, m.start(), m.end()), said[i]))
    ordinary = [i for i in range(len(rows)) if not chair[i]]
    day = dict(date=date, words=sum(len(r[3].split()) for r in rows), speeches=len(rows),
               ordinary=len(ordinary), ordinary_followed=sum(followed[i] for i in ordinary),
               challenges=sum(challenge), expletive=sum(r[3].lower().count("expletive") for r in rows))
    return day, hits


def main():
    paths = sorted(PARTS.glob("*.tsv.gz"))
    days, hits = [], []
    with Pool() as pool:
        for n, (day, h) in enumerate(pool.imap_unordered(process, paths, chunksize=20), 1):
            days.append(day)
            hits += h
            if n % 2000 == 0:
                print(f"{n}/{len(paths)}", flush=True)
    cols = ["date", "speech", "speech_id", "word", "kind", "match", "challenged", "context", "chair_said"]
    pd.DataFrame(hits, columns=cols).sort_values(["date", "speech"]).to_csv("data/hansard_hits.csv", index=False)
    pd.DataFrame(days).sort_values("date").to_csv("data/hansard_days.csv", index=False)
    print(f"{len(paths)} days, {len(hits)} hits", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
