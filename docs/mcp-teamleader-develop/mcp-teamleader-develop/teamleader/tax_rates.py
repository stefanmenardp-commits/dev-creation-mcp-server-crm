"""
Teamleader Tax Rates Module

Responsibilities:
- List available tax rates from Teamleader
- Provide a default French 20% TVA rate ID
"""

import requests
from teamleader.auth import get_valid_access_token


BASE_URL = "https://api.teamleader.eu"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_access_token()}"}


def list_tax_rates() -> dict:
    """
    Returns the list of available tax rates from Teamleader.

    Returns:
        dict: List of tax rates with id, description, and rate, or error
    """

    response = requests.post(
        f"{BASE_URL}/taxRates.list",
        headers=_headers(),
        json={}
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    rates = []

    for r in data.get("data", []):
        rates.append({
            "id": r.get("id"),
            "description": r.get("description"),
            "rate": r.get("rate"),
        })

    return {"tax_rates": rates, "count": len(rates)}


def get_default_tax_rate_id() -> str | None:
    """
    Looks up and returns the tax rate ID for the French 20% TVA.
    Matches by rate value == 20 or description containing "20".

    Used when adding a task line to a quote (add_product_to_quotation or add_custom_line_to_quotation).
    Without specifying the tax type. By default, adds the tax line associated with France.
    
    Returns:
        str: Tax rate UUID, or None if not found
    """

    result = list_tax_rates()
    if "error" in result:
        return None

    for rate in result.get("tax_rates", []):
        rate_value = rate.get("rate")
        desc = (rate.get("description") or "").lower()
        if rate_value == 20 or "20%" in desc or "tva 20" in desc:
            return rate.get("id")

    return None
