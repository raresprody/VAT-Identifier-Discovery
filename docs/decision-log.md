# Decision log

One entry per thing tried or decided, newest at the bottom. Write the entry the same day, while you still remember why. Never rewrite an old entry: if you change your mind, add a new one that points back to it.

## Entry template

### 2026-11-13 15:19  Câte firme are snapshot-ul Companies House

Question:       Câte rânduri are fișierul și ce coloane?
Expected:       În jur de 4,2 milioane, cât zice brief-ul pentru firme active.
What I did:     Am rulat în DuckDB SELECT COUNT(*) și DESCRIBE pe CSV-ul
                descărcat.
What came back: 5.711.779 rânduri. Printre coloane: CompanyStatus,
                CompanyCategory, IncorporationDate, Accounts.AccountCategory,
                adresa împărțită pe câmpuri, cu codul poștal separat.
Evidence:       evidence/2026-11-13_ch_sql.txt
Decision:       Număr firmele pe CompanyStatus și CompanyCategory ca să văd
                de unde vine diferența față de brief.
Open:           De ce 5,71 milioane și nu 4,2? Ce populație folosesc pentru eșantion?

### 2026-11-13 15:33 Cate firme unt active din snapshot-ul Companies House
Question:       Câte rânduri are fișierul și ce coloane?
Expected:       Ma astept la minim 4 milioane sa fie active.
What I did:     Am rulat în DuckDB SELECT CompanyStatus in CSV
What came back: 5179256 companii Active si 417325 Active - Proposal to Strike off .
Evidence:       evidence/2026-11-13_ch_sql.txt
Decision:       Număr firmele pe CompanyStatus și CompanyCategory ca să văd
                de unde vine diferența față de brief.
Open:           De ce 5,71 milioane și nu 4,2? Ce populație folosesc pentru eșantion?

## Entries

### 2026-11-12  To write up from today

<!-- Turn each line into a full entry using the template, in your own words. Delete this block when done.

- Manual check of two known VAT numbers in the HMRC checker: what it returned, field by field.
- What the checker does NOT return, and why that matters for linking to Companies House.
- The HSBC lookup in Companies House: how many candidates, how many at the same address.
- The Tesco Stores Limited lookup: re-check by company number and record what you find.
- Claim that two Tesco companies share a VAT number: where it came from, and whether you can trace it.
- First definition of "false positive" and how it changed during the day.
- First matching rule (name and address both identical) and what you expect it to cost.
-->
SELECT grupa, COUNT(*) AS n
FROM (
    SELECT
        CompanyNumber,
        CASE
            WHEN "Accounts.AccountCategory" IN ('DORMANT') THEN 'fara_activitate'
            WHEN "Accounts.AccountCategory" IN ('NO ACCOUNTS FILED') THEN 'noi'
            WHEN "Accounts.AccountCategory" IN ('MICRO ENTITY', 'TOTAL EXEMPTION FULL', 'UNAUDITED ABRIDGED', 'SMALL', 'PARTIAL EXEMPTION', 'TOTAL EXEMPTION SMALL', 'AUDITED ABRIDGED') THEN 'mici'
            WHEN "Accounts.AccountCategory" IN ('FULL', 'GROUP', 'MEDIUM') THEN 'mari'
            WHEN "Accounts.AccountCategory" IN ('AUDIT EXEMPTION SUBSIDIARY', 'FILING EXEMPTION SUBSIDIARY') THEN 'filiale'
        END AS grupa
    FROM ch
    WHERE CompanyStatus = 'Active'
      AND CompanyCategory IN ('Private Limited Company', 'Public Limited Company')
)
GROUP BY grupa
ORDER BY n DESC;
COPY (
    SELECT *
    FROM (
        SELECT
            CompanyNumber,
            CompanyName,
            ...,                      -- restul coloanelor de care ai nevoie
            CASE ... END AS grupa     -- același CASE de la etapa 1
        FROM ch
        WHERE ...                     -- același filtru de la etapa 1
    )
    WHERE grupa IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
                PARTITION BY grupa
                ORDER BY md5(CompanyNumber || '...')    -- seed-ul tău
            ) <= CASE WHEN grupa = 'filiale' THEN ... ELSE ... END
) TO 'data/sample/sample.csv' (HEADER);

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
) TO 'data/sample/sample.csv' (HEADER);