"""Masking rate in books: how often each word is printed masked ("d--n") instead of in full.

For every word and year, the rate is masked / (masked + full), pooled over the word's frames
and an 11-year window. Frequencies are turned into approximate counts with the corpus's yearly
word totals, so a window needs about 30 occurrences before it gets a rate at all.

Two cleaning steps, both per frame:
  * one-year spikes are capped at 4x the local median plus 25 occurrences (Google files many
    undated modern books under 1890-1901, which puts "what the fuck" in 1901);
  * asterisk masks are left out (they only appear in the data from 2019, a tokenizer change),
    and the series ends in 2018.

Uncertainty: 1000 bootstrap draws, each resampling the word's frames with replacement and
redrawing every count from a Poisson. The same draws give intervals for the event years.

Writes tables/ngram_rates.csv and tables/ngram_events.csv.
"""
import sys

import numpy as np
import pandas as pd

from words import START, WORDS, queries

Y0, Y1 = 1800, 2018
HALF = 5            # window is year +- HALF, for the plotted curves
HALF_EVENTS = 10    # wider window for dating peaks and spans, which are fragile in thin years
MIN_SUPPORT = 100   # occurrences in a window before a rate is reported
MIN_MASKED = 500    # masked occurrences overall before a word's events are dated at all
SPIKE_MULT, SPIKE_FLOOR, SPIKE_HALF = 4.0, 25.0, 7
B = 1000
SEED = 7


def load():
    d = pd.read_csv("data/ngrams.csv")
    d = d[(d.kind != "star") & d.year.between(Y0, Y1)]
    allowed = {(q.word, v) for w in WORDS for q in queries(w) for v in q.variants}
    d = d[[(w, g) in allowed for w, g in zip(d.word, d.ngram)]]  # the cache may hold dropped masks
    tot = pd.read_csv("data/ngram_totals.csv").set_index("year").words
    d["count"] = d.freq * d.year.map(tot)
    d["masked"] = d.kind != "full"
    return d


def frame_matrix(d, word):
    """counts as arrays [frame, year] for full and masked forms, after spike capping."""
    years = np.arange(START.get(word, Y0), Y1 + 1)
    sub = d[(d.word == word) & d.year.isin(years)]
    frames = sorted(sub.frame.unique())
    out = {}
    for masked in (False, True):
        t = (sub[sub.masked == masked].groupby(["frame", "year"])["count"].sum()
             .unstack().reindex(index=frames, columns=years).fillna(0.0))
        out[masked] = cap_spikes(t.to_numpy())
    return years, frames, out[False], out[True]


def cap_spikes(x):
    """cap each year at SPIKE_MULT x the median of its neighbours (+-SPIKE_HALF years, itself excluded)."""
    y = x.copy()
    n = x.shape[1]
    for j in range(n):
        lo, hi = max(0, j - SPIKE_HALF), min(n, j + SPIKE_HALF + 1)
        nb = np.concatenate([x[:, lo:j], x[:, j + 1:hi]], axis=1)
        cap = SPIKE_MULT * np.median(nb, axis=1) + SPIKE_FLOOR
        y[:, j] = np.minimum(x[:, j], cap)
    return y


def window_sum(a, half=HALF):
    """sum over year +- half along the last axis."""
    c = np.cumsum(np.pad(a, [(0, 0)] * (a.ndim - 1) + [(half + 1, half)]), axis=-1)
    return c[..., 2 * half + 1:] - c[..., :-(2 * half + 1)]


def rate(full, masked, half=HALF):
    f, m = window_sum(full.sum(0), half), window_sum(masked.sum(0), half)
    tot = f + m
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.where(tot >= MIN_SUPPORT, m / tot, np.nan)
    return r, tot


def events(years, r):
    """peak, and the contiguous span around it where the rate is at least half the peak."""
    if np.all(np.isnan(r)):
        return dict(peak_year=np.nan, peak=np.nan, rise=np.nan, fall=np.nan, open_start=False, open_end=False)
    i = int(np.nanargmax(r))
    half = r[i] / 2
    a = i
    while a > 0 and not np.isnan(r[a - 1]) and r[a - 1] >= half:
        a -= 1
    b = i
    while b < len(r) - 1 and not np.isnan(r[b + 1]) and r[b + 1] >= half:
        b += 1
    first = int(np.argmax(~np.isnan(r)))
    return dict(peak_year=years[i], peak=r[i], rise=years[a], fall=years[b],
                open_start=a == first, open_end=b == len(r) - 1)


def recent(years, r, lo=2009):
    return np.nanmean(r[years >= lo])


def analyse(d, rng):
    rates, evs = [], []
    for w in WORDS:
        years, frames, full, masked = frame_matrix(d, w.key)
        r, tot = rate(full, masked)
        boot = np.full((B, len(years)), np.nan)
        bev = []
        k = len(frames)
        for b in range(B):
            pick = rng.integers(0, k, k)
            fb, mb = rng.poisson(full[pick]), rng.poisson(masked[pick])
            boot[b] = rate(fb, mb)[0]
            bev.append(events(years, rate(fb, mb, HALF_EVENTS)[0]))
        lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0) if k else (r, r)
        rates.append(pd.DataFrame(dict(word=w.key, year=years, rate=r, lo=lo, hi=hi, support=tot)))
        e = events(years, rate(full, masked, HALF_EVENTS)[0])
        be = pd.DataFrame(bev)
        row = dict(word=w.key, label=w.label, group=w.group, frames=k,
                   masked_total=masked.sum(), full_total=full.sum(), recent=recent(years, r), **e)
        for col in ("peak_year", "rise", "fall", "peak"):
            row[col + "_lo"], row[col + "_hi"] = np.nanpercentile(be[col].astype(float), [2.5, 97.5])
        row["recent_lo"], row["recent_hi"] = np.nanpercentile([recent(years, x) for x in boot], [2.5, 97.5])
        row["datable"] = w.group != "control" and masked.sum() >= MIN_MASKED
        evs.append(row)
        print(f"{w.key:14s} peak {e['peak']:.3%} in {e['peak_year']}  half-peak span {e['rise']}-{e['fall']}"
              f"  2009-18 {row['recent']:.3%}", flush=True)
    return pd.concat(rates), pd.DataFrame(evs)


def euphemism_shares(rng):
    """share of mentions made through "the x-word", per year, 11-year window, Poisson intervals."""
    d = pd.read_csv("data/euphemisms.csv")
    d = d[d.year.between(1900, Y1)]
    tot = pd.read_csv("data/ngram_totals.csv").set_index("year").words
    d["count"] = d.freq * d.year.map(tot)
    out = []
    for word, g in d.groupby("word"):
        t = g.groupby(["kind", "year"])["count"].sum().unstack(0).fillna(0.0)
        years = t.index.to_numpy()
        e, w = t["euphemism"].to_numpy()[None], t["word"].to_numpy()[None]
        r, sup = rate(w, e)
        boot = np.array([rate(rng.poisson(w), rng.poisson(e))[0] for _ in range(B)])
        lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
        out.append(pd.DataFrame(dict(word=word, year=years, share=r, lo=lo, hi=hi, support=sup)))
    return pd.concat(out)


def main():
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    d = load()
    rates, evs = analyse(d, np.random.default_rng(SEED))
    noise = evs[evs.group == "control"].peak.max()
    evs["above_controls"] = evs.peak_lo > noise
    rates.to_csv("tables/ngram_rates.csv", index=False)
    euph = euphemism_shares(np.random.default_rng(SEED))
    euph.to_csv("tables/euphemism_shares.csv", index=False)
    for w, g in euph.groupby("word"):
        a, b = g.set_index("year").share.get(1960), g.set_index("year").share.get(2013)
        print(f"euphemism share {w}: 1960 {a:.3%}  2013 {b:.3%}")
    evs.to_csv("tables/ngram_events.csv", index=False)
    print(f"control ceiling (highest control peak): {noise:.3%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
