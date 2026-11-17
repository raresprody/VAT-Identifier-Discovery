"""Apply the matching rule (src/match.py) to the Common Crawl pairs checked by hand at HMRC.

    python src/commoncrawl_verify.py

Input:  data/commoncrawl/to_verify.csv   20 random linkable pairs, HMRC columns filled in by hand
Output: data/commoncrawl/verified.csv    the same rows with the decision added
"""
import csv
from collections import Counter
from pathlib import Path

import duckdb

from match import decide

IN = Path("data/commoncrawl/to_verify.csv")
OUT = Path("data/commoncrawl/verified.csv")
CH_SNAPSHOT = "data/raw/BasicCompanyDataAsOneFile-2026-11-01.csv"

rows = list(csv.DictReader(IN.open(newline="")))

# How many Companies House companies carry each exact name (needed for tier B).
names = [r["ch_name"] for r in rows]
counts = dict(duckdb.execute(
    f"SELECT CompanyName, count(*) FROM '{CH_SNAPSHOT}' WHERE CompanyName IN (SELECT unnest(?)) GROUP BY 1",
    [names],
).fetchall())

for r in rows:
    r["companies_with_same_name"] = counts.get(r["ch_name"], 0)
    r["decision"] = decide(
        r["vat_number"], r["ch_name"], r["ch_postcode"],
        r["hmrc_name"] or None, r["hmrc_postcode"] or None,
        r["companies_with_same_name"],
    )

with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)

for r in rows:
    print(f"{r['decision']:<28} {r['ch_name']:<34} HMRC: {r['hmrc_name']}")
print()
for decision, n in Counter(r["decision"] for r in rows).most_common():
    print(f"{decision}: {n}")
