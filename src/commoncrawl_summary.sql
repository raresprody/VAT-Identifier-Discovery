-- Combines the Common Crawl hits from all scanned files and links them to Companies House.
-- Run from the repo root after src/commoncrawl.py:  duckdb < src/commoncrawl_summary.sql
--
-- Output
--   data/commoncrawl/pairs.csv      one row per distinct (VAT number, company number)
--   data/commoncrawl/to_verify.csv  20 linkable pairs picked at random, to check at HMRC by hand

-- Every hit row from every file. all_varchar keeps leading zeros in company numbers.
CREATE TABLE hits AS
SELECT * FROM read_csv('data/commoncrawl/hits_*.csv', all_varchar = true, filename = true);

CREATE VIEW ch AS
SELECT CompanyNumber, CompanyName, CompanyStatus, "RegAddress.PostCode" AS postcode
FROM 'data/raw/BasicCompanyDataAsOneFile-2026-11-01.csv';

-- How many different company numbers each page shows. More than one (Lookers Limited and
-- Lookers Motor Group on the same footer) means the page does not say whose VAT number it is.
CREATE TABLE page_companies AS
SELECT page_url, count(DISTINCT company_number) AS companies_on_page
FROM hits
GROUP BY page_url;

-- One row per distinct (VAT number, company number), counting the pages it was seen on.
CREATE TABLE grouped AS
SELECT
    h.vat_number,
    h.company_number,
    count(DISTINCT h.page_url)   AS pages,
    count(DISTINCT h.filename)   AS files,
    max(p.companies_on_page)     AS max_companies_on_page,
    any_value(h.host)            AS example_host,
    any_value(h.page_url)        AS example_page,
    any_value(h.vat_context)     AS example_vat_context
FROM hits h
JOIN page_companies p USING (page_url)
GROUP BY h.vat_number, h.company_number;

-- Add the Companies House record and decide whether the pair can be linked to one company.
CREATE TABLE pairs AS
SELECT
    g.*,
    ch.CompanyName    AS ch_name,
    ch.CompanyStatus  AS ch_status,
    ch.postcode       AS ch_postcode,
    CASE
        WHEN ch.CompanyNumber IS NULL      THEN 'not a Companies House number'
        WHEN g.max_companies_on_page > 1   THEN 'ambiguous: several companies on page'
        ELSE 'linkable'
    END AS status
FROM grouped g
LEFT JOIN ch ON ch.CompanyNumber = g.company_number;

COPY (SELECT * FROM pairs ORDER BY status, company_number) TO 'data/commoncrawl/pairs.csv' (HEADER);

-- 20 linkable pairs in a random but repeatable order (same md5 trick as the sample).
COPY (
    SELECT vat_number, company_number, ch_name, ch_postcode, example_page,
           '' AS hmrc_name, '' AS hmrc_postcode, '' AS checked_on
    FROM pairs
    WHERE status = 'linkable'
    ORDER BY md5(vat_number || company_number || '2026-11-17_commoncrawl')
    LIMIT 20
) TO 'data/commoncrawl/to_verify.csv' (HEADER);

-- Funnel per file, then in total.
SELECT
    coalesce(regexp_extract(filename, 'hits_(\d+)', 1), 'total') AS file,
    count(DISTINCT page_url)                       AS pages_with_both,
    count(DISTINCT (vat_number, company_number))   AS distinct_pairs
FROM hits
GROUP BY ROLLUP (filename)
ORDER BY file;

SELECT status, count(*) AS pairs, count(DISTINCT company_number) AS companies
FROM pairs
GROUP BY ROLLUP (status)
ORDER BY status;

-- Same VAT number paired with different companies, or same company with different VAT numbers.
SELECT 'VAT number with >1 company' AS check, count(*) AS n
FROM (SELECT vat_number FROM pairs GROUP BY 1 HAVING count(DISTINCT company_number) > 1)
UNION ALL
SELECT 'company with >1 VAT number', count(*)
FROM (SELECT company_number FROM pairs GROUP BY 1 HAVING count(DISTINCT vat_number) > 1);
