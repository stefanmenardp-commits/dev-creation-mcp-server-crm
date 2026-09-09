"""
Teamleader MCP Server

Responsibilities:
- Register tools exposed to Claude
- Delegate execution to business API layer
- Return structured responses to the LLM

Important:
This layer must remain transport-only.
It must not contain authentication logic,
process lifecycle logic, or subprocess handling.
"""

import asyncio
import json

from mcp.server import Server
from mcp.types import Tool, TextContent

from teamleader.contacts import list_contacts, create_contact, update_contact
from teamleader.companies import list_companies, create_company, update_company, link_contact_to_company, unlink_contact_from_company
from teamleader.products import list_products, create_product, update_product
from teamleader.deals import list_deals, get_deal, create_deal
from teamleader.tax_rates import list_tax_rates
from teamleader.quotations import (
    list_quotations,
    get_quotation,
    create_quotation,
    update_quotation,
    add_product_to_quotation,
    add_custom_line_to_quotation,
    update_line_in_quotation,
    delete_line_from_quotation,
    add_contact_to_quotation,
    add_company_to_quotation,
)


# ==========================================================
# Server Initialization
# ==========================================================

server = Server("teamleader")


# ==========================================================
# Tool Registration
# ==========================================================

# answers “what tools do you have?”
@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Returns the list of available tools exposed to Claude.
    """

    return [

        # ── Companies ─────────────────────────────────────
        Tool(
            name="list_companies",
            description="List Teamleader companies, optionally filtered by name, email, or phone number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Search term: company name, email address, or phone number."},
                    "page": {"type": "integer", "description": "Page number (default: 1)."},
                    "size": {"type": "integer", "description": "Results per page (default: 20)."},
                },
                "required": []
            }
        ),
        Tool(
            name="create_company",
            description="Create a new company in Teamleader.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Company name (required)."},
                    "email": {"type": "string", "description": "Email address."},
                    "phone": {"type": "string", "description": "Phone number."},
                    "vat_number": {"type": "string", "description": "VAT number."},
                    "language": {"type": "string", "description": "Language code (e.g. 'fr', 'en', 'nl')."},
                    "website": {"type": "string", "description": "Website URL."},
                    "address_line": {"type": "string", "description": "Street address (e.g. 'Dok Noord 3A 101')."},
                    "postal_code": {"type": "string", "description": "Postal code (e.g. '9000')."},
                    "city": {"type": "string", "description": "City name (e.g. 'Ghent')."},
                    "country": {"type": "string", "description": "Country code (e.g. 'BE', 'FR'). Required to set an address."},
                    "address_type": {"type": "string", "description": "Address type (default: 'primary').", "enum": ["primary", "invoicing", "delivery", "visiting"]},
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="update_company",
            description="Update an existing company in Teamleader. Only provided fields are changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "Company UUID."},
                    "name": {"type": "string", "description": "New company name."},
                    "email": {"type": "string", "description": "New email address."},
                    "phone": {"type": "string", "description": "New phone number."},
                    "vat_number": {"type": "string", "description": "New VAT number."},
                    "language": {"type": "string", "description": "New language code (e.g. 'fr', 'en', 'nl')."},
                    "website": {"type": "string", "description": "New website URL."},
                    "address_line": {"type": "string", "description": "Street address (e.g. 'Dok Noord 3A 101')."},
                    "postal_code": {"type": "string", "description": "Postal code (e.g. '9000')."},
                    "city": {"type": "string", "description": "City name (e.g. 'Ghent')."},
                    "country": {"type": "string", "description": "Country code (e.g. 'BE', 'FR'). Required to set an address."},
                    "address_type": {"type": "string", "description": "Address type (default: 'primary').", "enum": ["primary", "invoicing", "delivery", "visiting"]},
                },
                "required": ["company_id"]
            }
        ),
        Tool(
            name="link_contact_to_company",
            description="Link a contact to a company in Teamleader, with optional job position and decision maker flag.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "Contact UUID."},
                    "company_id": {"type": "string", "description": "Company UUID."},
                    "position": {"type": "string", "description": "Job title / position within the company."},
                    "decision_maker": {"type": "boolean", "description": "Whether this contact is a decision maker."},
                },
                "required": ["contact_id", "company_id"]
            }
        ),
        Tool(
            name="unlink_contact_from_company",
            description="Unlink a contact from a company in Teamleader.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "Contact UUID."},
                    "company_id": {"type": "string", "description": "Company UUID."},
                },
                "required": ["contact_id", "company_id"]
            }
        ),

        # ── Contacts ──────────────────────────────────────
        Tool(
            name="list_contacts",
            description="List Teamleader contacts, optionally filtered by name, first name, email, or phone number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Search term: full name, first name, last name, email address, or phone number."},
                    "page": {"type": "integer", "description": "Page number (default: 1)."},
                    "size": {"type": "integer", "description": "Results per page (default: 20)."},
                },
                "required": []
            }
        ),
        Tool(
            name="create_contact",
            description="Create a new contact in Teamleader.",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_name": {"type": "string", "description": "Last name (required)."},
                    "first_name": {"type": "string", "description": "First name."},
                    "email": {"type": "string", "description": "Email address."},
                    "phone": {"type": "string", "description": "Phone number."},
                    "language": {"type": "string", "description": "Language code (e.g. 'fr', 'en', 'nl')."},
                },
                "required": ["last_name"]
            }
        ),
        Tool(
            name="update_contact",
            description="Update an existing contact in Teamleader. Only provided fields are changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "Contact UUID."},
                    "first_name": {"type": "string", "description": "New first name."},
                    "last_name": {"type": "string", "description": "New last name."},
                    "email": {"type": "string", "description": "New email address."},
                    "phone": {"type": "string", "description": "New phone number."},
                    "language": {"type": "string", "description": "New language code (e.g. 'fr', 'en', 'nl')."},
                },
                "required": ["contact_id"]
            }
        ),

        # ── Tax Rates ─────────────────────────────────────
        Tool(
            name="list_tax_rates",
            description="List all available Teamleader tax rates with their IDs, descriptions, and percentages.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        # ── Products ──────────────────────────────────────
        Tool(
            name="list_products",
            description="List Teamleader products, optionally filtered by name or code. Returns full pricing details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Search term: product name or code."},
                    "page": {"type": "integer", "description": "Page number (default: 1)."},
                    "size": {"type": "integer", "description": "Results per page (default: 20)."},
                },
                "required": []
            }
        ),
        Tool(
            name="create_product",
            description="Create a new product in Teamleader.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product name (required)."},
                    "description": {"type": "string", "description": "Product description (Markdown)."},
                    "code": {"type": "string", "description": "Product code / reference."},
                    "selling_price": {"type": "number", "description": "Selling price excl. tax."},
                    "currency": {"type": "string", "description": "Currency code (default: EUR)."},
                    "purchase_price": {"type": "number", "description": "Purchase price."},
                    "tax_rate_id": {"type": "string", "description": "Tax rate UUID."},
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="update_product",
            description="Update an existing product in Teamleader. Only provided fields are changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product UUID."},
                    "name": {"type": "string", "description": "New product name."},
                    "description": {"type": "string", "description": "New description (Markdown)."},
                    "code": {"type": "string", "description": "New product code / reference."},
                    "selling_price": {"type": "number", "description": "New selling price excl. tax."},
                    "currency": {"type": "string", "description": "Currency code (default: EUR)."},
                    "purchase_price": {"type": "number", "description": "New purchase price."},
                    "tax_rate_id": {"type": "string", "description": "New tax rate UUID."},
                },
                "required": ["product_id"]
            }
        ),

        # ── Deals ─────────────────────────────────────────
        Tool(
            name="list_deals",
            description="List Teamleader deals (opportunities), optionally filtered by search term or customer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Search term: filters on deal title, reference, and customer name."},
                    "customer_type": {"type": "string", "description": "Filter by customer type: 'contact' or 'company'."},
                    "customer_id": {"type": "string", "description": "Filter by customer UUID."},
                    "page": {"type": "integer", "description": "Page number (default: 1)."},
                    "size": {"type": "integer", "description": "Results per page (default: 20)."}
                },
                "required": []
            }
        ),
        Tool(
            name="get_deal",
            description="Get the details of a Teamleader deal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "string", "description": "Deal UUID."}
                },
                "required": ["deal_id"]
            }
        ),
        Tool(
            name="create_deal",
            description="Create a new deal (opportunity) linked to a contact or company.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Deal title."},
                    "customer_type": {"type": "string", "description": "'contact' or 'company'."},
                    "customer_id": {"type": "string", "description": "Contact or company UUID."}
                },
                "required": ["title", "customer_type", "customer_id"]
            }
        ),

        # ── Quotations ────────────────────────────────────
        Tool(
            name="list_quotations",
            description="List Teamleader quotations, optionally filtered by deal ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "string", "description": "Filter by deal UUID."},
                    "page": {"type": "integer", "description": "Page number (default: 1)."},
                    "size": {"type": "integer", "description": "Results per page (default: 20)."}
                },
                "required": []
            }
        ),
        Tool(
            name="get_quotation",
            description="Get the full details of a Teamleader quotation including line items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quotation_id": {"type": "string", "description": "Quotation UUID."}
                },
                "required": ["quotation_id"]
            }
        ),
        Tool(
            name="create_quotation",
            description="Create a new quotation linked to an existing deal (opportunity).",
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "string", "description": "Deal UUID (opportunity created beforehand)."},
                    "currency": {"type": "string", "description": "Currency code.", "default": "EUR"},
                    "expiry": {"type": "string", "description": "Expiry date (ISO format, e.g. '2026-12-31')."},
                },
                "required": ["deal_id"]
            }
        ),
        Tool(
            name="update_quotation",
            description="Update the currency or expiry date of an existing quotation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quotation_id": {"type": "string", "description": "Quotation UUID."},
                    "currency": {"type": "string", "description": "New currency code."},
                    "expiry": {"type": "string", "description": "New expiry date (ISO format)."},
                },
                "required": ["quotation_id"]
            }
        ),
        Tool(
            name="add_product_to_quotation",
            description="Add a Teamleader product (linked by product_id) as a line item to a quotation. Preserves existing lines. If tax_rate_id is omitted, defaults to the French 20% TVA.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quotation_id": {"type": "string", "description": "Quotation UUID."},
                    "product_id": {"type": "string", "description": "Teamleader product UUID to link (informational reference)."},
                    "description": {"type": "string", "description": "Line item description."},
                    "quantity": {"type": "number", "description": "Quantity (e.g. 3)."},
                    "unit_price": {"type": "number", "description": "Unit price excl. tax (e.g. 123.3)."},
                    "tax_rate_id": {"type": "string", "description": "Tax rate UUID. Defaults to French 20% TVA if not provided."},
                    "section_title": {"type": "string", "description": "Title of the section group (maps to section.title). Defaults to first section if omitted."},
                    "extended_description": {"type": "string", "description": "Additional description using Markdown formatting."},
                    "unit_of_measure_id": {"type": "string", "description": "Unit of measure UUID (nullable, only if explicitly requested)."},
                    "discount_value": {"type": "number", "description": "Discount percentage 0-100 (e.g. 10 for 10%). Only include if the user explicitly requests a discount."},
                    "purchase_price_amount": {"type": "number", "description": "Purchase price amount (nullable, only if explicitly requested)."},
                    "purchase_price_currency": {"type": "string", "description": "Purchase price currency code (e.g. EUR). Required when purchase_price_amount is set."},
                    "periodicity_unit": {"type": "string", "description": "Periodicity unit (nullable, only if explicitly requested).", "enum": ["week", "month", "year"]},
                    "periodicity_period": {"type": "integer", "description": "Periodicity period number (e.g. 1 or 2). Required when periodicity_unit is set."}
                },
                "required": ["quotation_id", "product_id", "description", "quantity", "unit_price"]
            }
        ),
        Tool(
            name="add_custom_line_to_quotation",
            description="Add a free-form line item (not linked to any product) to a quotation. Preserves existing lines. If tax_rate_id is omitted, defaults to the French 20% TVA.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quotation_id": {"type": "string", "description": "Quotation UUID."},
                    "description": {"type": "string", "description": "Line item description."},
                    "quantity": {"type": "number", "description": "Quantity (e.g. 3)."},
                    "unit_price": {"type": "number", "description": "Unit price excl. tax (e.g. 123.3)."},
                    "tax_rate_id": {"type": "string", "description": "Tax rate UUID. Defaults to French 20% TVA if not provided."},
                    "section_title": {"type": "string", "description": "Title of the section group (maps to section.title). Defaults to first section if omitted."},
                    "extended_description": {"type": "string", "description": "Additional description using Markdown formatting."},
                    "unit_of_measure_id": {"type": "string", "description": "Unit of measure UUID (nullable, only if explicitly requested)."},
                    "discount_value": {"type": "number", "description": "Discount percentage 0-100 (e.g. 10 for 10%). Only include if the user explicitly requests a discount."},
                    "purchase_price_amount": {"type": "number", "description": "Purchase price amount (nullable, only if explicitly requested)."},
                    "purchase_price_currency": {"type": "string", "description": "Purchase price currency code (e.g. EUR). Required when purchase_price_amount is set."},
                    "periodicity_unit": {"type": "string", "description": "Periodicity unit (nullable, only if explicitly requested).", "enum": ["week", "month", "year"]},
                    "periodicity_period": {"type": "integer", "description": "Periodicity period number (e.g. 1 or 2). Required when periodicity_unit is set."}
                },
                "required": ["quotation_id", "description", "quantity", "unit_price"]
            }
        ),
        Tool(
            name="update_line_in_quotation",
            description="Update an existing line item in a quotation. Identifies the line by section title and line description. Only provided fields are changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quotation_id": {"type": "string", "description": "Quotation UUID."},
                    "section_title": {"type": "string", "description": "Title of the section containing the line."},
                    "line_description": {"type": "string", "description": "Current description of the line item to update."},
                    "new_description": {"type": "string", "description": "New description for the line item."},
                    "new_quantity": {"type": "number", "description": "New quantity."},
                    "new_unit_price": {"type": "number", "description": "New unit price excl. tax."},
                    "new_tax_rate_id": {"type": "string", "description": "New tax rate UUID."},
                    "new_extended_description": {"type": "string", "description": "New extended description (Markdown)."},
                    "new_discount_value": {"type": "number", "description": "New discount percentage 0-100."},
                },
                "required": ["quotation_id", "section_title", "line_description"]
            }
        ),
        Tool(
            name="delete_line_from_quotation",
            description="Delete a line item from a quotation. Identifies the line by section title and line description. Removes the section if it becomes empty.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quotation_id": {"type": "string", "description": "Quotation UUID."},
                    "section_title": {"type": "string", "description": "Title of the section containing the line."},
                    "line_description": {"type": "string", "description": "Description of the line item to delete."},
                },
                "required": ["quotation_id", "section_title", "line_description"]
            }
        ),
        Tool(
            name="add_contact_to_quotation",
            description="Link a contact as the customer of the deal associated with a quotation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "string", "description": "Deal UUID linked to the quotation."},
                    "contact_id": {"type": "string", "description": "Contact UUID."}
                },
                "required": ["deal_id", "contact_id"]
            }
        ),
        Tool(
            name="add_company_to_quotation",
            description="Link a company as the customer of the deal associated with a quotation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "string", "description": "Deal UUID linked to the quotation."},
                    "company_id": {"type": "string", "description": "Company UUID."}
                },
                "required": ["deal_id", "company_id"]
            }
        ),
    ]


# ==========================================================
# Helpers
# ==========================================================

def _ok(data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

def _err(message: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error: {message}")]


# ==========================================================
# Tool Execution
# ==========================================================

# responds to “run this tool with these arguments”
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Executes a tool requested by Claude.
    """

    try:

        # ── Companies ─────────────────────────────────────
        if name == "list_companies":
            result = list_companies(
                term=arguments.get("term"),
                page=arguments.get("page", 1),
                size=arguments.get("size", 20),
            )
            return _ok(result)

        elif name == "create_company":
            result = create_company(
                name=arguments["name"],
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                vat_number=arguments.get("vat_number"),
                language=arguments.get("language"),
                website=arguments.get("website"),
                address_line=arguments.get("address_line"),
                postal_code=arguments.get("postal_code"),
                city=arguments.get("city"),
                country=arguments.get("country"),
                address_type=arguments.get("address_type", "primary"),
            )
            return _ok(result)

        elif name == "update_company":
            result = update_company(
                company_id=arguments["company_id"],
                name=arguments.get("name"),
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                vat_number=arguments.get("vat_number"),
                language=arguments.get("language"),
                website=arguments.get("website"),
                address_line=arguments.get("address_line"),
                postal_code=arguments.get("postal_code"),
                city=arguments.get("city"),
                country=arguments.get("country"),
                address_type=arguments.get("address_type", "primary"),
            )
            return _ok(result)

        elif name == "link_contact_to_company":
            result = link_contact_to_company(
                contact_id=arguments["contact_id"],
                company_id=arguments["company_id"],
                position=arguments.get("position"),
                decision_maker=arguments.get("decision_maker"),
            )
            return _ok(result)

        elif name == "unlink_contact_from_company":
            result = unlink_contact_from_company(
                contact_id=arguments["contact_id"],
                company_id=arguments["company_id"],
            )
            return _ok(result)

        # ── Contacts ──────────────────────────────────────
        elif name == "list_contacts":
            result = list_contacts(
                term=arguments.get("term"),
                page=arguments.get("page", 1),
                size=arguments.get("size", 20),
            )
            return _ok(result)

        elif name == "create_contact":
            result = create_contact(
                last_name=arguments["last_name"],
                first_name=arguments.get("first_name"),
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                language=arguments.get("language"),
            )
            return _ok(result)

        elif name == "update_contact":
            result = update_contact(
                contact_id=arguments["contact_id"],
                first_name=arguments.get("first_name"),
                last_name=arguments.get("last_name"),
                email=arguments.get("email"),
                phone=arguments.get("phone"),
                language=arguments.get("language"),
            )
            return _ok(result)

        # ── Tax Rates ─────────────────────────────────────
        elif name == "list_tax_rates":
            result = list_tax_rates()
            return _ok(result)

        # ── Products ──────────────────────────────────────
        elif name == "list_products":
            result = list_products(
                term=arguments.get("term"),
                page=arguments.get("page", 1),
                size=arguments.get("size", 20),
            )
            return _ok(result)

        elif name == "create_product":
            result = create_product(
                name=arguments["name"],
                description=arguments.get("description"),
                code=arguments.get("code"),
                selling_price=arguments.get("selling_price"),
                currency=arguments.get("currency", "EUR"),
                purchase_price=arguments.get("purchase_price"),
                tax_rate_id=arguments.get("tax_rate_id"),
            )
            return _ok(result)

        elif name == "update_product":
            result = update_product(
                product_id=arguments["product_id"],
                name=arguments.get("name"),
                description=arguments.get("description"),
                code=arguments.get("code"),
                selling_price=arguments.get("selling_price"),
                currency=arguments.get("currency", "EUR"),
                purchase_price=arguments.get("purchase_price"),
                tax_rate_id=arguments.get("tax_rate_id"),
            )
            return _ok(result)

        # ── Deals ─────────────────────────────────────────
        elif name == "list_deals":
            result = list_deals(
                term=arguments.get("term"),
                customer_type=arguments.get("customer_type"),
                customer_id=arguments.get("customer_id"),
                page=arguments.get("page", 1),
                size=arguments.get("size", 20),
            )
            return _ok(result)

        elif name == "get_deal":
            result = get_deal(arguments["deal_id"])
            return _ok(result)

        elif name == "create_deal":
            result = create_deal(
                title=arguments["title"],
                customer_type=arguments["customer_type"],
                customer_id=arguments["customer_id"],
            )
            return _ok(result)

        # ── Quotations ────────────────────────────────────
        elif name == "list_quotations":
            result = list_quotations(
                deal_id=arguments.get("deal_id"),
                page=arguments.get("page", 1),
                size=arguments.get("size", 20),
            )
            return _ok(result)

        elif name == "get_quotation":
            result = get_quotation(arguments["quotation_id"])
            return _ok(result)

        elif name == "create_quotation":
            result = create_quotation(
                deal_id=arguments["deal_id"],
                currency=arguments.get("currency", "EUR"),
                expiry=arguments.get("expiry"),
            )
            return _ok(result)

        elif name == "update_quotation":
            result = update_quotation(
                quotation_id=arguments["quotation_id"],
                currency=arguments.get("currency"),
                expiry=arguments.get("expiry"),
            )
            return _ok(result)

        elif name == "add_product_to_quotation":
            result = add_product_to_quotation(
                quotation_id=arguments["quotation_id"],
                product_id=arguments["product_id"],
                description=arguments["description"],
                quantity=arguments["quantity"],
                unit_price=arguments["unit_price"],
                tax_rate_id=arguments.get("tax_rate_id"),
                section=arguments.get("section_title", ""),
                extended_description=arguments.get("extended_description"),
                unit_of_measure_id=arguments.get("unit_of_measure_id"),
                discount_value=arguments.get("discount_value"),
                purchase_price_amount=arguments.get("purchase_price_amount"),
                purchase_price_currency=arguments.get("purchase_price_currency"),
                periodicity_unit=arguments.get("periodicity_unit"),
                periodicity_period=arguments.get("periodicity_period"),
            )
            return _ok(result)

        elif name == "add_custom_line_to_quotation":
            result = add_custom_line_to_quotation(
                quotation_id=arguments["quotation_id"],
                description=arguments["description"],
                quantity=arguments["quantity"],
                unit_price=arguments["unit_price"],
                tax_rate_id=arguments.get("tax_rate_id"),
                section=arguments.get("section_title", ""),
                extended_description=arguments.get("extended_description"),
                unit_of_measure_id=arguments.get("unit_of_measure_id"),
                discount_value=arguments.get("discount_value"),
                purchase_price_amount=arguments.get("purchase_price_amount"),
                purchase_price_currency=arguments.get("purchase_price_currency"),
                periodicity_unit=arguments.get("periodicity_unit"),
                periodicity_period=arguments.get("periodicity_period"),
            )
            return _ok(result)

        elif name == "update_line_in_quotation":
            result = update_line_in_quotation(
                quotation_id=arguments["quotation_id"],
                section_title=arguments["section_title"],
                line_description=arguments["line_description"],
                new_description=arguments.get("new_description"),
                new_quantity=arguments.get("new_quantity"),
                new_unit_price=arguments.get("new_unit_price"),
                new_tax_rate_id=arguments.get("new_tax_rate_id"),
                new_extended_description=arguments.get("new_extended_description"),
                new_discount_value=arguments.get("new_discount_value"),
            )
            return _ok(result)

        elif name == "delete_line_from_quotation":
            result = delete_line_from_quotation(
                quotation_id=arguments["quotation_id"],
                section_title=arguments["section_title"],
                line_description=arguments["line_description"],
            )
            return _ok(result)

        elif name == "add_contact_to_quotation":
            result = add_contact_to_quotation(
                deal_id=arguments["deal_id"],
                contact_id=arguments["contact_id"],
            )
            return _ok(result)

        elif name == "add_company_to_quotation":
            result = add_company_to_quotation(
                deal_id=arguments["deal_id"],
                company_id=arguments["company_id"],
            )
            return _ok(result)

        return _err(f"Unknown tool: {name}")

    except Exception as e:
        # Important:
        # We do not handle OAuth lifecycle here.
        # If authentication requires restart,
        # auth.py will terminate the process.
        return _err(str(e))


# ==========================================================
# Server Entry Point
# ==========================================================

async def main():
    """
    Starts the MCP stdio server.
    """

    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
