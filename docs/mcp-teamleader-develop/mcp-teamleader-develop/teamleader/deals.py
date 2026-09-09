"""
Teamleader Deals Module

Responsibilities:
- List / get deals (opportunities)
- Create deals
- Update deal customer (contact or company)
"""

import requests
from teamleader.auth import get_valid_access_token


BASE_URL = "https://api.teamleader.eu"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_access_token()}"}


# ==========================================================
# List / Get
# ==========================================================

def list_deals(
    term: str = None,
    customer_type: str = None,
    customer_id: str = None,
    page: int = 1,
    size: int = 20
) -> dict:
    """
    Returns a paginated list of deals, optionally filtered by
    search term and/or customer.

    Args:
        term (str): Search on title, reference, and customer name
        customer_type (str): "contact" or "company"
        customer_id (str): Customer UUID
        page (int): Page number (default: 1)
        size (int): Results per page (default: 20)

    Returns:
        dict: List of deals or error
    """

    payload = {"page": {"size": size, "number": page}}

    f = {}
    if term:
        f["term"] = term
    if customer_type and customer_id:
        f["customer"] = {"type": customer_type, "id": customer_id}
    if f:
        payload["filter"] = f

    response = requests.post(
        f"{BASE_URL}/deals.list",
        headers=_headers(),
        json=payload
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    deals = []

    for d in data.get("data", []):
        lead = d.get("lead") or {}
        customer = lead.get("customer") or {}
        deals.append({
            "id": d.get("id"),
            "title": d.get("title"),
            "status": d.get("status"),
            "reference": d.get("reference"),
            "currency": d.get("currency"),
            "customer_type": customer.get("type"),
            "customer_id": customer.get("id"),
        })

    return {"deals": deals, "count": len(deals)}


def get_deal(deal_id: str) -> dict:
    """
    Returns the details of a single deal.

    Args:
        deal_id (str): Deal UUID

    Returns:
        dict: Deal details or error
    """

    response = requests.post(
        f"{BASE_URL}/deals.info",
        headers=_headers(),
        json={"id": deal_id}
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    d = response.json().get("data", {})
    lead = d.get("lead") or {}
    customer = lead.get("customer") or {}

    return {
        "id": d.get("id"),
        "title": d.get("title"),
        "status": d.get("status"),
        "reference": d.get("reference"),
        "currency": d.get("currency"),
        "customer_type": customer.get("type"),
        "customer_id": customer.get("id"),
    }


# ==========================================================
# Create
# ==========================================================

def create_deal(
    title: str,
    customer_type: str,
    customer_id: str
) -> dict:
    """
    Creates a new deal linked to a contact or company.

    Args:
        title (str): Deal title
        customer_type (str): "contact" or "company"
        customer_id (str): Contact or company UUID

    Returns:
        dict: Created deal ID or error
    """

    response = requests.post(
        f"{BASE_URL}/deals.create",
        headers=_headers(),
        json={
            "title": title,
            "lead": {
                "customer": {"type": customer_type, "id": customer_id}
            }
        }
    )

    if response.status_code not in (200, 201):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    deal_id = data.get("data", {}).get("id")

    return {
        "id": deal_id,
        "title": title,
        "message": "Deal created successfully"
    }


# ==========================================================
# Update customer
# ==========================================================

def update_deal_customer(
    deal_id: str,
    customer_type: str,
    customer_id: str
) -> dict:
    """
    Updates the customer (lead) of an existing deal.

    Args:
        deal_id (str): Deal UUID
        customer_type (str): "contact" or "company"
        customer_id (str): Contact or company UUID

    Returns:
        dict: Confirmation or error
    """

    response = requests.post(
        f"{BASE_URL}/deals.update",
        headers=_headers(),
        json={
            "id": deal_id,
            "lead": {
                "customer": {"type": customer_type, "id": customer_id}
            }
        }
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "deal_id": deal_id,
        "customer_type": customer_type,
        "customer_id": customer_id,
        "message": f"{customer_type.capitalize()} linked to deal successfully"
    }
