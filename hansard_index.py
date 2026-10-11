"""Taboo in the Commons: how often each word is said, masked, and challenged by the Chair.

Challenge lift compares speeches that use a word with all ordinary speeches of the same era:
observed = speeches using the word that are followed by a Chair challenge within 3 speeches;
expected = the same count if those speeches were challenged at their era's baseline rate.
Lift = observed / expected, with an exact Poisson interval on the observed count.

Writes tables/hansard_words.csv (whole period) and tables/hansard_decades.csv (by era).
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2

from words import HANSARD, HANSARD_GROUP

# Words with enough challenges to follow over time, pooled into the two kinds of taboo the Chair polices.
POOLS = {"swearing": ["damn", "bloody", "hell"], "accusation": ["liar", "hypocrite", "coward", "traitor"]}
ERAS = [(1919, 1939), (1940, 1959), (1960, 1979), (1980, 1999), (2000, 2026)]


def era_of(year):
    for a, b in ERAS:
        if a <= year <= b:
            return f"{a}-{b}"
    return None


def poisson_ci(k, alpha=0.05):
    lo = chi2.ppf(alpha / 2, 2 * k) / 2 if k > 0 else 0.0
    hi = chi2.ppf(1 - alpha / 2, 2 * k + 2) / 2
    return lo, hi


# Hits read by hand and found not to be the word (OCR, a name, "Nationalisation is the N-word").
# Every n-word euphemism hit was read; the rest come from the sample in tables/check_hansard.csv.
EXCLUDE = {("1991-06-13", "nword", "the N-word")}


def load():
    h = pd.read_csv("data/hansard_hits.csv", keep_default_na=False)
    try:
        c = pd.read_csv("tables/check_hansard.csv", keep_default_na=False)
        bad = c[(c.check == "is the word") & (c.verdict == "n")]
        drop = set(zip(bad.date, bad.word, bad.match)) | EXCLUDE
    except FileNotFoundError:
        drop = EXCLUDE
    keep = [(d, w, m) not in drop for d, w, m in zip(h.date, h.word, h.match)]
    print(f"dropped {len(h) - sum(keep)} hits judged false by hand")
    h = h[keep]
    days = pd.read_csv("data/hansard_days.csv")
    for d in (h, days):
        d["year"] = d.date.str[:4].astype(int)
        d["era"] = d.year.map(era_of)
    return h, days


def baseline(days):
    g = days.groupby("era")[["ordinary", "ordinary_followed", "words"]].sum()
    g["p0"] = g.ordinary_followed / g.ordinary
    return g


def lift_table(h, base, by):
    """speech-level challenge counts per group in `by`, with era-standardised expectation."""
    speech = (h[h.kind.isin(["full", "masked", "euphemism"])]
              .drop_duplicates(["date", "speech", "word"]))
    speech = speech.assign(expected=speech.era.map(base.p0))
    g = speech.groupby(by).agg(speeches=("challenged", "size"), challenged=("challenged", "sum"),
                               expected=("expected", "sum")).reset_index()
    g["lift"] = g.challenged / g.expected
    ci = [poisson_ci(k) for k in g.challenged]
    g["lift_lo"] = [a / e for (a, _), e in zip(ci, g.expected)]
    g["lift_hi"] = [b / e for (_, b), e in zip(ci, g.expected)]
    return g


def main():
    h, days = load()
    h = h[h.word != ""]
    base = baseline(days)
    print("baseline: share of ordinary speeches followed by a Chair challenge within 3 speeches")
    print((base.p0 * 100).round(3).to_string(), "\n")

    counts = h.pivot_table(index=["word", "era"], columns="kind", values="date", aggfunc="size",
                           fill_value=0).reset_index()
    for k in ("full", "masked", "euphemism"):
        if k not in counts:
            counts[k] = 0
    counts["uses"] = counts.full + counts.masked + counts.euphemism
    counts["uses_per_million"] = counts.uses / counts.era.map(base.words) * 1e6
    counts["masked_share"] = counts.masked / counts.uses.where(counts.uses > 0)
    counts["group"] = counts.word.map(HANSARD_GROUP)
    by_era = counts.merge(lift_table(h, base, ["word", "era"]), on=["word", "era"], how="left")
    by_era.to_csv("tables/hansard_decades.csv", index=False)

    tot = counts.groupby("word")[["full", "masked", "euphemism", "uses"]].sum().reset_index()
    words = tot.merge(lift_table(h, base, ["word"]), on="word", how="left")
    words["group"] = words.word.map(HANSARD_GROUP)
    words = words.sort_values("lift", ascending=False)
    words.to_csv("tables/hansard_words.csv", index=False)
    pd.set_option("display.width", 200)
    print(words[["word", "group", "uses", "masked", "euphemism", "speeches", "challenged", "expected",
                 "lift", "lift_lo", "lift_hi"]].round(2).to_string(index=False))
    pool = {w: p for p, ws in POOLS.items() for w in ws}
    # a speech saying both "damn" and "bloody" counts once for its pool
    hp = h[h.word.isin(pool)].assign(pool=lambda x: x.word.map(pool), word=lambda x: x.word.map(pool))
    pools = lift_table(hp, base, ["pool", "era"])
    pools.to_csv("tables/hansard_pools.csv", index=False)
    print("\nchallenge lift by era, pooled:")
    print(pools.pivot(index="pool", columns="era", values="lift").round(1).to_string())
    missing = set(HANSARD) - set(words.word)
    if missing:
        print("no hits:", sorted(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
