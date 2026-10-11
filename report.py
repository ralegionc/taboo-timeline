"""Print every number the README quotes, from tables/ only."""
import sys

import pandas as pd

from words import BY_KEY

LABEL = {"nword": "n-word", "rword": "r-word"}


def lab(k):
    return LABEL.get(k, BY_KEY[k].label if k in BY_KEY else k)


def books():
    e = pd.read_csv("tables/ngram_events.csv")
    print("## Books: masking inside fixed idioms (Google Books, 1800-2018)\n")
    ctl = e[e.group == "control"]
    print(f"Controls (never-taboo insults), highest masking rate in any window: {ctl.peak.max():.3%}\n")
    print("| word | peak masking | 95% CI | peak year | 95% CI | taboo span (half peak or more) | 2009-18 | fall from peak |")
    print("|---|---|---|---|---|---|---|---|")
    for _, x in e[e.datable].sort_values("peak_year").iterrows():
        fall = x.peak / x.recent if x.recent > 0 else float("inf")
        print(f"| {lab(x.word)} | {x.peak:.1%} | {x.peak_lo:.1%} to {x.peak_hi:.1%} | {int(x.peak_year)} | "
              f"{int(x.peak_year_lo)} to {int(x.peak_year_hi)} | {int(x.rise)} to {int(x.fall)} | {x.recent:.2%} | "
              f"{fall:.0f}x |")
    rare = e[(~e.datable) & (e.group != "control")]
    print("\nToo few masked uses to date (masked total, approximate occurrences): "
          + ", ".join(f"{lab(w)} {m:.0f}" for w, m in zip(rare.word, rare.masked_total)))

    s = pd.read_csv("tables/sensitivity.csv").drop_duplicates("variant")
    print(f"\nSensitivity: wave order holds in {s.waves_in_order.sum()} of {len(s)} variants, "
          f"tenfold fall in {s.all_fell_tenfold.sum()} of {len(s)}")

    u = pd.read_csv("tables/euphemism_shares.csv").set_index(["word", "year"]).share
    print("\nEuphemism share (\"the x-word\" / all mentions), 11-year window:")
    for y in (1960, 1975, 1985, 1990, 2000, 2013):
        print(f"  n-word {y}: {u[('nword', y)]:.2%}")


def hansard():
    try:
        w = pd.read_csv("tables/hansard_words.csv")
        d = pd.read_csv("tables/hansard_decades.csv")
        days = pd.read_csv("data/hansard_days.csv")
    except FileNotFoundError:
        return
    print("\n## Commons (Hansard, 1919-2026)\n")
    print(f"{len(days)} sitting days, {days.words.sum() / 1e6:.0f} million words, "
          f"{days.challenges.sum()} Chair challenges")
    print("\n| word | group | uses | masked | \"the x-word\" | challenged | expected | lift | 95% CI |")
    print("|---|---|---|---|---|---|---|---|---|")
    for _, x in w.sort_values("lift", ascending=False).iterrows():
        print(f"| {lab(x.word)} | {x.group} | {x.uses:.0f} | {x.masked:.0f} | {x.euphemism:.0f} | {x.challenged:.0f} | "
              f"{x.expected:.1f} | {x.lift:.1f} | {x.lift_lo:.1f} to {x.lift_hi:.1f} |")
    print("\nUses per million words, by era:")
    t = d.pivot_table(index="word", columns="era", values="uses_per_million").fillna(0)
    print(t.round(2).to_string())
    print("\nChallenge lift by era (words with 10+ challenged speeches overall):")
    keep = w[w.challenged >= 10].word
    t = d[d.word.isin(keep)].pivot_table(index="word", columns="era", values="lift")
    print(t.round(1).to_string())
    print("\nMasked or euphemised share of uses, by era:")
    d["hidden"] = (d.masked + d.euphemism) / d.uses
    t = d[d.uses >= 5].pivot_table(index="word", columns="era", values="hidden")
    print((t * 100).round(1).to_string())


def checks():
    try:
        c = pd.read_csv("tables/check_hansard.csv", keep_default_na=False)
    except FileNotFoundError:
        return
    c = c[c.verdict != ""]
    print("\n## Hand checks\n")
    for k, g in c.groupby("check"):
        print(f"{k}: {(g.verdict == 'y').sum()} yes, {(g.verdict == 'n').sum()} no, "
              f"{(g.verdict == 'u').sum()} unclear, of {len(g)}")
        bad = g[g.verdict == "n"].word.value_counts()
        if len(bad):
            print("  no, by word: " + ", ".join(f"{lab(a)} {b}" for a, b in bad.items()))
    print("\nPooled challenge lift by era:")
    p = pd.read_csv("tables/hansard_pools.csv")
    for _, x in p.iterrows():
        print(f"  {x.pool:10s} {x.era}  {x.challenged:3.0f} of {x.speeches:4.0f} speeches  lift {x.lift:6.1f}"
              f"  ({x.lift_lo:.1f} to {x.lift_hi:.1f})")


def main():
    books()
    hansard()
    checks()
    return 0


if __name__ == "__main__":
    sys.exit(main())
