from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error,
    parse_datetime
)

interview_bp = Blueprint("interviews", __name__, url_prefix="/api/interviews")

VALID_INTERVIEW_MODES = {"Online", "Offline", "Hybrid"}
VALID_INTERVIEW_RESULTS = {"Pending", "Cleared", "Rejected", "No Show"}


@interview_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_interviews():
    """Retrieve all interview rounds with application, student, and job details."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    i.interview_id,
                    i.application_id,
                    i.round_number,
                    i.interview_date,
                    i.interview_mode,
                    i.interview_result,
                    i.feedback,
                    s.student_id,
                    s.student_name,
                    s.roll_number,
                    j.job_id,
                    j.job_title,
                    c.company_name
                FROM interview i
                LEFT JOIN application a ON i.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                ORDER BY i.interview_id ASC
            """
            cursor.execute(query)
            interviews = cursor.fetchall()
            return success_response(data=interviews)
    except Exception as e:
        return handle_db_error(e)


@interview_bp.route("/<int:interview_id>", methods=["GET"])
def get_interview_by_id(interview_id):
    """Retrieve a single interview round by ID."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    i.interview_id,
                    i.application_id,
                    i.round_number,
                    i.interview_date,
                    i.interview_mode,
                    i.interview_result,
                    i.feedback,
                    s.student_id,
                    s.student_name,
                    s.roll_number,
                    j.job_id,
                    j.job_title,
                    c.company_name
                FROM interview i
                LEFT JOIN application a ON i.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE i.interview_id = %s
            """
            cursor.execute(query, (interview_id,))
            interview = cursor.fetchone()
            if not interview:
                return error_response(f"Interview with ID {interview_id} not found.", status_code=404)
            return success_response(data=interview)
    except Exception as e:
        return handle_db_error(e)


@interview_bp.route("", methods=["POST"], strict_slashes=False)
def create_interview():
    """Schedule a new interview round for an application."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    required_fields = ["application_id", "round_number", "interview_date", "interview_mode"]
    missing = [f for f in required_fields if f not in data or data[f] is None or (isinstance(data[f], str) and not data[f].strip())]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}")

    # Application ID
    try:
        application_id = int(data["application_id"])
    except (ValueError, TypeError):
        return error_response("Application ID must be an integer.")

    # Round number
    try:
        round_number = int(data["round_number"])
        if round_number <= 0:
            return error_response("Round number must be a positive integer greater than zero.")
    except (ValueError, TypeError):
        return error_response("Round number must be an integer.")

    # Interview mode
    interview_mode = str(data["interview_mode"]).strip()
    if interview_mode not in VALID_INTERVIEW_MODES:
        return error_response(
            f"Invalid interview mode '{interview_mode}'. Allowed: {', '.join(sorted(VALID_INTERVIEW_MODES))}"
        )

    # Interview result
    interview_result = str(data.get("interview_result", "Pending")).strip()
    if interview_result not in VALID_INTERVIEW_RESULTS:
        return error_response(
            f"Invalid interview result '{interview_result}'. Allowed: {', '.join(sorted(VALID_INTERVIEW_RESULTS))}"
        )

    # Interview date
    try:
        interview_date = parse_datetime(data["interview_date"])
    except ValueError as ve:
        return error_response(str(ve))

    feedback = data.get("feedback")
    if feedback is not None:
        feedback = str(feedback).strip()
        if not feedback:
            feedback = None

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT application_id FROM application WHERE application_id = %s", (application_id,))
            if not cursor.fetchone():
                return error_response(f"Application with ID {application_id} does not exist.", status_code=400)

            # Check unique (application_id, round_number)
            cursor.execute(
                "SELECT interview_id FROM interview WHERE application_id = %s AND round_number = %s",
                (application_id, round_number)
            )
            if cursor.fetchone():
                return error_response(
                    f"Round {round_number} has already been scheduled for application {application_id}.",
                    status_code=409
                )

            insert_query = """
                INSERT INTO interview (
                    application_id, round_number, interview_date,
                    interview_mode, interview_result, feedback
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (application_id, round_number, interview_date, interview_mode, interview_result, feedback)
            )
            new_id = cursor.lastrowid

            cursor.execute("""
                SELECT 
                    i.interview_id, i.application_id, i.round_number,
                    i.interview_date, i.interview_mode, i.interview_result, i.feedback,
                    s.student_name, j.job_title
                FROM interview i
                LEFT JOIN application a ON i.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                WHERE i.interview_id = %s
            """, (new_id,))
            created_interview = cursor.fetchone()

            return success_response(
                data=created_interview,
                message="Interview scheduled successfully.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@interview_bp.route("/<int:interview_id>", methods=["PUT"])
def update_interview(interview_id):
    """Update interview details, result, or feedback."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT * FROM interview WHERE interview_id = %s", (interview_id,))
            existing = cursor.fetchone()
            if not existing:
                return error_response(f"Interview with ID {interview_id} not found.", status_code=404)

            application_id = existing["application_id"]
            round_number = existing["round_number"]
            interview_date = existing["interview_date"]
            interview_mode = existing["interview_mode"]
            interview_result = existing["interview_result"]
            feedback = existing["feedback"]

            if "round_number" in data:
                try:
                    val = int(data["round_number"])
                    if val <= 0:
                        return error_response("Round number must be a positive integer.")
                    if val != round_number:
                        # Check duplicate
                        cursor.execute(
                            "SELECT interview_id FROM interview WHERE application_id = %s AND round_number = %s",
                            (application_id, val)
                        )
                        if cursor.fetchone():
                            return error_response(f"Round {val} already exists for this application.", status_code=409)
                    round_number = val
                except (ValueError, TypeError):
                    return error_response("Round number must be an integer.")

            if "interview_date" in data:
                try:
                    interview_date = parse_datetime(data["interview_date"])
                except ValueError as ve:
                    return error_response(str(ve))

            if "interview_mode" in data:
                val = str(data["interview_mode"]).strip()
                if val not in VALID_INTERVIEW_MODES:
                    return error_response(
                        f"Invalid interview mode '{val}'. Allowed: {', '.join(sorted(VALID_INTERVIEW_MODES))}"
                    )
                interview_mode = val

            if "interview_result" in data:
                val = str(data["interview_result"]).strip()
                if val not in VALID_INTERVIEW_RESULTS:
                    return error_response(
                        f"Invalid interview result '{val}'. Allowed: {', '.join(sorted(VALID_INTERVIEW_RESULTS))}"
                    )
                interview_result = val

            if "feedback" in data:
                val = data["feedback"]
                feedback = str(val).strip() if val else None

            update_query = """
                UPDATE interview SET
                    round_number = %s,
                    interview_date = %s,
                    interview_mode = %s,
                    interview_result = %s,
                    feedback = %s
                WHERE interview_id = %s
            """
            cursor.execute(
                update_query,
                (round_number, interview_date, interview_mode, interview_result, feedback, interview_id)
            )

            cursor.execute("""
                SELECT 
                    i.interview_id, i.application_id, i.round_number,
                    i.interview_date, i.interview_mode, i.interview_result, i.feedback,
                    s.student_name, j.job_title
                FROM interview i
                LEFT JOIN application a ON i.application_id = a.application_id
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                WHERE i.interview_id = %s
            """, (interview_id,))
            updated_interview = cursor.fetchone()

            return success_response(
                data=updated_interview,
                message="Interview updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@interview_bp.route("/<int:interview_id>", methods=["DELETE"])
def delete_interview(interview_id):
    """Delete an interview round by ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT interview_id FROM interview WHERE interview_id = %s", (interview_id,))
            if not cursor.fetchone():
                return error_response(f"Interview with ID {interview_id} not found.", status_code=404)

            cursor.execute("DELETE FROM interview WHERE interview_id = %s", (interview_id,))
            return success_response(message="Interview round deleted successfully.")
    except Exception as e:
        return handle_db_error(e)

