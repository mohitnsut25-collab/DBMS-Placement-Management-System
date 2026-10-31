from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error
)

department_bp = Blueprint("departments", __name__, url_prefix="/api/departments")


@department_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_departments():
    """Retrieve all academic departments."""
    try:
        with get_db_cursor() as (conn, cursor):
            cursor.execute(
                "SELECT department_id, department_code, department_name FROM department ORDER BY department_id ASC"
            )
            departments = cursor.fetchall()
            return success_response(data=departments)
    except Exception as e:
        return handle_db_error(e)


@department_bp.route("/<int:department_id>", methods=["GET"])
def get_department_by_id(department_id):
    """Retrieve a single department by its ID."""
    try:
        with get_db_cursor() as (conn, cursor):
            cursor.execute(
                "SELECT department_id, department_code, department_name FROM department WHERE department_id = %s",
                (department_id,)
            )
            dept = cursor.fetchone()
            if not dept:
                return error_response(f"Department with ID {department_id} not found.", status_code=404)
            return success_response(data=dept)
    except Exception as e:
        return handle_db_error(e)


@department_bp.route("", methods=["POST"], strict_slashes=False)
def create_department():
    """Create a new academic department."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    department_code = data.get("department_code")
    department_name = data.get("department_name")

    # Required field validations
    if not department_code or not str(department_code).strip():
        return error_response("Field 'department_code' is required and cannot be empty.")
    if not department_name or not str(department_name).strip():
        return error_response("Field 'department_name' is required and cannot be empty.")

    department_code = str(department_code).strip().upper()
    department_name = str(department_name).strip()

    if len(department_code) > 15:
        return error_response("Department code must not exceed 15 characters.")
    if len(department_name) > 100:
        return error_response("Department name must not exceed 100 characters.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "INSERT INTO department (department_code, department_name) VALUES (%s, %s)",
                (department_code, department_name)
            )
            new_id = cursor.lastrowid
            cursor.execute(
                "SELECT department_id, department_code, department_name FROM department WHERE department_id = %s",
                (new_id,)
            )
            created_dept = cursor.fetchone()
            return success_response(
                data=created_dept,
                message="Department created successfully.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@department_bp.route("/<int:department_id>", methods=["PUT"])
def update_department(department_id):
    """Update an existing department by its ID."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "SELECT department_id, department_code, department_name FROM department WHERE department_id = %s",
                (department_id,)
            )
            dept = cursor.fetchone()
            if not dept:
                return error_response(f"Department with ID {department_id} not found.", status_code=404)

            department_code = data.get("department_code")
            department_name = data.get("department_name")

            if department_code is None and department_name is None:
                return error_response("At least one field ('department_code' or 'department_name') must be provided to update.")

            new_code = dept["department_code"]
            new_name = dept["department_name"]

            if department_code is not None:
                new_code = str(department_code).strip().upper()
                if not new_code:
                    return error_response("Field 'department_code' cannot be empty.")
                if len(new_code) > 15:
                    return error_response("Department code must not exceed 15 characters.")

            if department_name is not None:
                new_name = str(department_name).strip()
                if not new_name:
                    return error_response("Field 'department_name' cannot be empty.")
                if len(new_name) > 100:
                    return error_response("Department name must not exceed 100 characters.")

            cursor.execute(
                "UPDATE department SET department_code = %s, department_name = %s WHERE department_id = %s",
                (new_code, new_name, department_id)
            )

            cursor.execute(
                "SELECT department_id, department_code, department_name FROM department WHERE department_id = %s",
                (department_id,)
            )
            updated_dept = cursor.fetchone()
            return success_response(
                data=updated_dept,
                message="Department updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@department_bp.route("/<int:department_id>", methods=["DELETE"])
def delete_department(department_id):
    """Delete a department by its ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "SELECT department_id FROM department WHERE department_id = %s",
                (department_id,)
            )
            dept = cursor.fetchone()
            if not dept:
                return error_response(f"Department with ID {department_id} not found.", status_code=404)

            cursor.execute(
                "DELETE FROM department WHERE department_id = %s",
                (department_id,)
            )
            return success_response(message="Department deleted successfully.")
    except Exception as e:
        return handle_db_error(e)

