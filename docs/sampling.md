# Sampling

Draw the sample before looking at any source, and do not replace companies afterwards because they turned out to be inconvenient.

## Population

UK companies with CompanyStatus = 'Active' and CompanyCategory
'Private Limited Company' or 'Public Limited Company': 4,765,570 companies.
Why this population: <motivul tău: legătura cu furnizorii clientului din brief>

## Sampling frame

- Source file: Companies House Free Company Data Product
- Snapshot date: <data din numele fișierului>
- Rows in the frame: 5,711,779
- Filters applied, and why:
  - excluded statuses other than 'Active' (532,523 rows): <motivul tău>
  - excluded other company types: <motivul tău>
  - excluded 'ACCOUNTS TYPE NOT AVAILABLE' (839 rows): no stratum can be assigned

## Design

| DORMANT | 513,818 | 10.8% | 50 |
NO ACCOUNTS FILED | 1,139,643 | 23.9% | 50 |
MICRO ENTITY, TOTAL EXEMPTION FULL/SMALL, UNAUDITED ABRIDGED, SMALL, AUDITED ABRIDGED, PARTIAL EXEMPTION | 2,983,724 | 62.6% | 50 |
| FULL, GROUP, MEDIUM | 92,795 | 1.9% | 50 |
| AUDIT / FILING EXEMPTION SUBSIDIARY | 34,751 | 0.7% | 30 |

- Why these strata: <motivul tău: categoria de bilanț ca semnal pentru mărime și activitate>
- Why equal sizes instead of proportional: <motivul tău: câte firme mari ai prinde altfel>
- Total size, and why this size: 230. <motivul tău: verificare manuală la HMRC, marja de eroare>
- Random seed: <seed-ul tău>
- Method: rows ordered by md5(CompanyNumber || seed) within each stratum, first N kept
- Date drawn: 2026-11-13
- Script: src/draw_sample.sql
- Reproducibility check: ran twice, same 230 companies

## Known biases

<scrii tu, vezi mai jos>

## Hand-checked subset

<!-- If you verify part of the sample manually, describe how those companies were picked and what was checked. -->
