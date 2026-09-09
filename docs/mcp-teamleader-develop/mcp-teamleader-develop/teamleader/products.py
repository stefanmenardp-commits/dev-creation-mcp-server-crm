"""
Teamleader Products Module

Responsibilities:
- Search products
- Create products
- Update products
"""

import requests
from teamleader.auth import get_valid_access_token


BASE_URL = "https://api.teamleader.eu"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_access_token()}"}


# ==========================================================
# Search
# ==========================================================

def list_products(
    term: str = None,
    page: int = 1,
    size: int = 20
) -> dict:
    """
    Lists products, optionally filtered by name or code.

    Args:
        term (str): Search on product name or code
        page (int): Page number (default: 1)
        size (int): Results per page (default: 20)

    Returns:
        dict: List of matching products or error
    """

    payload = {"page": {"size": size, "number": page}}

    if term:
        payload["filter"] = {"term": term}

    response = requests.post(
        f"{BASE_URL}/products.list",
        headers=_headers(),
        json=payload
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()

    if not data.get("data"):
        return {"products": [], "count": 0}

    products = []
    for p in data["data"]:
        info = _get_product_info(p.get("id"))
        if "error" in info:
            # Fallback to list data if info call fails
            selling_price = p.get("selling_price") or {}
            products.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "code": p.get("code"),
                "selling_price": selling_price.get("amount"),
                "currency": selling_price.get("currency"),
                "tax_id": None,
            })
        else:
            products.append(info)

    return {"products": products, "count": len(products)}


def _get_product_info(product_id: str) -> dict:
    """
    Fetches full product details via products.info.
    """

    response = requests.post(
        f"{BASE_URL}/products.info",
        headers=_headers(),
        json={"id": product_id}
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    p = response.json().get("data", {})
    selling_price = p.get("selling_price") or {}
    purchase_price = p.get("purchase_price") or {}
    tax = p.get("tax") or {}

    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "code": p.get("code"),
        "description": p.get("description"),
        "selling_price": selling_price.get("amount"),
        "purchase_price": purchase_price.get("amount"),
        "currency": selling_price.get("currency"),
        "tax_id": tax.get("id"),
        "unit": p.get("unit"),
    }


# ==========================================================
# Create
# ==========================================================

def create_product(
    name: str,
    description: str = None,
    code: str = None,
    selling_price: float = None,
    currency: str = "EUR",
    purchase_price: float = None,
    tax_rate_id: str = None
) -> dict:
    """
    Creates a new product in Teamleader.

    Args:
        name (str): Product name (required)
        description (str): Product description (Markdown)
        code (str): Product code / reference
        selling_price (float): Selling price excl. tax
        currency (str): Currency code (default: EUR)
        purchase_price (float): Purchase price
        tax_rate_id (str): Tax rate UUID

    Returns:
        dict: Created product ID or error
    """

    payload = {"name": name}

    if description:
        payload["description"] = description
    if code:
        payload["code"] = code
    if selling_price is not None:
        payload["selling_price"] = {
            "amount": selling_price,
            "currency": currency,
            "tax": "excluding"
        }
    if purchase_price is not None:
        payload["purchase_price"] = {
            "amount": purchase_price,
            "currency": currency
        }
    if tax_rate_id:
        payload["tax_rate_id"] = tax_rate_id

    response = requests.post(
        f"{BASE_URL}/products.add",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 201):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    product_id = data.get("data", {}).get("id")

    return {
        "id": product_id,
        "name": name,
        "message": "Product created successfully"
    }


# ==========================================================
# Update
# ==========================================================

def update_product(
    product_id: str,
    name: str = None,
    description: str = None,
    code: str = None,
    selling_price: float = None,
    currency: str = "EUR",
    purchase_price: float = None,
    tax_rate_id: str = None
) -> dict:
    """
    Updates an existing product in Teamleader.

    Args:
        product_id (str): Product UUID (required)
        name (str): New product name
        description (str): New description (Markdown)
        code (str): New product code
        selling_price (float): New selling price excl. tax
        currency (str): Currency code (default: EUR)
        purchase_price (float): New purchase price
        tax_rate_id (str): New tax rate UUID

    Returns:
        dict: Confirmation or error
    """

    payload = {"id": product_id}

    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if code is not None:
        payload["code"] = code
    if selling_price is not None:
        payload["selling_price"] = {
            "amount": selling_price,
            "currency": currency,
            "tax": "excluding"
        }
    if purchase_price is not None:
        payload["purchase_price"] = {
            "amount": purchase_price,
            "currency": currency
        }
    if tax_rate_id is not None:
        payload["tax_rate_id"] = tax_rate_id

    response = requests.post(
        f"{BASE_URL}/products.update",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "id": product_id,
        "message": "Product updated successfully"
    }
