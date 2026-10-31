from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error,
    parse_date
)

job_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")

VALID_JOB_TYPES = {"Full-time", "Internship", "Contract"}
VALID_JOB_STATUSES = {"Open", "Closed", "On Hold", "Cancelled"}


@job_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_jobs():
    """Retrieve all jobs with company details."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    j.job_id,
                    j.company_id,
                    c.company_name,
                    j.job_title,
                    j.job_description,
                    j.job_type,
                    j.job_location,
                    j.minimum_cgpa,
                    j.maximum_backlogs,
                    j.minimum_package,
                    j.maximum_package,
                    j.number_of_openings,
                    j.posting_date,
                    j.application_deadline,
                    j.job_status
                FROM job j
                LEFT JOIN company c ON j.company_id = c.company_id
                ORDER BY j.job_id ASC
            """
            cursor.execute(query)
            jobs = cursor.fetchall()
            return success_response(data=jobs)
    except Exception as e:
        return handle_db_error(e)


@job_bp.route("/<int:job_id>", methods=["GET"])
def get_job_by_id(job_id):
    """Retrieve a single job vacancy by ID."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    j.job_id,
                    j.company_id,
                    c.company_name,
                    j.job_title,
                    j.job_description,
                    j.job_type,
                    j.job_location,
                    j.minimum_cgpa,
                    j.maximum_backlogs,
                    j.minimum_package,
                    j.maximum_package,
                    j.number_of_openings,
                    j.posting_date,
                    j.application_deadline,
                    j.job_status
                FROM job j
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE j.job_id = %s
            """
            cursor.execute(query, (job_id,))
            job = cursor.fetchone()
            if not job:
                return error_response(f"Job with ID {job_id} not found.", status_code=404)
            return success_response(data=job)
    except Exception as e:
        return handle_db_error(e)


@job_bp.route("", methods=["POST"], strict_slashes=False)
def create_job():
    """Create a new job posting."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    required_fields = [
        "company_id", "job_title", "job_description", "job_type",
        "job_location", "minimum_cgpa", "minimum_package",
        "maximum_package", "number_of_openings", "posting_date",
        "application_deadline"
    ]
    missing = [f for f in required_fields if f not in data or data[f] is None or (isinstance(data[f], str) and not data[f].strip())]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}")

    # Company validation
    try:
        company_id = int(data["company_id"])
    except (ValueError, TypeError):
        return error_response("Company ID must be an integer.")

    job_title = str(data["job_title"]).strip()
    job_description = str(data["job_description"]).strip()
    job_type = str(data["job_type"]).strip()
    job_location = str(data["job_location"]).strip()
    job_status = str(data.get("job_status", "Open")).strip()

    if len(job_title) > 150:
        return error_response("Job title must not exceed 150 characters.")
    if len(job_location) > 150:
        return error_response("Job location must not exceed 150 characters.")

    if job_type not in VALID_JOB_TYPES:
        return error_response(f"Invalid job type '{job_type}'. Allowed: {', '.join(sorted(VALID_JOB_TYPES))}")

    if job_status not in VALID_JOB_STATUSES:
        return error_response(f"Invalid job status '{job_status}'. Allowed: {', '.join(sorted(VALID_JOB_STATUSES))}")

    # CGPA validation
    try:
        minimum_cgpa = float(data["minimum_cgpa"])
        if minimum_cgpa < 0.0 or minimum_cgpa > 10.0:
            return error_response("Minimum CGPA must be between 0.0 and 10.0.")
    except (ValueError, TypeError):
        return error_response("Minimum CGPA must be a valid decimal number.")

    # Backlogs validation
    maximum_backlogs = data.get("maximum_backlogs", 0)
    try:
        maximum_backlogs = int(maximum_backlogs)
        if maximum_backlogs < 0:
            return error_response("Maximum backlogs cannot be negative.")
    except (ValueError, TypeError):
        return error_response("Maximum backlogs must be a valid non-negative integer.")

    # Package validation
    try:
        min_pkg = float(data["minimum_package"])
        max_pkg = float(data["maximum_package"])
        if min_pkg < 0:
            return error_response("Minimum package cannot be negative.")
        if max_pkg < min_pkg:
            return error_response("Maximum package cannot be less than minimum package.")
    except (ValueError, TypeError):
        return error_response("Package amounts must be valid numbers.")

    # Openings validation
    try:
        openings = int(data["number_of_openings"])
        if openings <= 0:
            return error_response("Number of openings must be greater than zero.")
    except (ValueError, TypeError):
        return error_response("Number of openings must be a positive integer.")

    # Dates validation
    try:
        post_date = parse_date(data["posting_date"])
        deadline = parse_date(data["application_deadline"])
        if deadline < post_date:
            return error_response("Application deadline cannot be earlier than posting date.")
    except ValueError as e:
        return error_response(str(e))

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT company_id FROM company WHERE company_id = %s", (company_id,))
            if not cursor.fetchone():
                return error_response(f"Company with ID {company_id} does not exist.", status_code=400)

            insert_query = """
                INSERT INTO job (
                    company_id, job_title, job_description, job_type,
                    job_location, minimum_cgpa, maximum_backlogs,
                    minimum_package, maximum_package, number_of_openings,
                    posting_date, application_deadline, job_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (company_id, job_title, job_description, job_type,
                 job_location, minimum_cgpa, maximum_backlogs,
                 min_pkg, max_pkg, openings,
                 post_date, deadline, job_status)
            )
            new_id = cursor.lastrowid

            cursor.execute("""
                SELECT 
                    j.job_id, j.company_id, c.company_name, j.job_title,
                    j.job_description, j.job_type, j.job_location,
                    j.minimum_cgpa, j.maximum_backlogs, j.minimum_package,
                    j.maximum_package, j.number_of_openings, j.posting_date,
                    j.application_deadline, j.job_status
                FROM job j
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE j.job_id = %s
            """, (new_id,))
            created_job = cursor.fetchone()

            return success_response(
                data=created_job,
                message="Job vacancy created successfully.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@job_bp.route("/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    """Update job posting details."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT * FROM job WHERE job_id = %s", (job_id,))
            existing = cursor.fetchone()
            if not existing:
                return error_response(f"Job with ID {job_id} not found.", status_code=404)

            company_id = existing["company_id"]
            job_title = existing["job_title"]
            job_description = existing["job_description"]
            job_type = existing["job_type"]
            job_location = existing["job_location"]
            minimum_cgpa = float(existing["minimum_cgpa"])
            maximum_backlogs = existing["maximum_backlogs"]
            min_pkg = float(existing["minimum_package"])
            max_pkg = float(existing["maximum_package"])
            openings = existing["number_of_openings"]
            post_date = existing["posting_date"]
            deadline = existing["application_deadline"]
            job_status = existing["job_status"]

            if "company_id" in data:
                try:
                    c_id = int(data["company_id"])
                    cursor.execute("SELECT company_id FROM company WHERE company_id = %s", (c_id,))
                    if not cursor.fetchone():
                        return error_response(f"Company with ID {c_id} does not exist.", status_code=400)
                    company_id = c_id
                except (ValueError, TypeError):
                    return error_response("Company ID must be an integer.")

            if "job_title" in data:
                val = str(data["job_title"]).strip()
                if not val or len(val) > 150:
                    return error_response("Job title cannot be empty or exceed 150 characters.")
                job_title = val

            if "job_description" in data:
                val = str(data["job_description"]).strip()
                if not val:
                    return error_response("Job description cannot be empty.")
                job_description = val

            if "job_type" in data:
                val = str(data["job_type"]).strip()
                if val not in VALID_JOB_TYPES:
                    return error_response(f"Invalid job type '{val}'. Allowed: {', '.join(sorted(VALID_JOB_TYPES))}")
                job_type = val

            if "job_location" in data:
                val = str(data["job_location"]).strip()
                if not val or len(val) > 150:
                    return error_response("Job location cannot be empty or exceed 150 characters.")
                job_location = val

            if "minimum_cgpa" in data:
                try:
                    val = float(data["minimum_cgpa"])
                    if val < 0.0 or val > 10.0:
                        return error_response("Minimum CGPA must be between 0.0 and 10.0.")
                    minimum_cgpa = val
                except (ValueError, TypeError):
                    return error_response("Minimum CGPA must be a valid decimal number.")

            if "maximum_backlogs" in data:
                try:
                    val = int(data["maximum_backlogs"])
                    if val < 0:
                        return error_response("Maximum backlogs cannot be negative.")
                    maximum_backlogs = val
                except (ValueError, TypeError):
                    return error_response("Maximum backlogs must be a valid non-negative integer.")

            if "minimum_package" in data:
                try:
                    val = float(data["minimum_package"])
                    if val < 0:
                        return error_response("Minimum package cannot be negative.")
                    min_pkg = val
                except (ValueError, TypeError):
                    return error_response("Minimum package must be a valid number.")

            if "maximum_package" in data:
                try:
                    val = float(data["maximum_package"])
                    max_pkg = val
                except (ValueError, TypeError):
                    return error_response("Maximum package must be a valid number.")

            if max_pkg < min_pkg:
                return error_response("Maximum package cannot be less than minimum package.")

            if "number_of_openings" in data:
                try:
                    val = int(data["number_of_openings"])
                    if val <= 0:
                        return error_response("Number of openings must be greater than zero.")
                    openings = val
                except (ValueError, TypeError):
                    return error_response("Number of openings must be a positive integer.")

            if "posting_date" in data:
                try:
                    post_date = parse_date(data["posting_date"])
                except ValueError as ve:
                    return error_response(str(ve))

            if "application_deadline" in data:
                try:
                    deadline = parse_date(data["application_deadline"])
                except ValueError as ve:
                    return error_response(str(ve))

            if deadline < post_date:
                return error_response("Application deadline cannot be earlier than posting date.")

            if "job_status" in data:
                val = str(data["job_status"]).strip()
                if val not in VALID_JOB_STATUSES:
                    return error_response(f"Invalid job status '{val}'. Allowed: {', '.join(sorted(VALID_JOB_STATUSES))}")
                job_status = val

            update_query = """
                UPDATE job SET
                    company_id = %s,
                    job_title = %s,
                    job_description = %s,
                    job_type = %s,
                    job_location = %s,
                    minimum_cgpa = %s,
                    maximum_backlogs = %s,
                    minimum_package = %s,
                    maximum_package = %s,
                    number_of_openings = %s,
                    posting_date = %s,
                    application_deadline = %s,
                    job_status = %s
                WHERE job_id = %s
            """
            cursor.execute(
                update_query,
                (company_id, job_title, job_description, job_type,
                 job_location, minimum_cgpa, maximum_backlogs,
                 min_pkg, max_pkg, openings,
                 post_date, deadline, job_status, job_id)
            )

            cursor.execute("""
                SELECT 
                    j.job_id, j.company_id, c.company_name, j.job_title,
                    j.job_description, j.job_type, j.job_location,
                    j.minimum_cgpa, j.maximum_backlogs, j.minimum_package,
                    j.maximum_package, j.number_of_openings, j.posting_date,
                    j.application_deadline, j.job_status
                FROM job j
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE j.job_id = %s
            """, (job_id,))
            updated_job = cursor.fetchone()

            return success_response(
                data=updated_job,
                message="Job updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@job_bp.route("/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    """Delete a job posting by ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT job_id FROM job WHERE job_id = %s", (job_id,))
            if not cursor.fetchone():
                return error_response(f"Job with ID {job_id} not found.", status_code=404)

            cursor.execute("DELETE FROM job WHERE job_id = %s", (job_id,))
            return success_response(message="Job deleted successfully.")
    except Exception as e:
        return handle_db_error(e)

