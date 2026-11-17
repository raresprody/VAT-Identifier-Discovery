"""Scan Common Crawl text files for pages showing a VAT number and a company number together.

    python src/commoncrawl.py 0        # scan the 1st of the randomly chosen files
    python src/commoncrawl.py 0 1 2    # scan several

Why both numbers: a VAT number alone on a page says nothing about which
company it belongs to (an agency's number in a client's footer, a group
company's number on a brand site). A page that also shows a Companies House
number states which legal entity it is talking about.

Files are read as a stream and not kept. Per file, the scan writes
    data/commoncrawl/hits_<n>.csv     one row per (page, VAT number, company number)
    evidence/commoncrawl/stats_<n>.json   counts and timing
"""
from __future__ import annotations

import csv
import gzip
import json
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from stdnum.gb import vat

CRAWL = "CC-MAIN-2026-43"
BASE = "https://data.commoncrawl.org/"
SEED = "2026-11-17_commoncrawl"
FILES_TO_PICK = 10
HITS_DIR = Path("data/commoncrawl")
STATS_DIR = Path("evidence/commoncrawl")

# "VAT", then up to 40 characters that are not digits ("Reg No:", "number is"),
# then 9 digits (optionally 12) grouped as 3-4-2, optional GB prefix.
VAT_RE = re.compile(
    r"\bVAT\b[^\d\n]{0,40}?\b((?:GB\s?)?\d{3}\s?\d{4}\s?\d{2}(?:\s?\d{3})?)\b",
    re.IGNORECASE,
)
# "Company No", "Company Registration Number", "Registered in England and Wales No",
# then a Companies House number: 8 digits, or 2 letters + 6 digits (SC, NI, OC...).
COMPANY_RE = re.compile(
    r"(?:\bcompany\s+(?:reg(?:istration|istered)?\.?\s+)?(?:no|number|num)\b"
    r"|\bregistered\s+in\s+(?:england|scotland|wales|northern\s+ireland)[\w\s&,]{0,30}?(?:no|number)\b)"
    r"[.:\s]{0,4}((?:SC|NI|OC|SO|NC|R0)?\s?\d{6,8})\b",
    re.IGNORECASE,
)


def get(url: str, stream: bool = False) -> requests.Response:
    """GET with retries. Common Crawl answers 503 when it is busy; wait and try again."""
    for attempt in range(6):
        response = requests.get(url, stream=stream, timeout=60)
        if response.status_code != 503:
            response.raise_for_status()
            return response
        response.close()
        time.sleep(15 * 2 ** attempt)  # 15 s, 30 s, 60 s ...
    response.raise_for_status()
    return response


def chosen_files() -> list[str]:
    """The same 10 file paths every time, picked at random from the crawl's 100,000."""
    saved = STATS_DIR / "chosen_files.txt"
    if saved.exists():
        return saved.read_text().split()
    paths = gzip.decompress(get(f"{BASE}crawl-data/{CRAWL}/wet.paths.gz").content).decode().split()
    chosen = random.Random(SEED).sample(paths, FILES_TO_PICK)
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    saved.write_text("\n".join(chosen) + "\n")
    return chosen


def records(url: str):
    """Yield (page_url, text) for each page in a WET file, streamed over HTTP."""
    with get(url, stream=True) as response:
        stream = gzip.GzipFile(fileobj=response.raw)
        while True:
            headers = {}
            line = stream.readline()
            if not line:
                return
            if not line.startswith(b"WARC/"):
                continue
            while (line := stream.readline().strip()):
                key, _, value = line.decode("utf-8", "replace").partition(":")
                headers[key.strip().lower()] = value.strip()
            body = stream.read(int(headers.get("content-length", 0)))
            if headers.get("warc-type") == "conversion":
                yield headers.get("warc-target-uri", ""), body.decode("utf-8", "replace")


def normalise_company_number(raw: str) -> str:
    raw = raw.replace(" ", "").upper()
    prefix = raw[:2] if raw[:2].isalpha() else ""
    digits = raw[len(prefix):]
    return prefix + digits.zfill(8 - len(prefix))


def context(text: str, match: re.Match) -> str:
    start, end = max(match.start() - 40, 0), min(match.end() + 40, len(text))
    return " ".join(text[start:end].split())


def scan(index: int) -> dict:
    path = chosen_files()[index]
    stats = {"file_index": index, "path": path, "pages": 0, "uk_pages": 0,
             "pages_with_vat_shape": 0, "pages_with_valid_vat": 0, "pages_with_both": 0}
    hits = []
    started = time.time()

    for page_url, text in records(BASE + path):
        stats["pages"] += 1
        host = urlparse(page_url).hostname or ""
        if host.endswith(".uk"):
            stats["uk_pages"] += 1

        vat_matches = list(VAT_RE.finditer(text))
        if not vat_matches:
            continue
        stats["pages_with_vat_shape"] += 1
        valid = [(m, vat.compact(m.group(1))) for m in vat_matches if vat.is_valid(m.group(1))]
        if not valid:
            continue
        stats["pages_with_valid_vat"] += 1
        companies = list(COMPANY_RE.finditer(text))
        if not companies:
            continue
        stats["pages_with_both"] += 1

        # Every VAT number on the page paired with every company number on the page.
        # A pair seen twice on the same page is kept once.
        seen = set()
        for vat_match, vat_number in valid:
            for company_match in companies:
                company_number = normalise_company_number(company_match.group(1))
                if (vat_number, company_number) in seen:
                    continue
                seen.add((vat_number, company_number))
                hits.append({
                    "page_url": page_url,
                    "host": host,
                    "vat_number": vat_number,
                    "company_number": company_number,
                    "vat_context": context(text, vat_match),
                    "company_context": context(text, company_match),
                })

    stats["seconds"] = round(time.time() - started, 1)
    stats["hit_rows"] = len(hits)

    HITS_DIR.mkdir(parents=True, exist_ok=True)
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["page_url", "host", "vat_number", "company_number", "vat_context", "company_context"]
    with (HITS_DIR / f"hits_{index}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(hits)
    (STATS_DIR / f"stats_{index}.json").write_text(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    for i in [int(a) for a in sys.argv[1:]] or [0]:
        print(json.dumps(scan(i), indent=2))
