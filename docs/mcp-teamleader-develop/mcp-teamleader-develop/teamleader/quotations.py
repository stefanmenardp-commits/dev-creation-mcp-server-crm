"""
Teamleader Quotations Module

Responsibilities:
- List / get quotations
- Create / update quotations
- Add line items (products) via grouped_lines
- Link a contact or company to a deal (which owns the quotation)

Key API facts:
- quotations.create requires: customer (type + id), department_id
- quotations.update uses grouped_lines (replaces entirely — GET first, then PUT)
- Each line item requires: description, quantity, unit_price, tax_rate_id
- add_contact/company work on the deal linked to the quotation via deals.update
"""

import requests
from teamleader.auth import get_valid_access_token
from teamleader.deals import update_deal_customer
from teamleader.tax_rates import get_default_tax_rate_id


BASE_URL = "https://api.teamleader.eu"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_access_token()}"}


# ==========================================================
# List / Get
# ==========================================================

# _ means that it is a function used only internally in the Python file, not imported from another file.
def _get_quotation_raw(quotation_id: str) -> dict:
    """
    Internal: returns the raw API response for a quotation (for write operations). Call in get_quotation and _add_line_item
    """

    response = requests.post(
        f"{BASE_URL}/quotations.info",
        headers=_headers(),
        json={"id": quotation_id}
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return response.json().get("data", {})


def _format_grouped_lines(raw_grouped_lines: list) -> list:
    """
    Converts raw API grouped_lines into a clean display format for the LLM.
    """

    result = []
    for group in raw_grouped_lines:
        # section can be a string or {"title": "..."} depending on context
        section_raw = group.get("section", "")
        if isinstance(section_raw, dict):
            section_title = section_raw.get("title", "")
        else:
            section_title = section_raw

        items = []
        for item in group.get("line_items", []):
            unit_price = item.get("unit_price") or {}
            total = item.get("total") or {}
            tax = item.get("tax") or {}
            items.append({
                "description": item.get("description"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "unit_price": unit_price.get("amount"),
                "currency": unit_price.get("currency"),
                "tax_rate_id": tax.get("id"),
                "tax_rate": tax.get("rate"),
                "discount": item.get("discount"),
                "total": total.get("amount"),
            })
        result.append({
            "section": section_title,
            "line_items": items,
        })
    return result


def list_quotations(
    deal_id: str = None,
    page: int = 1,
    size: int = 20
) -> dict:
    """
    Returns a paginated list of quotations with full line item details.

    Args:
        deal_id (str): Filter by deal UUID
        page (int): Page number (default: 1)
        size (int): Results per page (default: 20)

    Returns:
        dict: List of quotations with grouped_lines detail, or error
    """

    payload = {"page": {"size": size, "number": page}}

    if deal_id:
        payload["filter"] = {"ids": [deal_id]}

    response = requests.post(
        f"{BASE_URL}/quotations.list",
        headers=_headers(),
        json=payload
    )

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    quotations = []

    for q in data.get("data", []):
        detail = get_quotation(q["id"])
        if "error" in detail:
            # Fallback to summary data if detail call fails
            quotations.append({
                "id": q.get("id"),
                "name": q.get("name"),
                "status": q.get("status"),
                "currency": q.get("currency"),
                "expiry": q.get("expiry"),
                "grouped_lines": [],
            })
        else:
            quotations.append(detail)

    return {"quotations": quotations, "count": len(quotations)}


def get_quotation(quotation_id: str) -> dict:
    """
    Returns the full details of a single quotation including formatted line items.

    Args:
        quotation_id (str): Quotation UUID

    Returns:
        dict: Quotation details with grouped_lines, or error
    """

    raw = _get_quotation_raw(quotation_id)
    if "error" in raw:
        return raw

    totals = raw.get("total") or {}

    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "status": raw.get("status"),
        "currency": raw.get("currency"),
        "expiry": raw.get("expiry"),
        "total_excl_tax": (totals.get("tax_exclusive") or {}).get("amount"),
        "total_incl_tax": (totals.get("tax_inclusive") or {}).get("amount"),
        "grouped_lines": _format_grouped_lines(raw.get("grouped_lines", [])),
    }


# ==========================================================
# Create / Update
# ==========================================================

def create_quotation(
    deal_id: str,
    currency: str = "EUR",
    exchange_rate: float = 1,
    expiry: str = None
) -> dict:
    """
    Creates a new quotation linked to an existing deal.

    Args:
        deal_id (str): Deal UUID (opportunity created beforehand)
        currency (str): Currency code (default: EUR)
        exchange_rate (float): Currency exchange rate (default: 1 for EUR)
        expiry (str): Expiry date ISO format (e.g. "2026-12-31")

    Returns:
        dict: Created quotation ID or error
    """

    payload = {
        "deal_id": deal_id,
        "currency": {"code": currency, "exchange_rate": exchange_rate},
    }

    if expiry:
        payload["expiry"] = {"expires_after": expiry, "action_after_expiry": "none"}

    response = requests.post(
        f"{BASE_URL}/quotations.create",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 201):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    data = response.json()
    quotation_id = data.get("data", {}).get("id")

    return {
        "id": quotation_id,
        "deal_id": deal_id,
        "message": "Quotation created successfully"
    }


def update_quotation(
    quotation_id: str,
    currency: str = None,
    expiry: str = None
) -> dict:
    """
    Updates metadata (currency, expiry) of an existing quotation.

    Args:
        quotation_id (str): Quotation UUID
        currency (str): New currency code
        expiry (str): New expiry date ISO format

    Returns:
        dict: Confirmation or error
    """

    payload = {"id": quotation_id}

    if currency:
        payload["currency"] = {"code": currency, "exchange_rate": 1}
    if expiry:
        payload["expiry"] = {"expires_after": expiry, "action_after_expiry": "none"}

    response = requests.post(
        f"{BASE_URL}/quotations.update",
        headers=_headers(),
        json=payload
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {"id": quotation_id, "message": "Quotation updated successfully"}


# ==========================================================
# Add line item
# ==========================================================

def add_product_to_quotation(
    quotation_id: str,
    product_id: str,
    description: str,
    quantity: float,
    unit_price: float,
    tax_rate_id: str = None,
    section: str = "",
    extended_description: str = None,
    unit_of_measure_id: str = None,
    discount_value: float = None,
    purchase_price_amount: float = None,
    purchase_price_currency: str = None,
    periodicity_unit: str = None,
    periodicity_period: int = None,
) -> dict:
    """
    Adds a Teamleader product (linked by product_id) as a line item to a quotation.
    Fetches current grouped_lines first to preserve existing items.
    """

    discount = {"value": discount_value, "type": "percentage"} if discount_value is not None else None

    return _add_line_item(
        quotation_id=quotation_id,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        tax_rate_id=tax_rate_id,
        section=section,
        product_id=product_id,
        extended_description=extended_description,
        unit_of_measure_id=unit_of_measure_id,
        discount=discount,
        purchase_price_amount=purchase_price_amount,
        purchase_price_currency=purchase_price_currency,
        periodicity_unit=periodicity_unit,
        periodicity_period=periodicity_period,
    )


def add_custom_line_to_quotation(
    quotation_id: str,
    description: str,
    quantity: float,
    unit_price: float,
    tax_rate_id: str = None,
    section: str = "",
    extended_description: str = None,
    unit_of_measure_id: str = None,
    discount_value: float = None,
    purchase_price_amount: float = None,
    purchase_price_currency: str = None,
    periodicity_unit: str = None,
    periodicity_period: int = None,
) -> dict:
    """
    Adds a custom (free-form) line item to a quotation, not linked to any product.
    Fetches current grouped_lines first to preserve existing items.
    """

    discount = {"value": discount_value, "type": "percentage"} if discount_value is not None else None

    return _add_line_item(
        quotation_id=quotation_id,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        tax_rate_id=tax_rate_id,
        section=section,
        product_id=None,
        extended_description=extended_description,
        unit_of_measure_id=unit_of_measure_id,
        discount=discount,
        purchase_price_amount=purchase_price_amount,
        purchase_price_currency=purchase_price_currency,
        periodicity_unit=periodicity_unit,
        periodicity_period=periodicity_period,
    )


def _add_line_item(
    quotation_id: str,
    description: str,
    quantity: float,
    unit_price: float,
    tax_rate_id: str,
    section: str,
    product_id: str = None,
    extended_description: str = None,
    unit_of_measure_id: str = None,
    discount: dict = None,
    purchase_price_amount: float = None,
    purchase_price_currency: str = None,
    periodicity_unit: str = None,
    periodicity_period: int = None,
) -> dict:
    """
    Shared implementation: appends a line item to a quotation's grouped_lines.
    """

    raw = _get_quotation_raw(quotation_id)
    if "error" in raw:
        return raw

    # Resolve default tax rate if not provided
    if not tax_rate_id:
        tax_rate_id = get_default_tax_rate_id()
        if not tax_rate_id:
            return {"error": "tax_rate_id is required and no default French TVA 20% rate was found."}

    new_item = {
        "description": description,
        "quantity": quantity,
        "unit_price": {"amount": unit_price, "tax": "excluding"},
        "tax_rate_id": tax_rate_id,
    }

    if extended_description:
        new_item["extended_description"] = extended_description

    if unit_of_measure_id:
        new_item["unit_of_measure_id"] = unit_of_measure_id

    if product_id:
        new_item["product_id"] = product_id

    if discount is not None:
        new_item["discount"] = discount

    if purchase_price_amount is not None and purchase_price_currency:
        new_item["purchase_price"] = {
            "amount": purchase_price_amount,
            "currency": purchase_price_currency,
        }

    if periodicity_unit and periodicity_period is not None:
        new_item["periodicity"] = {
            "unit": periodicity_unit,
            "period": periodicity_period,
        }

    # Rebuild grouped_lines from raw API format, preserving existing items
    # and converting tax.id → tax_rate_id for the write payload
    existing = raw.get("grouped_lines", [])
    grouped_lines = _normalize_grouped_lines(existing)

    if grouped_lines:
        # Match section by title (after normalization section is {"title": "..."})
        target = next(
            (g for g in grouped_lines if g.get("section", {}).get("title", "") == section),
            None
        )
        if target is not None:
            # Existing section found — append to it
            target.setdefault("line_items", []).append(new_item)
        else:
            # No matching section found — create a new one
            grouped_lines.append({"section": {"title": section}, "line_items": [new_item]})
    else:
        grouped_lines = [{"section": {"title": section}, "line_items": [new_item]}]

    response = requests.post(
        f"{BASE_URL}/quotations.update",
        headers=_headers(),
        json={"id": quotation_id, "grouped_lines": grouped_lines}
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "quotation_id": quotation_id,
        "message": "Line item added to quotation successfully"
    }


def _normalize_grouped_lines(grouped_lines: list) -> list:
    """
    Converts the read format (from quotations.info) to the write format
    (for quotations.update): tax.id → tax_rate_id, section string → {"title": "..."}.
    """

    result = []
    for group in grouped_lines:
        section_raw = group.get("section", "")
        if isinstance(section_raw, dict):
            section_title = section_raw.get("title", "")
        else:
            section_title = section_raw

        normalized_items = []
        for item in group.get("line_items", []):
            tax = item.get("tax") or {}
            raw_price = item.get("unit_price") or {}
            normalized_item = {
                "description": item.get("description", ""),
                "quantity": item.get("quantity"),
                "unit_price": {"amount": raw_price.get("amount"), "tax": "excluding"},
                "tax_rate_id": tax.get("id"),
            }
            if item.get("extended_description"):
                normalized_item["extended_description"] = item["extended_description"]
            if item.get("unit_of_measure_id"):
                normalized_item["unit_of_measure_id"] = item["unit_of_measure_id"]
            if item.get("product_id"):
                normalized_item["product_id"] = item["product_id"]
            if item.get("discount") is not None:
                normalized_item["discount"] = item["discount"]
            if item.get("purchase_price") is not None:
                normalized_item["purchase_price"] = item["purchase_price"]
            if item.get("periodicity") is not None:
                normalized_item["periodicity"] = item["periodicity"]
            normalized_items.append(normalized_item)

        result.append({
            "section": {"title": section_title},
            "line_items": normalized_items,
        })

    return result


# ==========================================================
# Update / Delete line item
# ==========================================================

def update_line_in_quotation(
    quotation_id: str,
    section_title: str,
    line_description: str,
    new_description: str = None,
    new_quantity: float = None,
    new_unit_price: float = None,
    new_tax_rate_id: str = None,
    new_extended_description: str = None,
    new_discount_value: float = None,
) -> dict:
    """
    Updates an existing line item in a quotation, identified by
    section title and line description. Only provided fields are changed.
    """

    raw = _get_quotation_raw(quotation_id)
    if "error" in raw:
        return raw

    grouped_lines = _normalize_grouped_lines(raw.get("grouped_lines", []))

    found = False
    for group in grouped_lines:
        if group.get("section", {}).get("title", "") != section_title:
            continue
        for item in group.get("line_items", []):
            if item.get("description") == line_description:
                if new_description is not None:
                    item["description"] = new_description
                if new_quantity is not None:
                    item["quantity"] = new_quantity
                if new_unit_price is not None:
                    item["unit_price"] = {
                        "amount": new_unit_price,
                        "tax": "excluding",
                    }
                if new_tax_rate_id is not None:
                    item["tax_rate_id"] = new_tax_rate_id
                if new_extended_description is not None:
                    item["extended_description"] = new_extended_description
                if new_discount_value is not None:
                    item["discount"] = {
                        "value": new_discount_value,
                        "type": "percentage",
                    }
                found = True
                break
        if found:
            break

    if not found:
        return {
            "error": (
                f"Line '{line_description}' not found "
                f"in section '{section_title}'"
            )
        }

    response = requests.post(
        f"{BASE_URL}/quotations.update",
        headers=_headers(),
        json={"id": quotation_id, "grouped_lines": grouped_lines},
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "quotation_id": quotation_id,
        "message": "Line item updated successfully",
    }


def delete_line_from_quotation(
    quotation_id: str,
    section_title: str,
    line_description: str,
) -> dict:
    """
    Deletes a line item from a quotation, identified by section title
    and line description. Removes the section if it becomes empty.
    """

    raw = _get_quotation_raw(quotation_id)
    if "error" in raw:
        return raw

    grouped_lines = _normalize_grouped_lines(raw.get("grouped_lines", []))

    found = False
    for group in grouped_lines:
        if group.get("section", {}).get("title", "") != section_title:
            continue
        items = group.get("line_items", [])
        for i, item in enumerate(items):
            if item.get("description") == line_description:
                items.pop(i)
                found = True
                break
        if found:
            break

    if not found:
        return {
            "error": (
                f"Line '{line_description}' not found "
                f"in section '{section_title}'"
            )
        }

    # Remove empty sections
    grouped_lines = [
        g for g in grouped_lines if g.get("line_items")
    ]

    response = requests.post(
        f"{BASE_URL}/quotations.update",
        headers=_headers(),
        json={"id": quotation_id, "grouped_lines": grouped_lines},
    )

    if response.status_code not in (200, 204):
        return {"error": f"API Error {response.status_code}: {response.text}"}

    return {
        "quotation_id": quotation_id,
        "message": "Line item deleted successfully",
    }


# ==========================================================
# Link contact / company (via deal)
# ==========================================================

def add_contact_to_quotation(deal_id: str, contact_id: str) -> dict:
    """
    Links a contact as the customer of the deal associated with a quotation.

    Args:
        deal_id (str): Deal UUID linked to the quotation
        contact_id (str): Contact UUID

    Returns:
        dict: Confirmation or error
    """

    return update_deal_customer(deal_id, "contact", contact_id)


def add_company_to_quotation(deal_id: str, company_id: str) -> dict:
    """
    Links a company as the customer of the deal associated with a quotation.

    Args:
        deal_id (str): Deal UUID linked to the quotation
        company_id (str): Company UUID

    Returns:
        dict: Confirmation or error
    """

    return update_deal_customer(deal_id, "company", company_id)
