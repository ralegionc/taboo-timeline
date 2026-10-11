"""Rerun the book analysis with one choice changed at a time.

The claim under test is the order of the waves: every datable blasphemy word (damn, hell, devil)
peaks before every datable bodily or sexual word (shit, fuck), and every word's masking has
since fallen at least tenfold from its peak. Writes tables/sensitivity.csv.
"""
import sys

import numpy as np
import pandas as pd

import ngram_index as ni
from words import WORDS

WAVE1, WAVE2 = ["damn", "hell", "devil"], ["shit", "fuck"]


def run(d, name, frame_mean=False, drop_top_frame=False):
    rows = []
    for w in WORDS:
        if w.group == "control":
            continue
        years, frames, full, masked = ni.frame_matrix(d, w.key)
        if drop_top_frame and len(frames) > 1:
            keep = np.argsort(full.sum(1) + masked.sum(1))[:-1]
            full, masked = full[keep], masked[keep]
        if frame_mean:
            f, m = ni.window_sum(full, ni.HALF_EVENTS), ni.window_sum(masked, ni.HALF_EVENTS)
            with np.errstate(invalid="ignore", divide="ignore"):
                per = np.where(f + m >= 20, m / (f + m), np.nan)
            r = np.nanmean(per, axis=0) if len(per) else np.full(len(years), np.nan)
            r = np.where(ni.window_sum(full.sum(0)[None], ni.HALF_EVENTS)[0] >= ni.MIN_SUPPORT, r, np.nan)
        else:
            r = ni.rate(full, masked, ni.HALF_EVENTS)[0]
        e = ni.events(years, r)
        recent = np.nanmean(ni.rate(full, masked)[0][years >= 2009])
        rows.append(dict(variant=name, word=w.key, datable=masked.sum() >= ni.MIN_MASKED, **e, recent=recent))
    t = pd.DataFrame(rows)
    dt = t[t.datable].set_index("word")
    w1 = [dt.peak_year[k] for k in WAVE1 if k in dt.index]
    w2 = [dt.peak_year[k] for k in WAVE2 if k in dt.index]
    order = bool(w1 and w2 and max(w1) < min(w2))
    fallen = bool((dt.recent * 10 <= dt.peak).all())
    t["waves_in_order"], t["all_fell_tenfold"] = order, fallen
    print(f"{name:28s} wave order {'yes' if order else 'NO '}  tenfold fall {'yes' if fallen else 'NO '}  "
          + " ".join(f"{k}:{int(dt.peak_year[k])}" for k in WAVE1 + WAVE2 if k in dt.index), flush=True)
    return t


def main():
    base = ni.load()
    out = []
    defaults = dict(HALF=ni.HALF, HALF_EVENTS=ni.HALF_EVENTS, MIN_SUPPORT=ni.MIN_SUPPORT,
                    SPIKE_MULT=ni.SPIKE_MULT)

    def variant(name, data=None, **kw):
        for k, v in {**defaults, **{k: v for k, v in kw.items() if k in defaults}}.items():
            setattr(ni, k, v)
        out.append(run(base if data is None else data, name,
                       frame_mean=kw.get("frame_mean", False), drop_top_frame=kw.get("drop_top_frame", False)))

    variant("baseline")
    variant("event window +-5", HALF_EVENTS=5)
    variant("event window +-15", HALF_EVENTS=15)
    variant("no spike capping", SPIKE_MULT=1e9)
    variant("support floor 50", MIN_SUPPORT=50)
    variant("support floor 300", MIN_SUPPORT=300)
    variant("no trailing masks", data=base[base.kind != "trail"])
    variant("multi-dash masks only", data=base[(base.kind == "full") | base.ngram.str.contains("--")])
    variant("mean of frame rates", frame_mean=True)
    variant("biggest frame dropped", drop_top_frame=True)
    star = pd.read_csv("data/ngrams.csv")
    star = star[star.year.between(ni.Y0, ni.Y1)]
    tot = pd.read_csv("data/ngram_totals.csv").set_index("year").words
    star["count"] = star.freq * star.year.map(tot)
    star["masked"] = star.kind != "full"
    variant("asterisk masks included", data=pd.concat([base, star[star.kind == "star"]]))
    for k, v in defaults.items():
        setattr(ni, k, v)
    res = pd.concat(out)
    res.to_csv("tables/sensitivity.csv", index=False)
    s = res.drop_duplicates("variant")
    print(f"\nwave order holds in {s.waves_in_order.sum()}/{len(s)}, tenfold fall in {s.all_fell_tenfold.sum()}/{len(s)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
