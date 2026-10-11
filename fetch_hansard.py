"""Download House of Commons debates (1919 onwards) from TheyWorkForYou and keep the text.

Each sitting day is one XML file. Only the latest scrape of each day is used. The XML is
reduced to one line per speech (date, speech id, speaker, text) and written to
data/hansard/parts/YYYY-MM-DD.tsv.gz, so later steps never touch the network or the XML again.
Reruns skip days already saved. On a slow connection a second copy can run with --reverse.
"""
import gzip
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from lxml import etree

BASE = "https://www.theyworkforyou.com/pwdata/scrapedxml/debates/"
OUT = Path("data/hansard")
PARTS = OUT / "parts"
UA = {"User-Agent": "taboo-timeline research script (one pass, polite)"}


def list_days():
    html = requests.get(BASE, headers=UA, timeout=120).text
    latest = {}
    for date, ver in re.findall(r'href="debates(\d{4}-\d\d-\d\d)([a-z])\.xml"', html):
        if date not in latest or ver > latest[date]:
            latest[date] = ver
    return sorted(latest.items())


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def speeches(xml_bytes):
    root = etree.fromstring(xml_bytes, etree.XMLParser(recover=True, huge_tree=True))
    if root is None:
        return
    for sp in root.iter("speech"):
        text = clean(" ".join(sp.itertext()))
        if text:
            yield sp.get("id", ""), clean(sp.get("speakername", "")), text.replace("\t", " ")


def fetch_day(item):
    date, ver = item
    part = PARTS / f"{date}.tsv.gz"
    if part.exists():
        return date, "cached"
    for attempt in range(4):
        try:
            r = requests.get(f"{BASE}debates{date}{ver}.xml", headers=UA, timeout=120)
            r.raise_for_status()
            break
        except requests.RequestException as e:
            err = e
    else:
        return date, f"failed: {err}"
    rows = [f"{date}\t{i}\t{who}\t{t}\n" for i, who, t in speeches(r.content)]
    tmp = part.with_suffix(f".{threading.get_ident()}.tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        f.writelines(rows)
    tmp.replace(part)
    return date, len(rows)


def main():
    PARTS.mkdir(parents=True, exist_ok=True)
    days = list_days()
    if "--reverse" in sys.argv:
        days = days[::-1]  # a second process can work from the other end
    print(f"{len(days)} sitting days, {days[0][0]} to {days[-1][0]}", flush=True)
    failed = []
    with ThreadPoolExecutor(12) as pool:
        for n, (date, status) in enumerate(pool.map(fetch_day, days), 1):
            if isinstance(status, str) and status.startswith("failed"):
                failed.append(date)
            if n % 500 == 0:
                print(f"{n}/{len(days)} {date}", flush=True)
    print(f"failed: {len(failed)} {failed[:10]}", flush=True)
    print("done", flush=True)
    return 1 if len(failed) > 20 else 0


if __name__ == "__main__":
    sys.exit(main())
