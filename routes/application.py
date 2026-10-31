from datetime import date
from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error,
    parse_datetime
)

application_bp = Blueprint("applications", __name__, url_prefix="/api/applications")

VALID_APPLICATION_STATUSES = {
    "Applied", "Under Review", "Shortlisted", "Rejected", "Selected", "Withdrawn"
}


@application_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_applications():
    """Retrieve all student job applications with joined student, job, and company details."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    a.application_id,
                    a.student_id,
                    s.roll_number,
                    s.student_name,
                    s.email AS student_email,
                    s.cgpa AS student_cgpa,
                    s.active_backlogs AS student_backlogs,
                    a.job_id,
                    j.job_title,
                    j.job_type,
                    j.job_status,
                    c.company_id,
                    c.company_name,
                    a.application_date,
                    a.application_status
                FROM application a
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                ORDER BY a.application_id ASC
            """
            cursor.execute(query)
            applications = cursor.fetchall()
            return success_response(data=applications)
    except Exception as e:
        return handle_db_error(e)


@application_bp.route("/<int:application_id>", methods=["GET"])
def get_application_by_id(application_id):
    """Retrieve a single application by ID with full details."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    a.application_id,
                    a.student_id,
                    s.roll_number,
                    s.student_name,
                    s.email AS student_email,
                    s.cgpa AS student_cgpa,
                    s.active_backlogs AS student_backlogs,
                    a.job_id,
                    j.job_title,
                    j.job_type,
                    j.job_status,
                    c.company_id,
                    c.company_name,
                    a.application_date,
                    a.application_status
                FROM application a
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                LEFT JOIN company c ON j.company_id = c.company_id
                WHERE a.application_id = %s
            """
            cursor.execute(query, (application_id,))
            application = cursor.fetchone()
            if not application:
                return error_response(f"Application with ID {application_id} not found.", status_code=404)
            return success_response(data=application)
    except Exception as e:
        return handle_db_error(e)


@application_bp.route("", methods=["POST"], strict_slashes=False)
def create_application():
    """
    Submit a job application for a student.
    Enforces business validations:
    - Student eligibility (minimum CGPA and maximum backlogs)
    - Vacancy status (must be 'Open')
    - Application deadline (cannot be expired)
    - Duplicate application prevention
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    if "student_id" not in data or "job_id" not in data:
        return error_response("Fields 'student_id' and 'job_id' are required.")

    try:
        student_id = int(data["student_id"])
        job_id = int(data["job_id"])
    except (ValueError, TypeError):
        return error_response("Fields 'student_id' and 'job_id' must be integers.")

    status = data.get("application_status", "Applied")
    if status not in VALID_APPLICATION_STATUSES:
        return error_response(
            f"Invalid application status '{status}'. Allowed: {', '.join(sorted(VALID_APPLICATION_STATUSES))}"
        )

    # Optional explicit application_date
    app_date = None
    if "application_date" in data and data["application_date"]:
        try:
            app_date = parse_datetime(data["application_date"])
        except ValueError as ve:
            return error_response(str(ve))

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            # 1. Verify student existence
            cursor.execute(
                "SELECT student_id, student_name, cgpa, active_backlogs FROM student WHERE student_id = %s",
                (student_id,)
            )
            student = cursor.fetchone()
            if not student:
                return error_response(f"Student with ID {student_id} not found.", status_code=404)

            # 2. Verify job existence
            cursor.execute(
                """
                SELECT job_id, job_title, job_status, application_deadline,
                       minimum_cgpa, maximum_backlogs
                FROM job WHERE job_id = %s
                """,
                (job_id,)
            )
            job = cursor.fetchone()
            if not job:
                return error_response(f"Job with ID {job_id} not found.", status_code=404)

            # 3. Check for duplicate application
            cursor.execute(
                "SELECT application_id FROM application WHERE student_id = %s AND job_id = %s",
                (student_id, job_id)
            )
            if cursor.fetchone():
                return error_response(
                    f"Student '{student['student_name']}' has already applied for job '{job['job_title']}'.",
                    status_code=409
                )

            # 4. Vacancy status check: vacancy must be Open
            if job["job_status"] != "Open":
                return error_response(
                    f"Applications are not accepted for this vacancy because its status is '{job['job_status']}'. Only 'Open' vacancies accept applications.",
                    status_code=400
                )

            # 5. Vacancy expiration check: deadline must not have passed
            effective_date = app_date.date() if app_date else date.today()
            if effective_date > job["application_deadline"]:
                return error_response(
                    f"Application deadline for '{job['job_title']}' expired on {job['application_deadline']}.",
                    status_code=400
                )

            # 6. Student eligibility checks
            student_cgpa = float(student["cgpa"])
            min_cgpa = float(job["minimum_cgpa"])
            if student_cgpa < min_cgpa:
                return error_response(
                    f"Eligibility check failed: Student CGPA ({student_cgpa:.2f}) is below the required minimum CGPA ({min_cgpa:.2f}) for this job.",
                    status_code=400
                )

            student_backlogs = int(student["active_backlogs"])
            max_backlogs = int(job["maximum_backlogs"])
            if student_backlogs > max_backlogs:
                return error_response(
                    f"Eligibility check failed: Student has {student_backlogs} active backlogs, which exceeds the maximum allowed ({max_backlogs}) for this job.",
                    status_code=400
                )

            # 7. Insert application
            if app_date:
                insert_query = """
                    INSERT INTO application (student_id, job_id, application_date, application_status)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (student_id, job_id, app_date, status))
            else:
                insert_query = """
                    INSERT INTO application (student_id, job_id, application_status)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (student_id, job_id, status))

            new_id = cursor.lastrowid

            cursor.execute("""
                SELECT 
                    a.application_id, a.student_id, s.roll_number, s.student_name,
                    a.job_id, j.job_title, a.application_date, a.application_status
                FROM application a
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                WHERE a.application_id = %s
            """, (new_id,))
            created_app = cursor.fetchone()

            return success_response(
                data=created_app,
                message="Application submitted successfully.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@application_bp.route("/<int:application_id>", methods=["PUT"])
def update_application(application_id):
    """Update application status."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT * FROM application WHERE application_id = %s", (application_id,))
            existing = cursor.fetchone()
            if not existing:
                return error_response(f"Application with ID {application_id} not found.", status_code=404)

            new_status = existing["application_status"]
            if "application_status" in data:
                val = str(data["application_status"]).strip()
                if val not in VALID_APPLICATION_STATUSES:
                    return error_response(
                        f"Invalid application status '{val}'. Allowed: {', '.join(sorted(VALID_APPLICATION_STATUSES))}"
                    )
                new_status = val

            cursor.execute(
                "UPDATE application SET application_status = %s WHERE application_id = %s",
                (new_status, application_id)
            )

            cursor.execute("""
                SELECT 
                    a.application_id, a.student_id, s.roll_number, s.student_name,
                    a.job_id, j.job_title, a.application_date, a.application_status
                FROM application a
                LEFT JOIN student s ON a.student_id = s.student_id
                LEFT JOIN job j ON a.job_id = j.job_id
                WHERE a.application_id = %s
            """, (application_id,))
            updated_app = cursor.fetchone()

            return success_response(
                data=updated_app,
                message="Application updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@application_bp.route("/<int:application_id>", methods=["DELETE"])
def delete_application(application_id):
    """Delete an application by ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT application_id FROM application WHERE application_id = %s", (application_id,))
            if not cursor.fetchone():
                return error_response(f"Application with ID {application_id} not found.", status_code=404)

            cursor.execute("DELETE FROM application WHERE application_id = %s", (application_id,))
            return success_response(message="Application deleted successfully.")
    except Exception as e:
        return handle_db_error(e)

