"""Draw a stable sample of Hansard hits for checking by hand.

Two samples, both chosen by a hash of the hit so they do not move when data is added:
  * up to 10 hits per word: is this really the word (not OCR, not another word)?
  * up to 60 challenged hits: was the Chair's challenge about this word?
Verdicts are filled in by hand in the "verdict" column (y / n) and read back by report.py.
Existing verdicts are kept when the file is rewritten.
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

OUT = Path("tables/check_hansard.csv")


def h(s):
    return hashlib.sha1(s.encode()).hexdigest()


def main():
    hits = pd.read_csv("data/hansard_hits.csv", keep_default_na=False)
    hits = hits[hits.word != ""].copy()
    hits["key"] = (hits.speech_id + "|" + hits.word + "|" + hits.match).map(h)
    hits = hits.drop_duplicates("key").sort_values("key")
    use = hits.groupby("word").head(10).assign(check="is the word")
    chal = (hits[hits.challenged].drop_duplicates(["speech_id", "word"]).head(60)
            .assign(check="challenge about the word"))
    s = pd.concat([use, chal])[["check", "key", "date", "word", "kind", "match", "context", "chair_said"]]
    s["verdict"] = ""
    if OUT.exists():
        old = pd.read_csv(OUT, keep_default_na=False).set_index(["check", "key"]).verdict
        s["verdict"] = [old.get((c, k), "") for c, k in zip(s.check, s.key)]
    s.to_csv(OUT, index=False)
    print(f"{len(s)} rows, {(s.verdict == '').sum()} without a verdict -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
