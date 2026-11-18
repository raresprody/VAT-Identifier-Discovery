# UK VAT Identifier Discovery

## Short answer

Yes, partly. You can build a UK VAT dataset from the open web, but only for companies that actually trade and publish their details, mostly small and medium businesses with their own website. It won’t work for new companies, holding companies and subsidiaries, which usually don’t have a VAT number of their own.

The most promising source I found is Common Crawl, a free archive of the web. In 10 random files out of 100,000 (about 210,000 pages), I found 216 pages linking a VAT number to one real company. When I checked 20 of them by hand at HMRC, 16 passed my matching rule.

The most important thing I learned is that no web page proves whose VAT number it is. Even pages showing both the VAT number and the company number were wrong in 3 of 20 cases: the number belonged to the parent or a sister company. What keeps the data clean is the check at the end: HMRC’s name has to match the Companies House name exactly, or the number is rejected.

My numbers come from small samples (46 companies on Endole, 20 pairs from Common Crawl), so I can show the method works, but I can’t promise a 0% error rate yet. The next step would be a bigger Common Crawl run and a monthly manual audit against real invoices.

### Results at a glance

| Source | Tested on | Numbers found | Accepted after HMRC + matching rule | Belonged to another company | Status |
|---|---|---|---|---|---|
| Company websites (by hand) | 10 companies | 2 | 0 | 2 | dead end |
| Endole (third-party aggregator) | 46 companies | 7 | 7 (4 tier A, 3 tier B) | 0 | works, but not usable in a product |
| Peppol directory | 17 companies | 0 | 0 | 0 | dead end |
| Common Crawl (bulk web archive) | 210,843 pages, 10 files | 216 linkable pairs | 16 of 20 checked (12 A, 4 B) | 3 of 20 | most promising |

## Part 1: Research

### Where I started and why

I started this project not even knowing how a VAT number looks in the UK, but after looking close on the brief, this challenge got me instantly checking every source about the legislation and I found so many interesting things

The brief made some things clear from the beginning:

- HMRC only confirms the number, it doesn't serve it to you on a silver plate
- the real challenge is not finding the number, but to prove with no doubt that it is linked to the correct firm

So my rules were simple: a number is accepted only if the name shown by HMRC = the name from "Companies House"

My plan was initially to do a fuzzy match > 85, but it instantly turned out to be a dead end. Why? You'll see this below in my sources

### Source 1: Company websites (dead end)

My expectation was that, as I have seen in Romania, companies would put their VAT numbers on their website, in the footer section/contact page. Before searching anything, I drew a random sample of 230 companies from Companies House (how and why is in Part 2, Sample).

What did I do with the 230 companies: I like to check things by myself so I went on the internet and searched for the websites of 10 companies, 2 of each group, to see by myself if this is the way to pursue this problem. It turned out that 4 of them either didn't have any website at all or no VAT, 2 of them had the VAT in their contact page, but of the group:

* Getthelabel.com Ltd (dormant) → HMRC: Topgrade Sportswear Ltd, same address NG20 8RY
* Inn Collection Bidco 2 Ltd → HMRC: Inn Collection Topco Ltd. In Companies House there are 31 companies "Inn Collection" at the same postcode NE12 8BS.

The last two of them (Adore Golf and Deswik Europe) did have a VAT number, which I later found on Endole, but they had not listed it on their website.

I have to admit that 10 companies are not enough to prove that websites are a bad source, but for me it was enough to stop pursuing this, thinking that there had to be better alternatives

### Source 2: Endole (works, but it is someone else's database)

What did I do: 46 companies, every 5th row of my 230-company sample, so I did not pick them myself. Evidence: data/candidates.csv (check_set = endole_every5th).

What came out: 7 VAT numbers, every single one of them registered at HMRC under the same name as in Companies House. The address matched for 4 of them (tier A); for 3 it was different (tier B, see the matching rule in Part 2). The table is in Part 2.

Where do they get their data: their help page (https://www.endole.co.uk/help/where-does-endole-get-its-data-from-22) says official registers + public directories, list brokers and credit reference agencies. Companies House has no VAT numbers, so the VAT numbers must come from the second group.

My provenance test (on companies from my website check, plus two companies outside the sample):

- for Getthelabel and Inn Collection Bidco 2, Endole doesn't show any number (it did not copy the mistake that the websites had made)
- for Topgrade Sportswear (outside the sample) it shows the correct number
- for Inn Collection Topco (outside the sample) it doesn't show anything, although it is registered

I also found vatnumber.co.uk, a "reverse VAT lookup" site. Its page says "Powered by Endole API", so it is not an independent source: the two agreeing would prove nothing.

Why this is not my preferred solution: see Debate, "Sources I would not use in a product".

### Source 3: Peppol e-invoicing directory (dead end)

What I thought I would find: the companies that receive electronic invoices could be listed with their identifier.

What I did: searched by name for the 10 "large" companies + the confirmed 7 companies.

Found in the directory: 0 of 17.

Why: almost all small/medium sized companies are not listed there; useful maybe only for the public sector.

### Source 4: Common Crawl (most promising)

Why did I try it: the brief mentions large web corpora; site-by-site crawling doesn't scale.

Idea: keep only the pages that show not only a valid VAT number, but also a Company Number. The Company Number tells which legal entity the page is about (this should solve the group sites problem).

What did I do: 10 files randomly chosen from the 100,000 of the archive CC-MAIN-2026-43. Code: src/commoncrawl.py, src/commoncrawl_summary.sql. Evidence: evidence/commoncrawl/.

The funnel (from evidence/commoncrawl/stats_*.json):

210,843 pages → 4,614 from .uk websites → 416 with a valid VAT number near the word "VAT" → 258 with both numbers → 233 distinct (VAT number, company number) pairs → 216 linked to a single real company in Companies House

Filters that did the work by themselves:

- 11 ambiguous pairs: pages showing more than one company (Lookers Ltd + Lookers Motor Group; Euronics + Domestic & General). I don’t accept these, because the page doesn’t say whose VAT number it is.
- 6 numbers that are not Companies House numbers (for example the University of Edinburgh, which shows a charity number).

The check: I picked 20 pairs at random and checked every one of them by hand at HMRC. Evidence: data/commoncrawl/verified.csv.

Result: 12 tier A, 4 tier B, 4 rejected.

The surprise: my idea that “both numbers on the same page = a safe link” turned out to be wrong in 3 out of 20 cases (15%, 95% interval: 3%–38%):

- Mustard Market Research → HMRC: CIRL Holdings (the parent company)
- The Mae Deli → HMRC: Hero UK Foods (the owner of the Deliciously Ella brand)
- McSence Ltd → HMRC: McSence Workspace Ltd (a sister company)

Without the name check at HMRC, all three would have ended up in the dataset as wrong numbers.

And one case I rejected on purpose: Mane Contract Services. HMRC shows the name without “Limited”, so it could be a different entity (for example a sole trader with the same name). It’s probably the same company, but I prefer a missing number to a wrong one.

Speed: about 3.3 seconds per file on my laptop.

What I can’t say: how many distinct companies the whole archive would give. 224 of the 233 pairs appear in only one file, so 10 files are too few to see how often the same companies repeat. Multiplying by 10,000 would overestimate it.

### What I learned that wasn't obvious at the start

- A real VAT number, at the right address, can still belong to another company. Groups share the same office and the same website (Getthelabel, Inn Collection, CIRL Holdings, Hero UK Foods, McSence Workspace).
- Fuzzy matching is dangerous here. Inn Collection Bidco 2 vs Inn Collection Topco scores 86.2, above the 85 threshold I was planning to use, and they are different companies.
- The postcode proves almost nothing at mail-forwarding addresses: 89,012 companies are registered at WC2H 9JQ and 36,097 at N1 7GU (data/ch_context.csv).
- Companies House often has the accountant’s address, while HMRC has the address where the business actually works (Deswik, Cadlux). So a different postcode doesn’t mean a wrong company.
- “Dormant” doesn’t mean “no VAT” (Intellispace is dormant but still VAT registered), and “large” often means a holding company with no VAT number of its own (only 1 of 10 large companies had one).
- “Reverse VAT lookup” websites can be the same database under another name (vatnumber.co.uk is powered by Endole).

### Sources I did not test

- Companies House filed accounts: the only source tied for sure to the company number, and available as daily bulk files. I didn’t test it because annual accounts don’t have to include the VAT number, so I expected very few hits.
- EORI numbers: a GB EORI number is said to contain the VAT number. But the official checker only works backwards, like HMRC’s VAT checker: you give it the number and it tells you the company (and only shows the name if the company agreed). There is no search by company name, so it doesn’t help with discovery.
- The Gazette (insolvency notices): official notices with the company name and number. I didn’t test it because it covers companies going out of business, not active suppliers, and I doubt the notices include VAT numbers.
- Council spending data: councils publish payments to suppliers over £500. I didn’t test it because there are hundreds of files in different formats, and most only have the supplier’s name, which brings back the matching-by-name problem.
- Contracts Finder: structured data about public-sector suppliers. I didn’t test it because I expect suppliers to be identified by company number rather than VAT number, and it only covers public-sector suppliers.

## Part 2: Proof of concept

### Sample

I downloaded the Companies House Free Company Data Product snapshot of 1 November 2026, and queried it directly with DuckDB, without loading it into a database: 5,711,779 rows (evidence/2026-11-13_ch_sql.txt).

I kept companies with status Active and category Private Limited Company or Public Limited Company: 4,765,570 companies. These are the legal entities a procurement team invoices and pays. I excluded 839 companies whose accounts type is ACCOUNTS TYPE NOT AVAILABLE, because they cannot be assigned to a stratum. I split the population by the type of accounts each company last filed. This is the only field in the snapshot that says something about size and activity: dormant, newly incorporated with no accounts yet, small, large (full, group, medium), and subsidiaries. After that, I drew 50 companies per stratum, and 30 subsidiaries. A proportional sample of 230 would have contained about 4 large companies and 2 subsidiaries, too few to say anything about them. The cost is that the overall rates have to be weighted by each stratum’s share of the population before they describe the UK as a whole. Within each stratum, companies are ordered by md5(CompanyNumber || seed) and the first N are kept. This is a random order that is fixed by the seed, so anyone can reproduce the same 230 companies (src/draw_sample.sql). I re-ran the query three days later and got an identical file (evidence/2026-11-16_sample_reproducibility-check.txt).

| Stratum | Accounts category | Population | Share | Sampled |
|---|---|---|---|---|
| dormant | DORMANT | 513,818 | 10.8% | 50 |
| new | NO ACCOUNTS FILED | 1,139,643 | 23.9% | 50 |
| small | MICRO ENTITY, TOTAL EXEMPTION FULL/SMALL, UNAUDITED ABRIDGED, SMALL, AUDITED ABRIDGED, PARTIAL EXEMPTION | 2,983,724 | 62.6% | 50 |
| large | FULL, GROUP, MEDIUM | 92,795 | 1.9% | 50 |
| subsidiary | AUDIT / FILING EXEMPTION SUBSIDIARY | 34,751 | 0.7% | 30 |

### Matching rule

My rule is simple, and every step exists because of a real case I ran into. The code is in src/match.py and every case below is a test in tests/test_match.py.

1. Wrong checksum → rejected. When I checked HH Development Group, I first copied its company number (11994089) instead of its VAT number by mistake. It failed the checksum straight away.
2. HMRC name ≠ Companies House name → rejected, whatever the address says. Getthelabel and Inn Collection Bidco 2 had the same address as the company HMRC returned, but it was a different company.
3. Same name + same postcode → tier A.
4. Same name + different postcode + no other company has exactly that name in Companies House → tier B. Deswik and Cadlux: Companies House has their accountant’s address, HMRC has the address where they actually work.
5. Anything else → review. It doesn’t get published.

What “same name” means: I only ignore upper/lower case, punctuation, extra spaces and LIMITED vs LTD. So “T.I. THERMAL IMAGING LIMITED” and “T I THERMAL IMAGING LTD” are the same name. I never remove words: “BIDCO 2” and “TOPCO” stay different.

The price I chose to pay: Mane Contract Services is rejected, because HMRC shows the name without “Limited”. It is probably the same company, but I prefer a missing number to a wrong one.

Why tier B exists: 3 of the 7 numbers confirmed through Endole are tier B. A rule that required the same postcode would have thrown them away, even though they are correct.

### Verification against HMRC

To be honest about how I checked:

- My HMRC API credentials only work in the sandbox (HMRC’s test environment). In production they return “invalid client”. I asked for production access on 15.11.2026.
- So I checked every number in this report by hand, on the gov.uk VAT checker. HMRC’s answers, with the date of each check, are in data/hmrc_recorded.csv (Endole and websites) and data/commoncrawl/verified.csv (Common Crawl).
- The code can also ask HMRC directly through the API (src/run.py --hmrc api), and saves every answer in evidence/hmrc/. I tested it in the sandbox, but not in production.

### Results on the sample (Endole, every fifth company)

| Stratum | Checked | Number found | Tier A | Tier B | Rejected |
|---|---|---|---|---|---|
| dormant | 10 | 1 | 1 | 0 | 0 |
| large | 10 | 1 | 0 | 1 | 0 |
| new | 10 | 0 | 0 | 0 | 0 |
| small | 10 | 5 | 3 | 2 | 0 |
| subsidiary | 6 | 0 | 0 | 0 | 0 |
| **total** | **46** | **7** | **4** | **3** | **0** |

What the table says:

- I found a VAT number for 7 of the 46 companies: 15% (95% interval: 6%–29%). But it changes a lot from group to group: 5 of 10 small companies, 0 of 10 new ones.
- Why 0 for new companies: they were all incorporated between December 2024 and October 2026. Most of them are probably still below the VAT registration threshold, so they likely don’t have a VAT number at all.
- Why only 1 of 10 for large companies: most of them are holding companies or financial vehicles (Nando’s Finance, Urbanest UK Camley Street GP1, GRIF045). They don’t sell anything themselves, so the VAT number usually belongs to another company in the group.
- Because my sample has the same number of companies in every group, 15% is not a UK-wide figure. If I weight each group by its real share of the population (small companies are 62.6% of it), the estimate goes up to about 33%. But with only 10 companies per group, this number is very uncertain.

### False-positive rate: what I measured and how

My definition of a false positive: a VAT number put next to a company, while HMRC has it registered under another company’s name.

Before my rule (how often the source itself is wrong):

- Websites: 2 of 2 numbers belonged to another company
- Common Crawl: 3 of 20 (15%, 95% interval: 3%–38%)
- Endole: 0 of 7 (95% interval: 0%–41%, because 7 numbers are not enough to say more)

After my rule: none of the numbers I accepted (16 from Common Crawl + 7 from Endole) is registered at HMRC under another name. But I have to be honest: this is guaranteed by how the rule works, because it rejects exactly those cases. So it is not proof that the real false-positive rate is 0.

The risk that remains: another entity with exactly the same name, for example a sole trader trading as “Smith Building Services” next to “Smith Building Services Ltd”. I can’t measure this without an independent source, like real invoices where I know for sure which company issued them.

### What these numbers don't capture

- The sample is small: 7 confirmed numbers from Endole and 20 checked pairs from Common Crawl. That’s enough to see patterns, but not enough to promise 0% wrong numbers.
- “Not found” means two different things: the company is not VAT registered, or it is registered and I just didn’t find the number. The groups help me guess (dormant and new companies are probably not registered; small ones I probably missed), but I can’t separate them for sure.
- VAT groups: Inn Collection Bidco 2 is probably covered by Inn Collection Topco’s VAT number, but HMRC doesn’t tell me that. So I count it as “not found”, even if in real life its invoices might carry Topco’s number.
- Endole can change: I don’t know where its data comes from or how often it is updated, so the same check could give different results next month.

## Part 3: With real resources

### What I would build

1. Run my Common Crawl scan on the whole archive. On my laptop one file takes about 3.3 seconds, so all 100,000 files would take about 92 hours in a single process. Running in parallel on 100 machines in the same AWS region as the archive (us-east-1), it would take about 1 hour (cost below).
2. Check every pair through the HMRC API instead of by hand. The API allows 3 requests per second per application. At that rate, 1 million checks take about 93 hours (almost 4 days) with one application. This is slower than the Common Crawl scan itself, so HMRC becomes the most time consuming, not the crawling.
3. Apply my matching rule to everything. It is already written and tested on the real cases I found (src/match.py, tests/test_match.py).
4. Link subsidiaries to their parent company using Companies House’s free PSC data (people with significant control). This way, instead of “not found”, I could mark a company like Inn Collection Bidco 2 as “probably covered by the VAT number of Inn Collection Topco”.
5. License data from the companies Endole gets its numbers from (credit reference agencies, list brokers), and run it through the same HMRC check and matching rule. My Endole test showed the numbers exist somewhere upstream; with a budget, I would pay for them properly instead of copying them.
6. An annotation team that checks a random sample every month (for example 200 numbers) against real invoices. This is the only way to measure the risk my rule can’t see: two different entities with exactly the same name.

### Cost per company

This is a rough estimate. I separate what I measured from what I assumed.

What I measured (10 files):

- about 3.3 seconds per file
- 216 linkable pairs in 10 files, so about 21.6 per file
- 16 of 20 checked pairs accepted by my rule (80%)

The calculation for the whole archive (100,000 files):

- Compute: 100,000 files × 3.3 s = 330,000 s ≈ 92 machine-hours. On a small AWS machine (t3.small, $0.0208 per hour) that’s about $2; on a bigger one (t3.medium, $0.0416 per hour) about $4. The Common Crawl data itself is free and sits in the same AWS region (us-east-1).
- HMRC checks: free, but limited to 3 per second. At most 2,160,000 pairs ÷ 3 per second = 720,000 s ≈ 8.3 days with one application.
- Manual audit (assumed): 200 numbers per month × 2 minutes each ≈ 6.7 hours per month. At an assumed £15 per hour, that’s about £100 per month, £1,200 per year.

Cost per company:

- Upper bound: 2,160,000 pairs × 80% accepted ≈ 1,730,000 companies. One year of running costs (≈ £1,200 audit + a few dollars of compute) ÷ 1,730,000 ≈ less than 0.1 pence per company.
- Even if the real number of distinct companies is 10 times lower (about 173,000), it’s still under 1 penny per company.

What this tells me: the money cost is tiny. The real costs are time (8 days of HMRC checks because of the rate limit), people (the audit), and the engineering work to build and maintain the pipeline, which I haven’t counted here.

The biggest unknown is the number of companies. 2,160,000 is an upper bound: the same company appears on many pages and in many files, and with only 10 files I can’t see how often. Only a bigger test (for example 1,000 files) would tell me the real number.

### What breaks first

- Groups of companies. The parent company’s VAT number shows up on the subsidiaries’ pages. In my Common Crawl test this happened in 3 of 20 checked pairs (15%), and on websites in both cases I found. My rule catches it, but every such case is a number I lose.
- Saturation. Big companies appear on thousands of pages, small ones on very few. The more files I scan, the more often I find the same companies again, and the fewer new ones I get per file. This is why I can’t trust a simple multiplication of my 10 files.
- The HMRC rate limit. At 3 checks per second, HMRC becomes the bottleneck long before the crawling does: about 8 days for 2 million pairs with one application.
- Old pages. Common Crawl keeps pages that may be months or years old. A company can deregister for VAT, change its name, or be dissolved, and the old page still shows the old number. Every number has to be checked again at HMRC before it is used.

### What I would monitor

- The rejection rate at HMRC, for each source. If it suddenly goes up for one source, something changed there (a site layout, a broken scanner, a new kind of group page), and I would stop using that source until I know why.
- How many numbers become invalid at each monthly re-check. Companies deregister for VAT all the time. If this number jumps, my data is getting old faster than I thought.
- The result of the monthly manual audit. It’s the only check that can catch what my rule can’t see: two different entities with exactly the same name. If the audit finds even one wrong number, I need to look at the rule again.

## Debate topics

### Enumerating valid numbers against HMRC's checker

A UK VAT number has 9 digits, and the last two are a checksum. With the checksum rule my code uses (from python-stdnum), 28,869,645 of the 1 billion possible 9-digit numbers are valid: about 2.9%. I counted them exactly. HMRC allows 3 requests per second per application, so checking all of them would take about 9.6 million seconds: 111 days with one application.

Making it faster means getting around HMRC’s limit, with many applications or proxies. That is exactly what the limit is there to prevent, and I wouldn’t build a product on breaking the terms of the service that the whole product depends on.

My strongest argument: even if it were allowed, it doesn’t solve the hard part. Enumeration gives me pairs of VAT number → name and address. But linking that name to the right company is still the problem, and my own data shows it:

- Inn Collection: HMRC returns “Inn Collection Topco Ltd”. In Companies House there are 31 “Inn Collection” companies at the same postcode. Matching by name and address could easily pick the wrong one, and a fuzzy match scores 86.2 for the wrong company.
- Deswik: HMRC has the company’s working address in London, Companies House has its accountant’s address in Beaconsfield. Matching by address would miss a correct number.

Also, about half of the VAT register are sole traders and partnerships, which are not in Companies House at all, and their names are personal data.

So is it a good idea? As a way to collect the whole register: no, because of the terms and the 111 days. As a small check on a sample, with HMRC’s agreement, it could tell me how many registered numbers my other sources miss. But it doesn’t replace the matching problem, it just moves it.

### Keeping the dataset current

- Check every number again at HMRC on a schedule, for example every month. Companies deregister for VAT, change their name, or get dissolved all the time, and a number that was right last month can be wrong today.
- Keep the date of the last check on every row. I already do this (checked_on in my files). The customer should see how fresh each number is, not just the number.
- When a number stops being valid, don’t delete it silently. I would mark it as “no longer valid since [date]” and keep the history. A customer matching old invoices still needs to know that the number used to belong to that company.
- Watch Companies House for changes. The monthly snapshot shows name changes, dissolutions and new companies. A name change means the HMRC name check has to run again, and a new company is a new candidate to search for.

### Knowing the dataset is wrong at scale

There is no complete dataset to compare against, so I would use three signals instead:

- A random audit every month. Take a random sample of published numbers (for example 200) and check them by hand against real invoices or the company itself. With 0 errors in 200, I could say the real error rate is very likely below about 2%. That’s the only way to see errors my rule can’t catch, like two entities with exactly the same name.
- The rejection rate per source. If HMRC starts rejecting many more numbers from one source than usual, that source has changed or broken, even before any customer notices.
- The customer’s own third. The procurement team already has VAT numbers for about a third of their 40,000 suppliers. That’s a ready-made reference set: I can run my pipeline on those suppliers without looking at their numbers, then compare. It tells me how many I find (coverage) and how many I get wrong, on exactly the kind of companies the customer cares about.

### Sources I would not use in a product

- Endole, and sites built on top of it (like vatnumber.co.uk). It worked well in my test (7 of 7 correct), but I don’t know where its VAT numbers come from, I probably don’t have the right to resell them, and the whole product would depend on another company’s database that can change or disappear. I would use it only for research, as I did here, to see that the data exists somewhere upstream.
- Company websites without the HMRC check. On my websites test, both numbers I found belonged to another company in the same group. And in Common Crawl, even pages showing both the VAT number and the company number were wrong in 3 of 20 cases. A number from a web page is only a candidate, never an answer.
- Enumerating the HMRC checker with proxies. Going around HMRC’s rate limit means breaking the terms of the service the whole product relies on to verify its numbers.

## Beyond the UK

Germany: discovery gets easier, verification gets harder.

- Discovery: German websites must have an “Impressum” (legal notice), and if the company has a VAT ID (USt-IdNr, “DE” + 9 digits), it must be listed there. So the number I struggled to find in the UK is legally required on the website in Germany. The group problem would still exist, but the Impressum also names the legal entity and its register number (Handelsregister), which is the same trick I used with the UK company number.
- Verification: in VIES, Germany only confirms that a number is valid. It doesn’t return the name and address, so I can’t do my name check the way I do with HMRC. Germany’s own service (the BZSt) can confirm whether a name and address match a number, but you have to send it the name yourself, and you need a German VAT ID to use it.
- Would my pipeline survive? The scanning part, yes: just a different pattern (“USt-IdNr” instead of “VAT”). The matching rule, no: I would have to rebuild it around a “does this name match?” answer instead of comparing names myself.

A country where the VAT number is barely “discovered”: Belgium. There, the VAT number is the company’s registration number in the business register (KBO/BCE) with “BE” in front. Once you know the company, you know its VAT number, and the register says whether it is VAT registered. Discovery is almost free.

What this means for choosing markets: I would start with countries where the VAT number comes straight from the business register (Belgium) or must be published by law (Germany), and leave the UK-style problem, where the number is hidden and the checker only works backwards, for later.

## How I used AI tools

I used Claude Code throughout this project, and I want to be clear about what it did and what I did.

What AI did:

- Reviewed my first plan and pointed out its problems: fuzzy matching, the enumeration idea with proxies, and the checksum arithmetic.
- Wrote some of the code: the matching rule (src/match.py) from the rules I agreed on, the HMRC client, the Common Crawl scanner, the SQL that combines the results, and the tests.
- Ran queries on the Companies House data (for example the 31 “Inn Collection” companies at one postcode, and how many companies share a postcode).
- Calculated the confidence intervals, the weighted estimate and the exact number of checksum-valid VAT numbers.
- Looked up information online: Endole’s data sources, the EORI pages, AWS prices.

What I did:

- Downloaded the Companies House snapshot and explored it myself in DuckDB, before writing any code.
- Set up my HMRC developer application and tested the API in the sandbox.
- Drew the 230-company sample (the SQL, the strata and the reasons behind them).
- Found the sources myself: Endole, Endole’s page about where its data comes from, vatnumber.co.uk, and HMRC’s rate limit.
- All the manual checks: 10 companies on websites, 46 companies on Endole, 17 searches in Peppol, and every HMRC check by hand on gov.uk (11 numbers from websites and Endole, 20 pairs from Common Crawl).
- The decisions: which sources to try and when to stop, accepting tier B after Deswik, rejecting Mane Contract Services, and what to leave out.
- Wrote all sections of this README myself.

What I rejected: my own first idea of enumerating all valid numbers through HMRC with proxies, after understanding the terms and the matching problem. I also rejected a “loopholes” approach suggested by another AI tool, which presented enumeration as a ready-made 100% accurate solution. My own data showed it isn’t.

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

Common Crawl test (streams about 640 MB, keeps only the matching pages):

```
.venv/bin/python src/commoncrawl.py 0 1 2 3 4 5 6 7 8 9
duckdb < src/commoncrawl_summary.sql
.venv/bin/python src/commoncrawl_verify.py
```

To re-draw the sample, download the Companies House snapshot (BasicCompanyDataAsOneFile-2026-11-01) from https://download.companieshouse.gov.uk/en_output.html, unzip it into `data/raw/`, then run `duckdb < src/draw_sample.sql`. The output should be identical to the committed `data/sample_230.csv`.

## Repo layout

```
src/draw_sample.sql           draws the 230-company sample from Companies House
src/match.py                  the rule deciding whether a VAT number belongs to a company
src/hmrc.py                   HMRC "Check a UK VAT number" API client
src/run.py                    applies the rule to the manual checks and writes the results
src/commoncrawl.py            scans Common Crawl files for pages with a VAT and a company number
src/commoncrawl_summary.sql   combines the Common Crawl hits and picks pairs to verify
src/commoncrawl_verify.py     applies the rule to the Common Crawl pairs checked at HMRC
tests/test_match.py           the rule tested on the real cases from the manual checks
data/sample_230.csv           the sample
data/candidates.csv           what I found for each company checked, and where
data/hmrc_recorded.csv        HMRC's answer for each number found
data/ch_context.csv           per sampled company: companies sharing its name and its postcode
data/results/                 outputs of src/run.py
data/commoncrawl/             Common Crawl hits, pairs, and the 20 verified pairs
evidence/                     raw outputs behind the numbers in this document
```
