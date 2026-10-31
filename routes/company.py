from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error,
    validate_email
)

company_bp = Blueprint("companies", __name__, url_prefix="/api/companies")


def _attach_company_contacts(cursor, companies):
    """Helper to fetch and attach nested HR contacts and phone numbers to company records."""
    if not companies:
        return companies

    company_ids = [c["company_id"] for c in companies if isinstance(c, dict) and "company_id" in c]
    if not company_ids:
        return companies

    format_strings = ",".join(["%s"] * len(company_ids))

    # Fetch contacts
    cursor.execute(f"""
        SELECT contact_id, company_id, contact_name, designation, email
        FROM company_contact
        WHERE company_id IN ({format_strings})
        ORDER BY company_id ASC, contact_id ASC
    """, tuple(company_ids))

    contacts = cursor.fetchall()
    contact_ids = [c["contact_id"] for c in contacts if isinstance(c, dict) and "contact_id" in c]

    # Fetch contact phones
    phones_by_contact = {}
    if contact_ids:
        cf_strings = ",".join(["%s"] * len(contact_ids))
        cursor.execute(f"""
            SELECT contact_id, phone_number, phone_type
            FROM company_contact_phone
            WHERE contact_id IN ({cf_strings})
            ORDER BY contact_id ASC, (phone_type = 'Work') DESC, phone_number ASC
        """, tuple(contact_ids))
        phones = cursor.fetchall()
        if phones and isinstance(phones, list):
            for p in phones:
                if not isinstance(p, dict) or "contact_id" not in p or "phone_number" not in p:
                    continue
                cid = p["contact_id"]
                if cid not in phones_by_contact:
                    phones_by_contact[cid] = []
                phones_by_contact[cid].append({
                    "phone_number": p["phone_number"],
                    "phone_type": p.get("phone_type", "Work")
                })

    # Group contacts by company
    contacts_by_company = {}
    if contacts and isinstance(contacts, list):
        for c in contacts:
            if not isinstance(c, dict) or "company_id" not in c or "contact_id" not in c:
                continue
            cid = c["company_id"]
            if cid not in contacts_by_company:
                contacts_by_company[cid] = []
            c_phones = phones_by_contact.get(c["contact_id"], [])
            contacts_by_company[cid].append({
                "contact_id": c["contact_id"],
                "company_id": c["company_id"],
                "contact_name": c.get("contact_name", ""),
                "designation": c.get("designation", "HR Contact"),
                "email": c.get("email", ""),
                "phones": c_phones
            })

    # Attach to each company object
    for comp in companies:
        if isinstance(comp, dict):
            cid = comp.get("company_id")
            c_list = contacts_by_company.get(cid, [])
            comp["contacts"] = c_list

            # Backward compatibility fields populated from primary contact
            if c_list:
                primary_c = c_list[0]
                comp["hr_contact_name"] = primary_c["contact_name"]
                comp["hr_email"] = primary_c["email"]
                comp["hr_phone"] = primary_c["phones"][0]["phone_number"] if primary_c["phones"] else ""
            else:
                comp["hr_contact_name"] = ""
                comp["hr_email"] = ""
                comp["hr_phone"] = ""

    return companies


@company_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_companies():
    """Retrieve all recruiting companies with full nested HR contacts and phone numbers."""
    try:
        with get_db_cursor() as (conn, cursor):
            cursor.execute("""
                SELECT 
                    company_id, company_name, industry, website, company_address
                FROM company
                ORDER BY company_id ASC
            """)
            companies = cursor.fetchall()
            _attach_company_contacts(cursor, companies)
            return success_response(data=companies)
    except Exception as e:
        return handle_db_error(e)


@company_bp.route("/<int:company_id>", methods=["GET"])
def get_company_by_id(company_id):
    """Retrieve a single company by ID with full contact information."""
    try:
        with get_db_cursor() as (conn, cursor):
            cursor.execute("""
                SELECT 
                    company_id, company_name, industry, website, company_address
                FROM company
                WHERE company_id = %s
            """, (company_id,))
            company = cursor.fetchone()
            if not company:
                return error_response(f"Company with ID {company_id} not found.", status_code=404)

            _attach_company_contacts(cursor, [company])
            return success_response(data=company)
    except Exception as e:
        return handle_db_error(e)


@company_bp.route("", methods=["POST"], strict_slashes=False)
def create_company():
    """Register a new recruiting company with multiple HR contacts and phone numbers."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    company_name = str(data.get("company_name", "")).strip()
    industry = str(data.get("industry", "")).strip()
    company_address = str(data.get("company_address", "")).strip()

    if not company_name:
        return error_response("Company name is required.")
    if not industry:
        return error_response("Industry is required.")
    if not company_address:
        return error_response("Company address is required.")

    website = data.get("website")
    if website is not None:
        website = str(website).strip()
        if not website:
            website = None
        elif len(website) > 255:
            return error_response("Website URL must not exceed 255 characters.")

    if len(company_name) > 150:
        return error_response("Company name must not exceed 150 characters.")
    if len(industry) > 100:
        return error_response("Industry must not exceed 100 characters.")
    if len(company_address) > 255:
        return error_response("Company address must not exceed 255 characters.")

    # Parse HR contacts
    raw_contacts = data.get("contacts")
    parsed_contacts = []

    if raw_contacts and isinstance(raw_contacts, list):
        for c in raw_contacts:
            if isinstance(c, dict):
                c_name = str(c.get("contact_name", "")).strip()
                c_desig = str(c.get("designation", "HR Contact")).strip() or "HR Contact"
                c_email = str(c.get("email", "")).strip().lower()

                if c_name and c_email:
                    if not validate_email(c_email):
                        return error_response(f"Invalid email format: {c_email}")
                    # Collect phones
                    phones = []
                    raw_phones = c.get("phones", [])
                    if isinstance(raw_phones, list):
                        for p in raw_phones:
                            if isinstance(p, dict) and p.get("phone_number"):
                                num = str(p["phone_number"]).strip()
                                ptype = str(p.get("phone_type", "Work")).strip() or "Work"
                                if num and len(num) <= 20:
                                    phones.append((num, ptype))
                            elif isinstance(p, str) and p.strip():
                                phones.append((p.strip(), "Work"))
                    elif "phone" in c and str(c["phone"]).strip():
                        phones.append((str(c["phone"]).strip(), "Work"))

                    parsed_contacts.append({
                        "name": c_name,
                        "designation": c_desig,
                        "email": c_email,
                        "phones": phones
                    })
    elif "hr_contact_name" in data and "hr_email" in data:
        # Backward compatibility with single HR contact
        c_name = str(data["hr_contact_name"]).strip()
        c_email = str(data["hr_email"]).strip().lower()
        if not validate_email(c_email):
            return error_response("Invalid HR email format.")

        phones = []
        if "hr_phone" in data and str(data["hr_phone"]).strip():
            phones.append((str(data["hr_phone"]).strip(), "Work"))

        if c_name and c_email:
            parsed_contacts.append({
                "name": c_name,
                "designation": "HR Manager",
                "email": c_email,
                "phones": phones
            })

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            insert_query = """
                INSERT INTO company (company_name, industry, website, company_address)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (company_name, industry, website, company_address))
            new_company_id = cursor.lastrowid

            # Insert contacts and their phone numbers
            for c in parsed_contacts:
                cursor.execute("""
                    INSERT INTO company_contact (company_id, contact_name, designation, email)
                    VALUES (%s, %s, %s, %s)
                """, (new_company_id, c["name"], c["designation"], c["email"]))
                new_contact_id = cursor.lastrowid

                for num, ptype in c["phones"]:
                    cursor.execute("""
                        INSERT INTO company_contact_phone (contact_id, phone_number, phone_type)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                    """, (new_contact_id, num, ptype))

            # Retrieve created company
            cursor.execute("""
                SELECT company_id, company_name, industry, website, company_address
                FROM company
                WHERE company_id = %s
            """, (new_company_id,))
            created_company = cursor.fetchone()
            _attach_company_contacts(cursor, [created_company])

            return success_response(
                data=created_company,
                message="Company registered successfully with HR contacts.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@company_bp.route("/<int:company_id>", methods=["PUT"])
def update_company(company_id):
    """Update company details and HR contacts."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT * FROM company WHERE company_id = %s", (company_id,))
            existing = cursor.fetchone()
            if not existing:
                return error_response(f"Company with ID {company_id} not found.", status_code=404)

            company_name = existing["company_name"]
            industry = existing["industry"]
            website = existing["website"]
            company_address = existing["company_address"]

            if "company_name" in data:
                val = str(data["company_name"]).strip()
                if not val or len(val) > 150:
                    return error_response("Company name cannot be empty or exceed 150 characters.")
                company_name = val

            if "industry" in data:
                val = str(data["industry"]).strip()
                if not val or len(val) > 100:
                    return error_response("Industry cannot be empty or exceed 100 characters.")
                industry = val

            if "website" in data:
                val = data["website"]
                if val is not None:
                    val = str(val).strip()
                    if not val:
                        website = None
                    elif len(val) > 255:
                        return error_response("Website URL cannot exceed 255 characters.")
                    else:
                        website = val
                else:
                    website = None

            if "company_address" in data:
                val = str(data["company_address"]).strip()
                if not val or len(val) > 255:
                    return error_response("Company address cannot be empty or exceed 255 characters.")
                company_address = val

            update_query = """
                UPDATE company SET
                    company_name = %s,
                    industry = %s,
                    website = %s,
                    company_address = %s
                WHERE company_id = %s
            """
            cursor.execute(update_query, (company_name, industry, website, company_address, company_id))

            # Synchronize contacts if provided
            if "contacts" in data and isinstance(data["contacts"], list):
                # Delete existing contacts for this company (cascades to company_contact_phone)
                cursor.execute("DELETE FROM company_contact WHERE company_id = %s", (company_id,))

                for c in data["contacts"]:
                    if isinstance(c, dict):
                        c_name = str(c.get("contact_name", "")).strip()
                        c_desig = str(c.get("designation", "HR Contact")).strip() or "HR Contact"
                        c_email = str(c.get("email", "")).strip().lower()

                        if c_name and c_email:
                            if not validate_email(c_email):
                                return error_response(f"Invalid email: {c_email}")
                            cursor.execute("""
                                INSERT INTO company_contact (company_id, contact_name, designation, email)
                                VALUES (%s, %s, %s, %s)
                            """, (company_id, c_name, c_desig, c_email))
                            cid = cursor.lastrowid

                            raw_phones = c.get("phones", [])
                            if isinstance(raw_phones, list):
                                for p in raw_phones:
                                    if isinstance(p, dict) and p.get("phone_number"):
                                        num = str(p["phone_number"]).strip()
                                        ptype = str(p.get("phone_type", "Work")).strip() or "Work"
                                        if num:
                                            cursor.execute("""
                                                INSERT INTO company_contact_phone (contact_id, phone_number, phone_type)
                                                VALUES (%s, %s, %s)
                                                ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                                            """, (cid, num, ptype))
                                    elif isinstance(p, str) and p.strip():
                                        cursor.execute("""
                                            INSERT INTO company_contact_phone (contact_id, phone_number, phone_type)
                                            VALUES (%s, %s, 'Work')
                                            ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                                        """, (cid, p.strip()))

            cursor.execute("""
                SELECT company_id, company_name, industry, website, company_address
                FROM company
                WHERE company_id = %s
            """, (company_id,))
            updated_company = cursor.fetchone()
            _attach_company_contacts(cursor, [updated_company])

            return success_response(
                data=updated_company,
                message="Company updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@company_bp.route("/<int:company_id>", methods=["DELETE"])
def delete_company(company_id):
    """Delete a company by ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT company_id FROM company WHERE company_id = %s", (company_id,))
            if not cursor.fetchone():
                return error_response(f"Company with ID {company_id} not found.", status_code=404)

            # Deletion cascades to company_contact and company_contact_phone via FK
            cursor.execute("DELETE FROM company WHERE company_id = %s", (company_id,))
            return success_response(message="Company deleted successfully.")
    except Exception as e:
        return handle_db_error(e)


# ----------------------------------------------------------------------------
# Dedicated Contact Management Endpoints
# ----------------------------------------------------------------------------

@company_bp.route("/<int:company_id>/contacts", methods=["POST"])
def add_company_contact(company_id):
    """Add a new HR contact to an existing company."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    contact_name = str(data.get("contact_name", "")).strip()
    designation = str(data.get("designation", "HR Contact")).strip() or "HR Contact"
    email = str(data.get("email", "")).strip().lower()

    if not contact_name:
        return error_response("Contact name is required.")
    if not email or not validate_email(email):
        return error_response("Valid email is required.")

    phones = data.get("phones", [])

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT company_id FROM company WHERE company_id = %s", (company_id,))
            if not cursor.fetchone():
                return error_response(f"Company with ID {company_id} not found.", status_code=404)

            cursor.execute("""
                INSERT INTO company_contact (company_id, contact_name, designation, email)
                VALUES (%s, %s, %s, %s)
            """, (company_id, contact_name, designation, email))
            new_contact_id = cursor.lastrowid

            if isinstance(phones, list):
                for p in phones:
                    if isinstance(p, dict) and p.get("phone_number"):
                        num = str(p["phone_number"]).strip()
                        ptype = str(p.get("phone_type", "Work")).strip() or "Work"
                        if num:
                            cursor.execute("""
                                INSERT INTO company_contact_phone (contact_id, phone_number, phone_type)
                                VALUES (%s, %s, %s)
                                ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                            """, (new_contact_id, num, ptype))
                    elif isinstance(p, str) and p.strip():
                        cursor.execute("""
                            INSERT INTO company_contact_phone (contact_id, phone_number, phone_type)
                            VALUES (%s, %s, 'Work')
                            ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                        """, (new_contact_id, p.strip()))

            return success_response(
                data={"contact_id": new_contact_id, "company_id": company_id, "contact_name": contact_name, "email": email},
                message="HR contact added successfully.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@company_bp.route("/<int:company_id>/contacts/<int:contact_id>", methods=["DELETE"])
def delete_company_contact(company_id, contact_id):
    """Delete a specific HR contact from a company."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT contact_id FROM company_contact WHERE contact_id = %s AND company_id = %s", (contact_id, company_id))
            if not cursor.fetchone():
                return error_response("HR Contact not found for this company.", status_code=404)

            cursor.execute("DELETE FROM company_contact WHERE contact_id = %s", (contact_id,))
            return success_response(message="HR Contact deleted successfully.")
    except Exception as e:
        return handle_db_error(e)
