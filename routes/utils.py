import re
from contextlib import contextmanager
from datetime import datetime, date
from decimal import Decimal
import mysql.connector
from flask import jsonify, current_app
from db import get_db_connection

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for safely managing database connections and cursors.
    Handles automatic commits on success (if commit=True),
    rollbacks on exception, and guaranteed cleanup of cursor and connection.
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        yield connection, cursor
        if commit:
            connection.commit()
    except Exception:
        if connection is not None and connection.is_connected():
            try:
                connection.rollback()
            except Exception:
                pass
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if connection is not None and connection.is_connected():
            try:
                connection.close()
            except Exception:
                pass


def success_response(data=None, message=None, status_code=200):
    """Constructs a consistent successful JSON response."""
    response = {"success": True}
    if message is not None:
        response["message"] = message
    if data is not None:
        if isinstance(data, list):
            response["count"] = len(data)
        response["data"] = data
    return jsonify(response), status_code


def error_response(message, status_code=400, details=None):
    """Constructs a consistent error JSON response without leaking sensitive info."""
    response = {
        "success": False,
        "error": message
    }
    if details is not None:
        response["details"] = details
    return jsonify(response), status_code


def handle_db_error(e):
    """
    Translates MySQL exceptions into clean, secure HTTP responses with proper status codes.
    Prevents database credentials or internal stack traces from leaking to clients.
    """
    if isinstance(e, mysql.connector.Error):
        current_app.logger.warning(f"MySQL Error [{e.errno}]: {e.msg}")

        # 1062: Duplicate entry
        if e.errno == 1062:
            return error_response(
                "A duplicate record already exists with the provided unique information.",
                status_code=409,
                details=e.msg
            )

        # 1451: Foreign key deletion restriction
        if e.errno == 1451:
            return error_response(
                "Cannot delete or modify record because other records depend on it.",
                status_code=409,
                details="Foreign key restriction: related child records exist."
            )

        # 1452: Foreign key reference failure on insert/update
        if e.errno == 1452:
            return error_response(
                "Invalid foreign key reference: the related record does not exist.",
                status_code=400,
                details="Referenced foreign key ID not found."
            )

        # 3819: Check constraint violation
        if e.errno == 3819:
            return error_response(
                "Data constraint violation: input values violate database validation constraints.",
                status_code=400,
                details=e.msg
            )

        # General MySQL error
        return error_response(
            "A database error occurred while processing your request.",
            status_code=500
        )

    current_app.logger.exception("Unexpected server error")
    return error_response(
        "An unexpected internal server error occurred.",
        status_code=500
    )


def validate_email(email_str):
    """Validates email format and length."""
    if not isinstance(email_str, str):
        return False
    email_str = email_str.strip()
    if len(email_str) > 254:
        return False
    return bool(EMAIL_REGEX.match(email_str))


def parse_date(date_val):
    """Parses a date string in YYYY-MM-DD format, or returns date object if already one."""
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if not isinstance(date_val, str):
        raise ValueError("Date must be a string in YYYY-MM-DD format.")
    return datetime.strptime(date_val.strip(), "%Y-%m-%d").date()


def parse_datetime(dt_val):
    """Parses ISO or standard datetime strings."""
    if isinstance(dt_val, datetime):
        return dt_val
    if not isinstance(dt_val, str):
        raise ValueError("Datetime must be a string in YYYY-MM-DD HH:MM:SS or ISO format.")
    val_str = dt_val.strip()
    try:
        return datetime.fromisoformat(val_str)
    except ValueError:
        return datetime.strptime(val_str, "%Y-%m-%d %H:%M:%S")

