-- Draws the stratified sample of 230 companies. Deterministic: same snapshot and seed give the same rows.
-- Run from the repo root:  duckdb < src/draw_sample.sql
-- Input:  data/raw/BasicCompanyDataAsOneFile-2026-11-01.csv (Companies House Free Company Data Product)
-- Output: data/sample_230.csv
-- Design and reasoning: README.md, Part 2, Sample

CREATE VIEW ch AS
SELECT * FROM 'data/raw/BasicCompanyDataAsOneFile-2026-11-01.csv';

COPY (
    SELECT *
    FROM (
        SELECT
            CompanyNumber,
            CompanyName,
            "RegAddress.AddressLine1"    AS address_line1,
            "RegAddress.AddressLine2"    AS address_line2,
            "RegAddress.PostTown"        AS post_town,
            "RegAddress.PostCode"        AS postcode,
            CompanyCategory,
            IncorporationDate,
            "Accounts.AccountCategory"   AS account_category,
            "SICCode.SicText_1"          AS sic_1,
            "SICCode.SicText_2"          AS sic_2,
            "PreviousName_1.CompanyName" AS previous_name,
            CASE
                WHEN "Accounts.AccountCategory" = 'DORMANT' THEN 'dormant'
                WHEN "Accounts.AccountCategory" = 'NO ACCOUNTS FILED' THEN 'new'
                WHEN "Accounts.AccountCategory" IN (
                         'MICRO ENTITY', 'TOTAL EXEMPTION FULL', 'TOTAL EXEMPTION SMALL',
                         'UNAUDITED ABRIDGED', 'SMALL', 'AUDITED ABRIDGED', 'PARTIAL EXEMPTION'
                     ) THEN 'small'
                WHEN "Accounts.AccountCategory" IN ('FULL', 'GROUP', 'MEDIUM') THEN 'large'
                WHEN "Accounts.AccountCategory" IN (
                         'AUDIT EXEMPTION SUBSIDIARY', 'FILING EXEMPTION SUBSIDIARY'
                     ) THEN 'subsidiary'
            END AS stratum
        FROM ch
        WHERE CompanyStatus = 'Active'
          AND CompanyCategory IN ('Private Limited Company', 'Public Limited Company')
    )
    WHERE stratum IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
                PARTITION BY stratum
                ORDER BY md5(CompanyNumber || '2026-11-13_UK_VAT_DISCOVERY')
            ) <= CASE WHEN stratum = 'subsidiary' THEN 30 ELSE 50 END
    ORDER BY stratum, CompanyNumber
) TO 'data/sample_230.csv' (HEADER);
