"""
Teamleader Companies Module

Responsibilities:
- Search companies
- Create companies
- Update companies
- Link / unlink contacts to companies
"""

import requests
from teamleader.auth import get_valid_access_token


BASE_URL = "https://api.teamleader.eu"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_access_token()}"}


# ==========================================================
# Search
# ==========================================================

def list_companies(
    term: str = None,
    page: int = 1,
    size: int = 20
) -> dict:
    """
    Lists companies, optionally filtered by name, email,
    or phone number.

    Args:
        term (str): Search term (name, email, or phone)
        page (int): Page number (default: 1)
        size (int): Results per page (default: 20)

    Returns:
        dict: List of companies or error
    """

    payload = {"page": {"size": size, "number": page}}

    if term:
        payload["filter"] = {"term": term}

    response = requests.post(
        f"{BASE_URL}/companies.list",
        headers=_headers(),
        json=payload
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()

    if not data.get("data"):
        return {"companies": [], "count": 0}

    companies = []
    for company in data["data"]:
        emails = company.get("emails") or []
        phones = company.get("telephones") or []
        address = company.get("primary_address") or {}

        companies.append({
            "id": company.get("id"),
            "name": company.get("name"),
            "email": emails[0].get("email") if emails else None,
            "phone": phones[0].get("number") if phones else None,
            "country": address.get("country"),
            "vat_number": company.get("vat_number"),
        })

    return {"companies": companies, "count": len(companies)}


# ==========================================================
# Create
# ==========================================================

def create_company(
    name: str,
    email: str = None,
    phone: str = None,
    vat_number: str = None,
    language: str = None,
    website: str = None,
    address_line: str = None,
    postal_code: str = None,
    city: str = None,
    country: str = None,
    address_type: str = "primary"
) -> dict:
    """
    Creates a new company in Teamleader.

    Args:
        name (str): Company name (required)
        email (str): Email address
        phone (str): Phone number
        vat_number (str): VAT number
        language (str): Language code (e.g. "fr", "en", "nl")
        website (str): Website URL
        address_line (str): Street address (e.g. "Dok Noord 3A 101")
        postal_code (str): Postal code (e.g. "9000")
        city (str): City name (e.g. "Ghent")
        country (str): Country code (e.g. "BE", "FR")
        address_type (str): Address type: primary, invoicing, delivery, visiting

    Returns:
        dict: Created company ID or error
    """

    payload = {"name": name}

    if email:
        payload["emails"] = [{"type": "primary", "email": email}]
    if phone:
        payload["telephones"] = [{"type": "phone", "number": phone}]
    if vat_number:
        payload["vat_number"] = vat_number
    if language:
        payload["language"] = language
    if website:
        payload["website"] = website
    if country:
        address = {
            "line_1": address_line,
            "postal_code": postal_code,
            "city": city,
            "country": country
        }
        payload["addresses"] = [{"type": address_type, "address": address}]

    response = requests.post(
        f"{BASE_URL}/companies.add",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 201):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    company_id = data.get("data", {}).get("id")

    return {
        "id": company_id,
        "name": name,
        "message": "Company created successfully"
    }


# ==========================================================
# Update
# ==========================================================

def update_company(
    company_id: str,
    name: str = None,
    email: str = None,
    phone: str = None,
    vat_number: str = None,
    language: str = None,
    website: str = None,
    address_line: str = None,
    postal_code: str = None,
    city: str = None,
    country: str = None,
    address_type: str = "primary"
) -> dict:
    """
    Updates an existing company in Teamleader.

    Args:
        company_id (str): Company UUID (required)
        name (str): New company name
        email (str): New email address
        phone (str): New phone number
        vat_number (str): New VAT number
        language (str): New language code
        website (str): New website URL
        address_line (str): Street address (e.g. "Dok Noord 3A 101")
        postal_code (str): Postal code (e.g. "9000")
        city (str): City name (e.g. "Ghent")
        country (str): Country code (e.g. "BE", "FR")
        address_type (str): Address type: primary, invoicing, delivery, visiting

    Returns:
        dict: Confirmation or error
    """

    payload = {"id": company_id}

    if name is not None:
        payload["name"] = name
    if email is not None:
        payload["emails"] = [{"type": "primary", "email": email}]
    if phone is not None:
        payload["telephones"] = [{"type": "phone", "number": phone}]
    if vat_number is not None:
        payload["vat_number"] = vat_number
    if language is not None:
        payload["language"] = language
    if website is not None:
        payload["website"] = website
    if country is not None:
        address = {
            "line_1": address_line,
            "postal_code": postal_code,
            "city": city,
            "country": country
        }
        payload["addresses"] = [{"type": address_type, "address": address}]

    response = requests.post(
        f"{BASE_URL}/companies.update",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "id": company_id,
        "message": "Company updated successfully"
    }


# ==========================================================
# Link contact to company
# ==========================================================

def link_contact_to_company(
    contact_id: str,
    company_id: str,
    position: str = None,
    decision_maker: bool = None
) -> dict:
    """
    Links a contact to a company in Teamleader.

    Args:
        contact_id (str): Contact UUID (required)
        company_id (str): Company UUID (required)
        position (str): Job title / position within the company
        decision_maker (bool): Whether this contact is a decision maker

    Returns:
        dict: Confirmation or error
    """

    payload = {
        "id": contact_id,
        "company_id": company_id
    }

    if position is not None:
        payload["position"] = position
    if decision_maker is not None:
        payload["decision_maker"] = decision_maker

    response = requests.post(
        f"{BASE_URL}/contacts.linkToCompany",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "contact_id": contact_id,
        "company_id": company_id,
        "message": "Contact linked to company successfully"
    }


def unlink_contact_from_company(
    contact_id: str,
    company_id: str
) -> dict:
    """
    Unlinks a contact from a company in Teamleader.

    Args:
        contact_id (str): Contact UUID (required)
        company_id (str): Company UUID (required)

    Returns:
        dict: Confirmation or error
    """

    payload = {
        "id": contact_id,
        "company_id": company_id
    }

    response = requests.post(
        f"{BASE_URL}/contacts.unlinkFromCompany",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "contact_id": contact_id,
        "company_id": company_id,
        "message": "Contact unlinked from company successfully"
    }
