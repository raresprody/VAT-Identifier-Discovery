"""Decide whether a VAT number belongs to a Companies House company.

The rule, and the case that led to each part of it:

1. No candidate number                     -> "not found"
2. Fails the checksum                      -> reject. Catches typos, such as
                                              copying the company number instead (HH Development).
3. HMRC does not know the number           -> reject.
4. HMRC name differs from Companies House  -> reject, whatever the address says.
                                              Getthelabel and Inn Collection Bidco 2: real numbers
                                              belonging to another company in the same group, at the
                                              same address. A fuzzy score of 86.2 would have accepted
                                              Inn Collection, so names must be equal, not similar.
5. Name equal and postcode equal           -> "tier A"
6. Name equal, postcode differs, and no
   other company has that exact name       -> "tier B". Deswik and Cadlux: Companies House holds
                                              the accountant's address, HMRC the trading address.
7. Name equal, postcode differs, name
   shared by other companies               -> "review": not published.

The postcode is supporting evidence only. Some postcodes are mail-forwarding
addresses shared by tens of thousands of companies (WC2H 9JQ: 89,012), where
an equal postcode proves almost nothing. The name carries the decision.
"""
from __future__ import annotations

import re

from stdnum.gb import vat


def normalise_name(name: str) -> str:
    """Remove differences that do not change which company is meant.

    Only case, punctuation, spacing and the spelling of the legal suffix.
    Words are never dropped, so BIDCO 2 and TOPCO stay different.
    """
    name = name.upper().replace("&", " AND ")
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\bPUBLIC LIMITED COMPANY$", "PLC", name)
    name = re.sub(r"\bLIMITED$", "LTD", name)
    return name


def normalise_postcode(postcode: str) -> str:
    return postcode.upper().replace(" ", "")


def decide(
    candidate: str,
    ch_name: str,
    ch_postcode: str,
    hmrc_name: str | None,
    hmrc_postcode: str | None,
    companies_with_same_name: int,
) -> str:
    if not candidate:
        return "not found"
    if not vat.is_valid(candidate):
        return "reject: checksum"
    if hmrc_name is None:
        return "reject: not registered"
    if normalise_name(hmrc_name) != normalise_name(ch_name):
        return "reject: different company"
    if normalise_postcode(hmrc_postcode or "") == normalise_postcode(ch_postcode):
        return "tier A"
    if companies_with_same_name == 1:
        return "tier B"
    return "review"
