# UK VAT Identifier Discovery

Status: work in progress. Started 2026-11-12.

## The question

Can a dataset of UK company VAT numbers be built from the open web, and what does it cost in coverage, accuracy and money? HMRC confirms a VAT number you already have. It does not tell you a company's number.

## Short answer

<!-- Write this last. Three or four sentences a busy reader can act on:
     for which companies it works, with what coverage and false-positive rate, on what sample, and where it stops working. -->

## Repo layout

```
README.md              this document (the deliverable)
docs/decision-log.md   dated journal: what I tried, what came back, what I decided
docs/definitions.md    what "found", "confirmed" and "false positive" mean here
docs/hypotheses.md     every source idea, tested or not, with its status
docs/dead-ends.md      sources that failed, with the reason and the evidence
docs/sampling.md       how the sample was drawn
evidence/              raw outputs behind every number in this document
data/sample/           the sample itself
data/results/          outputs of the proof of concept
data/raw/              large downloads, not committed
src/                   code
```

## How to reproduce

<!-- Exact commands, in order. Python version, how to get the input data, what credentials are needed. -->

## Part 1: Research

### What I learned that wasn't obvious at the start

### Sources tested

| Source | What I expected | Tested on (n) | What came back | Status | Evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Dead ends

<!-- Summary here, full write-ups in docs/dead-ends.md. -->

## Part 2: Proof of concept

### Sample

<!-- How it was drawn and why it is representative. Details in docs/sampling.md. -->

### Method

### Verification against HMRC

<!-- How every reported number was checked, and how "valid number" was separated from "this company's number". -->

### Results

| Metric | Value | n | Interval | How measured |
|---|---|---|---|---|
|  |  |  |  |  |

### What these numbers don't capture

## Part 3: With real resources

### What changes with a budget

### Cost per company

### What breaks first

### What I'd monitor in production

## Debate topics

### Enumerating valid numbers against HMRC's checker

### Keeping the dataset current

### Knowing the dataset is wrong at scale

### Sources I would not use in a product

## Beyond the UK

<!-- Optional. One country compared properly against the UK. -->

## How I used AI tools

<!-- The brief allows them. Say plainly what you used them for and which decisions were yours. -->
