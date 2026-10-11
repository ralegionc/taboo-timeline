"""Fetch yearly frequencies for every frame, full and masked, from the Google Books Ngram API.

Responses are cached in data/ngram_cache/, so a rerun costs nothing. Output: data/ngrams.csv,
one row per (word, frame, kind, variant, year) with the relative frequency.
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from words import EUPHEMISMS, WORDS, queries, star_hit

API = "https://books.google.com/ngrams/json"
CORPUS = "en"
Y0, Y1 = 1800, 2022
CACHE = Path("data/ngram_cache")
BATCH = 10
UA = {"User-Agent": "taboo-timeline research script"}


def key(s):
    return re.sub(r"\s+", "", s)


def fetch(content):
    path = CACHE / (hashlib.sha1(content.encode()).hexdigest()[:16] + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["data"]
    params = dict(content=content, year_start=Y0, year_end=Y1, corpus=CORPUS, smoothing=0)
    for attempt in range(8):
        r = requests.get(API, params=params, headers=UA, timeout=60)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        data = r.json()
        break
    else:
        raise RuntimeError(f"rate limited on {content!r}")
    path.write_text(json.dumps({"content": content, "data": data}), encoding="utf-8")
    time.sleep(1.0)
    return data


def fetch_totals():
    """yearly 1-gram totals of the English corpus, to turn frequencies into approximate counts."""
    url = "http://storage.googleapis.com/books/ngrams/books/20200217/eng/totalcounts-1"
    rows = [r.split(",") for r in requests.get(url, headers=UA, timeout=120).text.split()]
    pd.DataFrame([(int(r[0]), int(r[1])) for r in rows], columns=["year", "words"]).to_csv(
        "data/ngram_totals.csv", index=False)


def fetch_euphemisms(years):
    rows = []
    for word, (euph, forms) in EUPHEMISMS.items():
        for kind, texts in (("euphemism", euph), ("word", forms)):
            got = {key(x["ngram"]): x["timeseries"] for x in fetch(",".join(texts)) if x["type"] == "NGRAM"}
            for t in texts:
                for y, f in zip(years, got.get(key(t), [0.0] * len(years))):
                    rows.append((word, kind, t, y, f))
    pd.DataFrame(rows, columns=["word", "kind", "ngram", "year", "freq"]).to_csv("data/euphemisms.csv", index=False)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    fetch_totals()
    plain, star = [], []
    for w in WORDS:
        for q in queries(w):
            (star if q.kind == "star" else plain).append(q)

    wanted = {}  # space-free variant -> (query, variant)
    for q in plain:
        for v in q.variants:
            wanted.setdefault(key(v), []).append((q, v))
    texts = sorted({v for q in plain for v in q.variants})
    print(f"{len(texts)} plain n-grams in {len(texts) // BATCH + 1} requests, {len(star)} wildcard requests",
          flush=True)

    rows = []
    years = list(range(Y0, Y1 + 1))
    seen = set()
    for i in range(0, len(texts), BATCH):
        for item in fetch(",".join(texts[i:i + BATCH])):
            k = key(item["ngram"])
            if item["type"] != "NGRAM" or k not in wanted or k in seen:
                continue
            seen.add(k)
            for q, v in wanted[k]:
                rows += [(q.word, q.frame, q.form, q.kind, v, y, f) for y, f in zip(years, item["timeseries"])]
        if (i // BATCH) % 25 == 0:
            print(f"  plain {i}/{len(texts)}", flush=True)

    for n, q in enumerate(star):
        best = {}
        for item in fetch(q.text):
            if item["type"] == "EXPANSION" and star_hit(q.text, item["ngram"]):
                best[item["ngram"]] = item["timeseries"]  # duplicates in the response are identical
        for g, ts in best.items():
            rows += [(q.word, q.frame, q.form, "star", g, y, f) for y, f in zip(years, ts)]
        if n % 25 == 0:
            print(f"  wildcard {n}/{len(star)}", flush=True)

    df = pd.DataFrame(rows, columns=["word", "frame", "form", "kind", "ngram", "year", "freq"])
    df.to_csv("data/ngrams.csv", index=False)
    found = df.groupby("kind").ngram.nunique()
    print(f"wrote {len(df)} rows; distinct n-grams found by kind:\n{found}", flush=True)
    fetch_euphemisms(years)
    missing = sorted(set(texts) - {v for k in seen for _, v in wanted[k]})
    Path("data/ngrams_missing.txt").write_text("\n".join(missing), encoding="utf-8")
    print(f"{len(missing)} queried n-grams never reach the corpus threshold (listed in data/ngrams_missing.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
