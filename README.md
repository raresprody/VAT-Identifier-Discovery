# UK VAT Identifier Discovery

## Short answer

<!-- Write last. 3-4 sentences: can it be done, for which companies, what coverage and error rate on what sample, where it stops working. -->

## How to reproduce

Python 3.14 and the DuckDB command-line tool.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
.venv/bin/python src/run.py
```

`src/run.py` reads the companies I checked (`data/candidates.csv`) and HMRC's answers as I recorded them from the gov.uk checker (`data/hmrc_recorded.csv`), applies the matching rule in `src/match.py`, and writes `data/results/results.csv` and `data/results/summary.md`.

To query HMRC live instead, put production credentials for the "Check a UK VAT number" API in `.env` (see `.env.example`) and run `src/run.py --hmrc api`. Each answer is saved under `evidence/hmrc/`.

To re-draw the sample, download the Companies House snapshot (BasicCompanyDataAsOneFile-2026-11-01) from https://download.companieshouse.gov.uk/en_output.html, unzip it into `data/raw/`, then run `duckdb < src/draw_sample.sql`. The output should be identical to the committed `data/sample_230.csv`.

## Repo layout

```
src/draw_sample.sql        draws the 230-company sample from Companies House
src/match.py               the rule deciding whether a VAT number belongs to a company
src/hmrc.py                HMRC "Check a UK VAT number" API client
src/run.py                 applies the rule to every candidate and writes the results
tests/test_match.py        the rule tested on the real cases from the manual checks
data/sample_230.csv        the sample
data/candidates.csv        what I found for each company checked, and where
data/hmrc_recorded.csv     HMRC's answer for each number found
data/ch_context.csv        per sampled company: companies sharing its name and its postcode
data/results/              outputs of src/run.py
evidence/                  raw outputs behind the numbers in this document
```

## Part 1: Research

### What I learned that wasn't obvious at the start

### Sources tested

| Source | What I expected | Tested on (n) | What came back | Status | Evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Dead ends

## Part 2: Proof of concept

### Sample

### Method

### Matching rule

### Results

### What these numbers don't capture

## Part 3: With real resources

### What I would do

### Cost per company

### What breaks first

### What I would monitor

## Debate topics

### Enumerating valid numbers against HMRC's checker

### Keeping the dataset current

### Knowing the dataset is wrong at scale

### Sources I would not use in a product

## How I used AI tools
