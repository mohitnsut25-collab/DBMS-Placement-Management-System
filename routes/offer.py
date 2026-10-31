from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error,
    parse_date
)

offer_bp = Blueprint("offers", __name__, url_prefix="/api/offers")

VALID_OFFER_STATUSES = {"Pending", "Accepted", "Declined", "Expired"}


@offer_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_offers():
    """Retrieve all placement offers with student, job, and company details."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    o.offer_id,
                    o.application_id,
                    o.offered_ctc,
                    o.offer_date,
                    o.joining_date,
                    o.offer_status,
                    a.student_id,
                    s.student_name,
                    s.roll_number,
                    s.email AS student_email,
                    a.job_id,
                    j.job_title,
                    c.company_id,
                    c.company_name
                FROM offer o
                LEFT JOIN application a ON o.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                ORDER BY o.offer_id ASC
            """
            cursor.execute(query)
            offers = cursor.fetchall()
            return success_response(data=offers)
    except Exception as e:
        return handle_db_error(e)


@offer_bp.route("/<int:offer_id>", methods=["GET"])
def get_offer_by_id(offer_id):
    """Retrieve a single placement offer by ID."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    o.offer_id,
                    o.application_id,
                    o.offered_ctc,
                    o.offer_date,
                    o.joining_date,
                    o.offer_status,
                    a.student_id,
                    s.student_name,
                    s.roll_number,
                    s.email AS student_email,
                    a.job_id,
                    j.job_title,
                    c.company_id,
                    c.company_name
                FROM offer o
                LEFT JOIN application a ON o.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE o.offer_id = %s
            """
            cursor.execute(query, (offer_id,))
            offer = cursor.fetchone()
            if not offer:
                return error_response(f"Offer with ID {offer_id} not found.", status_code=404)
            return success_response(data=offer)
    except Exception as e:
        return handle_db_error(e)


@offer_bp.route("", methods=["POST"], strict_slashes=False)
def create_offer():
    """
    Issue a new job offer for a selected application.
    Enforces business validations:
    - Application status must be 'Selected'
    - Only one offer per application
    - Offered CTC must be greater than zero
    - Joining date must be on or after offer date
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    required_fields = ["application_id", "offered_ctc", "offer_date", "joining_date"]
    missing = [f for f in required_fields if f not in data or data[f] is None or (isinstance(data[f], str) and not data[f].strip())]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}")

    # Application ID
    try:
        application_id = int(data["application_id"])
    except (ValueError, TypeError):
        return error_response("Application ID must be an integer.")

    # CTC
    try:
        offered_ctc = float(data["offered_ctc"])
        if offered_ctc <= 0:
            return error_response("Offered CTC must be greater than zero.")
    except (ValueError, TypeError):
        return error_response("Offered CTC must be a valid positive number.")

    # Dates
    try:
        offer_date = parse_date(data["offer_date"])
        joining_date = parse_date(data["joining_date"])
        if joining_date < offer_date:
            return error_response("Joining date cannot be earlier than offer date.")
    except ValueError as ve:
        return error_response(str(ve))

    offer_status = str(data.get("offer_status", "Pending")).strip()
    if offer_status not in VALID_OFFER_STATUSES:
        return error_response(
            f"Invalid offer status '{offer_status}'. Allowed: {', '.join(sorted(VALID_OFFER_STATUSES))}"
        )

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            # 1. Verify application exists and its status
            cursor.execute(
                "SELECT application_id, application_status FROM application WHERE application_id = %s",
                (application_id,)
            )
            app_row = cursor.fetchone()
            if not app_row:
                return error_response(f"Application with ID {application_id} not found.", status_code=404)

            # 2. Business validation: Application must be 'Selected'
            if app_row["application_status"] != "Selected":
                return error_response(
                    f"Offers can only be issued for applications with status 'Selected'. Current status is '{app_row['application_status']}'.",
                    status_code=400
                )

            # 3. Check unique offer for application
            cursor.execute("SELECT offer_id FROM offer WHERE application_id = %s", (application_id,))
            if cursor.fetchone():
                return error_response(
                    f"An offer has already been issued for application ID {application_id}.",
                    status_code=409
                )

            # 4. Insert offer
            insert_query = """
                INSERT INTO offer (application_id, offered_ctc, offer_date, joining_date, offer_status)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (application_id, offered_ctc, offer_date, joining_date, offer_status))
            new_id = cursor.lastrowid

            cursor.execute("""
                SELECT 
                    o.offer_id, o.application_id, o.offered_ctc, o.offer_date,
                    o.joining_date, o.offer_status,
                    s.student_name, j.job_title, c.company_name
                FROM offer o
                LEFT JOIN application a ON o.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE o.offer_id = %s
            """, (new_id,))
            created_offer = cursor.fetchone()

            return success_response(
                data=created_offer,
                message="Offer issued successfully.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@offer_bp.route("/<int:offer_id>", methods=["PUT"])
def update_offer(offer_id):
    """Update offer details or status."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT * FROM offer WHERE offer_id = %s", (offer_id,))
            existing = cursor.fetchone()
            if not existing:
                return error_response(f"Offer with ID {offer_id} not found.", status_code=404)

            offered_ctc = float(existing["offered_ctc"])
            offer_date = existing["offer_date"]
            joining_date = existing["joining_date"]
            offer_status = existing["offer_status"]

            if "offered_ctc" in data:
                try:
                    val = float(data["offered_ctc"])
                    if val <= 0:
                        return error_response("Offered CTC must be greater than zero.")
                    offered_ctc = val
                except (ValueError, TypeError):
                    return error_response("Offered CTC must be a valid number.")

            if "offer_date" in data:
                try:
                    offer_date = parse_date(data["offer_date"])
                except ValueError as ve:
                    return error_response(str(ve))

            if "joining_date" in data:
                try:
                    joining_date = parse_date(data["joining_date"])
                except ValueError as ve:
                    return error_response(str(ve))

            if joining_date < offer_date:
                return error_response("Joining date cannot be earlier than offer date.")

            if "offer_status" in data:
                val = str(data["offer_status"]).strip()
                if val not in VALID_OFFER_STATUSES:
                    return error_response(
                        f"Invalid offer status '{val}'. Allowed: {', '.join(sorted(VALID_OFFER_STATUSES))}"
                    )
                offer_status = val

            update_query = """
                UPDATE offer SET
                    offered_ctc = %s,
                    offer_date = %s,
                    joining_date = %s,
                    offer_status = %s
                WHERE offer_id = %s
            """
            cursor.execute(update_query, (offered_ctc, offer_date, joining_date, offer_status, offer_id))

            cursor.execute("""
                SELECT 
                    o.offer_id, o.application_id, o.offered_ctc, o.offer_date,
                    o.joining_date, o.offer_status,
                    s.student_name, j.job_title, c.company_name
                FROM offer o
                LEFT JOIN application a ON o.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE o.offer_id = %s
            """, (offer_id,))
            updated_offer = cursor.fetchone()

            return success_response(
                data=updated_offer,
                message="Offer updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@offer_bp.route("/<int:offer_id>", methods=["DELETE"])
def delete_offer(offer_id):
    """Delete an offer by ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT offer_id FROM offer WHERE offer_id = %s", (offer_id,))
            if not cursor.fetchone():
                return error_response(f"Offer with ID {offer_id} not found.", status_code=404)

            cursor.execute("DELETE FROM offer WHERE offer_id = %s", (offer_id,))
            return success_response(message="Offer deleted successfully.")
    except Exception as e:
        return handle_db_error(e)

