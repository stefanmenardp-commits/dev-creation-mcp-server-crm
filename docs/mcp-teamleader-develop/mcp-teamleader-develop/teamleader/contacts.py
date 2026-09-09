"""
Teamleader Contacts Module

Responsibilities:
- Search contacts
- Create contacts
- Update contacts
"""

import requests
from teamleader.auth import get_valid_access_token


BASE_URL = "https://api.teamleader.eu"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_access_token()}"}


# ==========================================================
# Search
# ==========================================================

def list_contacts(
    term: str = None,
    page: int = 1,
    size: int = 20
) -> dict:
    """
    Lists contacts, optionally filtered by name, first name,
    email, or phone number.

    Args:
        term (str): Search term (name, first name, email, or phone)
        page (int): Page number (default: 1)
        size (int): Results per page (default: 20)

    Returns:
        dict: List of contacts or error
    """

    payload = {"page": {"size": size, "number": page}}

    if term:
        payload["filter"] = {"term": term}

    response = requests.post(
        f"{BASE_URL}/contacts.list",
        headers=_headers(),
        json=payload
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()

    if not data.get("data"):
        return {"contacts": [], "count": 0}

    contacts = []
    for contact in data["data"]:
        first = contact.get("first_name", "")
        last = contact.get("last_name", "")
        emails = contact.get("emails") or []
        phones = contact.get("telephones") or []
        address = contact.get("primary_address") or {}

        contacts.append({
            "id": contact.get("id"),
            "full_name": f"{first} {last}".strip(),
            "email": emails[0].get("email") if emails else None,
            "phone": phones[0].get("number") if phones else None,
            "country": address.get("country"),
        })

    return {"contacts": contacts, "count": len(contacts)}


# ==========================================================
# Create
# ==========================================================

def create_contact(
    last_name: str,
    first_name: str = None,
    email: str = None,
    phone: str = None,
    language: str = None
) -> dict:
    """
    Creates a new contact in Teamleader.

    Args:
        last_name (str): Last name (required)
        first_name (str): First name
        email (str): Email address
        phone (str): Phone number
        language (str): Language code (e.g. "fr", "en", "nl")

    Returns:
        dict: Created contact ID or error
    """

    payload = {"last_name": last_name}

    if first_name:
        payload["first_name"] = first_name
    if email:
        payload["emails"] = [{"type": "primary", "email": email}]
    if phone:
        payload["telephones"] = [{"type": "phone", "number": phone}]
    if language:
        payload["language"] = language

    response = requests.post(
        f"{BASE_URL}/contacts.add",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 201):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    contact_id = data.get("data", {}).get("id")

    return {
        "id": contact_id,
        "message": "Contact created successfully"
    }


# ==========================================================
# Update
# ==========================================================

def update_contact(
    contact_id: str,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    phone: str = None,
    language: str = None
) -> dict:
    """
    Updates an existing contact in Teamleader.

    Args:
        contact_id (str): Contact UUID (required)
        first_name (str): New first name
        last_name (str): New last name
        email (str): New email address
        phone (str): New phone number
        language (str): New language code

    Returns:
        dict: Confirmation or error
    """

    payload = {"id": contact_id}

    if first_name is not None:
        payload["first_name"] = first_name
    if last_name is not None:
        payload["last_name"] = last_name
    if email is not None:
        payload["emails"] = [{"type": "primary", "email": email}]
    if phone is not None:
        payload["telephones"] = [{"type": "phone", "number": phone}]
    if language is not None:
        payload["language"] = language

    response = requests.post(
        f"{BASE_URL}/contacts.update",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "id": contact_id,
        "message": "Contact updated successfully"
    }
