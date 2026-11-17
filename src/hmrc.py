"""Ask HMRC who a VAT number is registered to.

Uses HMRC's "Check a UK VAT number" API, version 2.0. Each answer is saved
unchanged under evidence/hmrc/, so every reported number can be traced.

Needs HMRC_CLIENT_ID and HMRC_CLIENT_SECRET in .env. HMRC_BASE_URL picks the
environment: production by default, https://test-api.service.hmrc.gov.uk for
the sandbox (which only knows HMRC's test numbers).
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import requests

PRODUCTION = "https://api.service.hmrc.gov.uk"
EVIDENCE_DIR = Path("evidence/hmrc")


def get_token(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/oauth/token",
        data={
            "client_id": os.environ["HMRC_CLIENT_ID"],
            "client_secret": os.environ["HMRC_CLIENT_SECRET"],
            "grant_type": "client_credentials",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def lookup(vrn: str, token: str, base_url: str) -> dict | None:
    """Return {"name", "postcode"} for a registered number, None if HMRC does not know it.

    vrn is the 9 or 12 digit number without the GB prefix.
    """
    response = requests.get(
        f"{base_url}/organisations/vat/check-vat-number/lookup/{vrn}",
        headers={"Accept": "application/vnd.hmrc.2.0+json", "Authorization": f"Bearer {token}"},
        timeout=20,
    )
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / f"{date.today()}_{vrn}.json").write_text(response.text)

    if response.status_code == 404:
        return None
    response.raise_for_status()
    target = response.json()["target"]
    return {"name": target["name"], "postcode": target["address"].get("postcode", "")}


def base_url() -> str:
    return os.environ.get("HMRC_BASE_URL", PRODUCTION)


if __name__ == "__main__":
    # Quick manual check: python src/hmrc.py 106566322
    import sys

    from dotenv import load_dotenv

    load_dotenv(".env")
    url = base_url()
    print(json.dumps(lookup(sys.argv[1], get_token(url), url), indent=2))
