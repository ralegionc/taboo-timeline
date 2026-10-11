"""Figures for the README. Reads only tables/, so it runs in seconds."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from words import BY_KEY, HANSARD_GROUP

OUT = Path("figures")
GROUP_COLOR = {"blasphemy": "#2a78d6", "profanity": "#eb6834", "sexual": "#1baf7a", "slur": "#4a3aa7",
               "insult": "#e34948", "control": "#8a8985"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
LABEL = {"nword": "n-word", "rword": "r-word"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "figure.dpi": 150, "savefig.bbox": "tight",
})


def label(k):
    return LABEL.get(k, BY_KEY[k].label if k in BY_KEY else k)


def pct_axis(ax, lo=1e-4, hi=0.6):
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    ticks = [1e-4, 1e-3, 1e-2, 1e-1]
    ax.set_yticks(ticks, ["0.01%", "0.1%", "1%", "10%"])
    ax.minorticks_off()


def fig_curves():
    """small multiples: masking rate per word, log scale, ordered by peak year."""
    r = pd.read_csv("tables/ngram_rates.csv")
    e = pd.read_csv("tables/ngram_events.csv").set_index("word")
    words = [w for w in e.sort_values("peak_year").index if e.loc[w, "datable"]]
    words.append("controls")
    n = len(words)
    cols = 4
    fig, axes = plt.subplots(int(np.ceil(n / cols)), cols, figsize=(11, 2.1 * np.ceil(n / cols)), sharex=True, sharey=True)
    for ax, w in zip(axes.flat, words):
        if w == "controls":
            for c in [k for k in e.index if e.loc[k, "group"] == "control"]:
                g = r[r.word == c]
                ax.plot(g.year, g.rate.clip(lower=1.1e-4), color=GROUP_COLOR["control"], lw=1.2)
            ax.set_title("4 never-taboo insults (controls)", loc="left", fontsize=9, color=INK)
        else:
            g = r[r.word == w]
            col = GROUP_COLOR[e.loc[w, "group"]]
            ax.fill_between(g.year, g.lo.clip(lower=1.1e-4), g.hi.clip(lower=1.1e-4), color=col, alpha=0.18, lw=0)
            ax.plot(g.year, g.rate.clip(lower=1.1e-4), color=col, lw=2)
            ax.set_title(label(w), loc="left", fontsize=9, color=INK)
        pct_axis(ax)
        ax.set_xlim(1800, 2018)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.suptitle("Share of uses printed masked (\"d--n\", \"f---ing\") inside fixed idioms, Google Books, 11-year window",
                 x=0.01, ha="left", fontsize=10, color=INK)
    handles = [plt.Line2D([], [], color=c, lw=2, label=g) for g, c in GROUP_COLOR.items() if g not in ("insult", "slur")]
    fig.legend(handles=handles, loc="lower right", ncol=5, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(OUT / "fig1_masking_curves.png")
    plt.close(fig)


def euphemism_span(g):
    """years where the euphemism share is at least half its 2009-2018 level."""
    s = g.set_index("year").share
    target = s.loc[2009:].mean() / 2
    above = s[s >= target]
    return int(above.index.min()) if len(above) else None


def fig_timeline():
    """one row per word: the span where masking sat at half its peak or more, plus the euphemism era."""
    e = pd.read_csv("tables/ngram_events.csv")
    e = e[e.datable].sort_values("peak_year")
    eu = pd.read_csv("tables/euphemism_shares.csv")
    fig, ax = plt.subplots(figsize=(10, 0.5 * (len(e) + 3) + 0.8))
    rows = []
    for _, x in e.iterrows():
        note = f"masked {x.peak:.0%} at peak" + ("; already high in 1800, when the data start" if x.open_start else "")
        rows.append((label(x.word), GROUP_COLOR[x.group], x.rise, x.fall, x.peak_year,
                     (x.rise_lo, x.rise_hi), (x.fall_lo, x.fall_hi), note))
    for w in ("nword",):
        g = eu[eu.word == w]
        start = euphemism_span(g)
        share = g.set_index("year").share.loc[2009:].mean()
        rows.append((f"{label(w)} (euphemism)", GROUP_COLOR["slur"], start, 2018, None, None, None,
                     f"\"the {label(w)}\" {share:.1%} of mentions, 2009-18"))
    for i, (name, col, a, b, pk, rci, fci, note) in enumerate(rows):
        y = len(rows) - i
        if rci:
            ax.plot(rci, [y, y], color=col, lw=1, alpha=0.6)
            ax.plot(fci, [y, y], color=col, lw=1, alpha=0.6)
        ax.barh(y, b - a, left=a, height=0.42, color=col, alpha=0.85)
        if pk:
            ax.plot(pk, y, "o", color="white", ms=5, mec=col, mew=1.5)
        ax.text(b + 2, y, note, va="center", fontsize=7.5, color=MUTED)
    ax.set_yticks(range(len(rows), 0, -1), [r[0] for r in rows])
    ax.set_xlim(1795, 2085)
    ax.set_xticks(range(1800, 2021, 20))
    ax.grid(axis="y", visible=False)
    ax.set_title("When each word was taboo in print: years at half its peak masking or more (dot = peak, "
                 "thin lines = 95% intervals)", loc="left", fontsize=9.5, color=INK)
    fig.savefig(OUT / "fig2_timeline.png")
    plt.close(fig)


def fig_euphemism():
    """the n-word: share of mentions made as "the n-word" in books, and masked or euphemised in the Commons."""
    eu = pd.read_csv("tables/euphemism_shares.csv")
    g = eu[(eu.word == "nword") & (eu.year >= 1960)]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    col = GROUP_COLOR["slur"]
    ax.fill_between(g.year, g.lo.clip(lower=1e-4), g.hi.clip(lower=1e-4), color=col, alpha=0.15, lw=0)
    ax.plot(g.year, g.share.clip(lower=1e-4), color=col, lw=2, label="books: \"the n-word\" / all mentions (11-year window)")
    p = Path("tables/hansard_decades.csv")
    if p.exists():
        h = pd.read_csv(p)
        h = h[h.word == "nword"]
        mid = {e: (int(e[:4]) + int(e[5:])) / 2 for e in h.era}
        share = (h.masked + h.euphemism) / h.uses
        ax.plot([mid[e] for e in h.era], share.clip(lower=1.2e-4), "s", color=INK, ms=6,
                label="Commons: masked or \"the n-word\" / all uses, by era")
        for e, v, n in zip(h.era, share, h.uses):
            if mid[e] >= 1960:
                ax.annotate(f"{v:.0%} of {n} uses", (mid[e], max(v, 1.2e-4)), textcoords="offset points", xytext=(6, 6), fontsize=7.5,
                            color=MUTED)
    ax.set_xlim(1960, 2026)
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 1.5)
    ax.set_yticks([1e-4, 1e-3, 1e-2, 1e-1, 1], ["0.01% or 0", "0.1%", "1%", "10%", "100%"])
    ax.minorticks_off()
    ax.set_ylabel("share of mentions")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("The n-word: taboo rising, shown as talking around the word", loc="left", fontsize=9.5, color=INK)
    fig.savefig(OUT / "fig3_nword.png")
    plt.close(fig)


def fig_hansard():
    p = Path("tables/hansard_decades.csv")
    if not p.exists():
        return
    h = pd.read_csv(p)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    # left: challenge lift by word, pooled over the whole period
    w = pd.read_csv("tables/hansard_words.csv")
    w = w[w.uses >= 50].sort_values("lift")
    ax = axes[0]
    y = np.arange(len(w))
    ax.errorbar(w.lift, y, xerr=[w.lift - w.lift_lo, w.lift_hi - w.lift], fmt="none", ecolor=GRID, elinewidth=3)
    cols = [GROUP_COLOR[HANSARD_GROUP[k]] for k in w.word]
    ax.scatter(w.lift.where(w.lift > 0), y, c=cols, s=30, zorder=3)
    zero = (w.lift == 0).to_numpy()
    ax.scatter(np.full(zero.sum(), 0.32), y[zero], facecolors="none", edgecolors=np.array(cols)[zero], s=30, zorder=3)
    for yy, (_, x) in zip(y[zero], w[zero].iterrows()):
        ax.text(0.38, yy, f"never, in {x.speeches:.0f} speeches", va="center", fontsize=7.5, color=MUTED)
    groups = [g for g in GROUP_COLOR if g in {HANSARD_GROUP[k] for k in w.word}]
    ax.legend(handles=[plt.Line2D([], [], marker="o", lw=0, color=GROUP_COLOR[g], label=g) for g in groups],
              frameon=False, fontsize=8, loc="lower right")
    ax.set_yticks(y, [label(k) for k in w.word])
    ax.set_xscale("log")
    ax.set_xlim(0.28, 400)
    ax.axvline(1, color=MUTED, lw=0.8)
    ax.set_xlabel("how much likelier the Chair challenges the language within 3 speeches (x baseline)")
    ax.set_title("Commons, 1919-2026: which words get challenged", loc="left", fontsize=9.5)
    # right: how the Chair's reaction to each kind of word changed
    ax = axes[1]
    p = pd.read_csv("tables/hansard_pools.csv")
    colors = {"swearing": GROUP_COLOR["profanity"], "accusation": GROUP_COLOR["insult"]}
    eras = sorted(p.era.unique())
    x = {e: i for i, e in enumerate(eras)}
    for k, g in p.groupby("pool"):
        off = -0.06 if k == "swearing" else 0.06
        xs = [x[e] + off for e in g.era]
        lo = (g.lift - g.lift_lo).clip(lower=0)
        ax.errorbar(xs, g.lift.clip(lower=0.5), yerr=[lo.where(g.lift > 0, 0), g.lift_hi - g.lift], fmt="o-",
                    color=colors[k], ms=5, lw=2, capsize=0, elinewidth=1, label=k)
    ax.set_yscale("log")
    ax.set_xticks(range(len(eras)), eras)
    ax.set_ylabel("challenge lift (x baseline)")
    ax.legend(frameon=False, fontsize=8, title=None)
    ax.set_title("Swearing stopped drawing the Chair; accusations did not", loc="left", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_hansard.png")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    fig_curves()
    fig_timeline()
    fig_euphemism()
    fig_hansard()
    return 0


if __name__ == "__main__":
    sys.exit(main())
