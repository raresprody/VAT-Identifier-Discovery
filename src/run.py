"""Verify every candidate VAT number and report the results per stratum.

    python src/run.py                 # HMRC answers from data/hmrc_recorded.csv (manual checks)
    python src/run.py --hmrc api      # ask HMRC's API live (needs production credentials in .env)

Inputs
    data/sample_230.csv      the sample, drawn by src/draw_sample.sql
    data/candidates.csv      one row per company checked: where I looked and what I found
    data/hmrc_recorded.csv   HMRC's answer for each number, copied from the gov.uk checker
    data/ch_context.csv      per company: how many companies share its exact name, and its
                             postcode. Built once from the Companies House snapshot in data/raw/.

Outputs
    data/results/results.csv  every candidate row with the decision from src/match.py
    data/results/summary.md   counts per check set and stratum
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from match import decide

SAMPLE = Path("data/sample_230.csv")
CANDIDATES = Path("data/candidates.csv")
RECORDED = Path("data/hmrc_recorded.csv")
CONTEXT = Path("data/ch_context.csv")
CH_SNAPSHOT = Path("data/raw/BasicCompanyDataAsOneFile-2026-11-01.csv")
OUT = Path("data/results")


def read(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def build_context(sample: list[dict]) -> None:
    """Count, for each sampled company, the companies sharing its name and its postcode."""
    import duckdb

    duckdb.sql(f"""
        COPY (
            WITH ch AS (SELECT CompanyName, "RegAddress.PostCode" AS postcode FROM '{CH_SNAPSHOT}'),
                 names AS (SELECT CompanyName, count(*) AS n FROM ch GROUP BY 1),
                 postcodes AS (SELECT postcode, count(*) AS n FROM ch GROUP BY 1)
            SELECT s.CompanyNumber AS company_number,
                   coalesce(names.n, 0) AS companies_with_same_name,
                   coalesce(postcodes.n, 0) AS companies_at_postcode
            FROM '{SAMPLE}' s
            LEFT JOIN names ON names.CompanyName = s.CompanyName
            LEFT JOIN postcodes ON postcodes.postcode = s.postcode
            ORDER BY s.CompanyNumber
        ) TO '{CONTEXT}' (HEADER)
    """)


def hmrc_answers(candidates: list[dict], mode: str) -> dict[str, dict | None]:
    numbers = {c["vat_candidate"] for c in candidates if c["vat_candidate"]}
    if mode == "recorded":
        recorded = {r["vat_number"]: {"name": r["hmrc_name"], "postcode": r["hmrc_postcode"]} for r in read(RECORDED)}
        return {n: recorded.get(n) for n in numbers}

    from dotenv import load_dotenv
    from stdnum.gb import vat

    import hmrc

    load_dotenv(".env")
    url = hmrc.base_url()
    token = hmrc.get_token(url)
    return {n: hmrc.lookup(vat.compact(n), token, url) if vat.is_valid(n) else None for n in numbers}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hmrc", choices=["recorded", "api"], default="recorded")
    args = parser.parse_args()

    sample = {r["CompanyNumber"]: r for r in read(SAMPLE)}
    if not CONTEXT.exists():
        build_context(list(sample.values()))
    context = {r["company_number"]: r for r in read(CONTEXT)}
    candidates = read(CANDIDATES)
    answers = hmrc_answers(candidates, args.hmrc)

    results = []
    for c in candidates:
        company = sample[c["company_number"]]
        answer = answers.get(c["vat_candidate"]) if c["vat_candidate"] else None
        ctx = context[c["company_number"]]
        results.append({
            "check_set": c["check_set"],
            "company_number": c["company_number"],
            "company_name": company["CompanyName"],
            "stratum": company["stratum"],
            "source": c["source"],
            "vat_candidate": c["vat_candidate"],
            "hmrc_name": answer["name"] if answer else "",
            "hmrc_postcode": answer["postcode"] if answer else "",
            "ch_postcode": company["postcode"],
            "companies_with_same_name": ctx["companies_with_same_name"],
            "companies_at_ch_postcode": ctx["companies_at_postcode"],
            "decision": decide(
                c["vat_candidate"], company["CompanyName"], company["postcode"],
                answer["name"] if answer else None, answer["postcode"] if answer else None,
                int(ctx["companies_with_same_name"]),
            ),
            "notes": c["notes"],
        })

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "results.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, list(results[0]))
        w.writeheader()
        w.writerows(results)

    summary = summarise(results, args.hmrc)
    (OUT / "summary.md").write_text(summary)
    print(summary)


def summarise(results: list[dict], mode: str) -> str:
    lines = [f"HMRC answers: {mode}", ""]
    for check_set in sorted({r["check_set"] for r in results}):
        rows = [r for r in results if r["check_set"] == check_set]
        lines += [f"## {check_set}", "",
                  "| Stratum | Checked | Candidate found | Tier A | Tier B | Review | Rejected |",
                  "|---|---|---|---|---|---|---|"]
        for stratum in sorted({r["stratum"] for r in rows}) + ["total"]:
            group = rows if stratum == "total" else [r for r in rows if r["stratum"] == stratum]
            d = Counter(r["decision"] for r in group)
            rejected = sum(n for k, n in d.items() if k.startswith("reject"))
            found = sum(1 for r in group if r["vat_candidate"])
            lines.append(f"| {stratum} | {len(group)} | {found} | {d['tier A']} | {d['tier B']} | {d['review']} | {rejected} |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
