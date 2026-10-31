from datetime import date
from flask import Blueprint, request
from routes.utils import (
    get_db_cursor,
    success_response,
    error_response,
    handle_db_error,
    validate_email,
    parse_date
)

student_bp = Blueprint("students", __name__, url_prefix="/api/students")


def _attach_student_phones(cursor, students):
    """Helper to attach phone_numbers list to a list of student records."""
    if not students:
        return students

    student_ids = [s["student_id"] for s in students if isinstance(s, dict) and "student_id" in s]
    if not student_ids:
        return students

    format_strings = ",".join(["%s"] * len(student_ids))
    cursor.execute(f"""
        SELECT student_id, phone_number, phone_type
        FROM student_phone
        WHERE student_id IN ({format_strings})
        ORDER BY student_id, (phone_type = 'Primary') DESC, phone_number ASC
    """, tuple(student_ids))

    phones = cursor.fetchall()
    phones_by_student = {}
    if phones and isinstance(phones, list):
        for p in phones:
            if not isinstance(p, dict) or "student_id" not in p or "phone_number" not in p:
                continue
            sid = p["student_id"]
            if sid not in phones_by_student:
                phones_by_student[sid] = []
            phones_by_student[sid].append({
                "phone_number": p["phone_number"],
                "phone_type": p.get("phone_type", "Primary")
            })

    for s in students:
        if isinstance(s, dict):
            sid = s.get("student_id")
            s_phones = phones_by_student.get(sid, [])
            s["phone_numbers"] = s_phones
            # Convenience legacy field
            s["phone"] = s_phones[0]["phone_number"] if s_phones else ""

    return students


@student_bp.route("", methods=["GET"], strict_slashes=False)
def get_all_students():
    """Retrieve all students with department details and normalized contact numbers."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    s.student_id,
                    s.roll_number,
                    s.student_name,
                    s.email,
                    s.date_of_birth,
                    s.batch_year,
                    s.cgpa,
                    s.active_backlogs,
                    s.department_id,
                    d.department_code,
                    d.department_name
                FROM student s
                LEFT JOIN department d ON s.department_id = d.department_id
                ORDER BY s.student_id ASC
            """
            cursor.execute(query)
            students = cursor.fetchall()
            _attach_student_phones(cursor, students)
            return success_response(data=students)
    except Exception as e:
        return handle_db_error(e)


@student_bp.route("/<int:student_id>", methods=["GET"])
def get_student_by_id(student_id):
    """Retrieve a single student by ID with all contact numbers."""
    try:
        with get_db_cursor() as (conn, cursor):
            query = """
                SELECT 
                    s.student_id,
                    s.roll_number,
                    s.student_name,
                    s.email,
                    s.date_of_birth,
                    s.batch_year,
                    s.cgpa,
                    s.active_backlogs,
                    s.department_id,
                    d.department_code,
                    d.department_name
                FROM student s
                LEFT JOIN department d ON s.department_id = d.department_id
                WHERE s.student_id = %s
            """
            cursor.execute(query, (student_id,))
            student = cursor.fetchone()
            if not student:
                return error_response(f"Student with ID {student_id} not found.", status_code=404)

            _attach_student_phones(cursor, [student])
            return success_response(data=student)
    except Exception as e:
        return handle_db_error(e)


@student_bp.route("", methods=["POST"], strict_slashes=False)
def create_student():
    """Register a new student with multiple contact phone numbers."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    required_fields = [
        "roll_number", "student_name", "email",
        "date_of_birth", "batch_year", "cgpa", "department_id"
    ]
    missing = [f for f in required_fields if f not in data or data[f] is None or (isinstance(data[f], str) and not data[f].strip())]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}")

    roll_number = str(data["roll_number"]).strip().upper()
    student_name = str(data["student_name"]).strip()
    email = str(data["email"]).strip().lower()

    # Parse and validate phone numbers
    raw_phones = data.get("phone_numbers")
    phone_list = []

    if raw_phones and isinstance(raw_phones, list):
        for p in raw_phones:
            if isinstance(p, dict) and p.get("phone_number"):
                num = str(p["phone_number"]).strip()
                ptype = str(p.get("phone_type", "Primary")).strip() or "Primary"
                if num and len(num) <= 20:
                    phone_list.append((num, ptype))
            elif isinstance(p, str) and p.strip():
                num = p.strip()
                if len(num) <= 20:
                    phone_list.append((num, "Primary"))
    elif "phone" in data and str(data["phone"]).strip():
        # Backward compatibility with single phone input
        num = str(data["phone"]).strip()
        if len(num) <= 20:
            phone_list.append((num, "Primary"))

    # Length validations
    if len(roll_number) > 30:
        return error_response("Roll number must not exceed 30 characters.")
    if len(student_name) > 100:
        return error_response("Student name must not exceed 100 characters.")

    # Email validation
    if not validate_email(email):
        return error_response("Invalid email format.")

    # Date of birth validation
    try:
        dob = parse_date(data["date_of_birth"])
        if dob >= date.today():
            return error_response("Date of birth must be a past date.")
    except ValueError as e:
        return error_response(str(e))

    # Batch year validation
    try:
        batch_year = int(data["batch_year"])
        if batch_year < 1990 or batch_year > 2100:
            return error_response("Batch year must be between 1990 and 2100.")
    except (ValueError, TypeError):
        return error_response("Batch year must be a valid integer.")

    # CGPA validation
    try:
        cgpa = float(data["cgpa"])
        if cgpa < 0.0 or cgpa > 10.0:
            return error_response("CGPA must be between 0.0 and 10.0.")
    except (ValueError, TypeError):
        return error_response("CGPA must be a valid decimal number.")

    # Active backlogs validation
    active_backlogs = data.get("active_backlogs", 0)
    try:
        active_backlogs = int(active_backlogs)
        if active_backlogs < 0:
            return error_response("Active backlogs cannot be negative.")
    except (ValueError, TypeError):
        return error_response("Active backlogs must be a valid non-negative integer.")

    # Department validation
    try:
        department_id = int(data["department_id"])
    except (ValueError, TypeError):
        return error_response("Department ID must be a valid integer.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            # Verify department exists
            cursor.execute("SELECT department_id FROM department WHERE department_id = %s", (department_id,))
            if not cursor.fetchone():
                return error_response(f"Department with ID {department_id} does not exist.", status_code=400)

            # Insert student
            insert_query = """
                INSERT INTO student (
                    roll_number, student_name, email,
                    date_of_birth, batch_year, cgpa, active_backlogs, department_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (roll_number, student_name, email, dob, batch_year, cgpa, active_backlogs, department_id)
            )
            new_id = cursor.lastrowid

            # Insert phone numbers into student_phone table
            for num, ptype in phone_list:
                cursor.execute("""
                    INSERT INTO student_phone (student_id, phone_number, phone_type)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                """, (new_id, num, ptype))

            # Fetch created student with details
            cursor.execute("""
                SELECT 
                    s.student_id, s.roll_number, s.student_name, s.email,
                    s.date_of_birth, s.batch_year, s.cgpa, s.active_backlogs, s.department_id,
                    d.department_code, d.department_name
                FROM student s
                LEFT JOIN department d ON s.department_id = d.department_id
                WHERE s.student_id = %s
            """, (new_id,))
            created_student = cursor.fetchone()
            _attach_student_phones(cursor, [created_student])

            return success_response(
                data=created_student,
                message="Student registered successfully with contact numbers.",
                status_code=201
            )
    except Exception as e:
        return handle_db_error(e)


@student_bp.route("/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """Update existing student details and contact numbers."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return error_response("Invalid JSON request body.")

    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT * FROM student WHERE student_id = %s", (student_id,))
            existing = cursor.fetchone()
            if not existing:
                return error_response(f"Student with ID {student_id} not found.", status_code=404)

            roll_number = existing["roll_number"]
            student_name = existing["student_name"]
            email = existing["email"]
            dob = existing["date_of_birth"]
            batch_year = existing["batch_year"]
            cgpa = existing["cgpa"]
            active_backlogs = existing["active_backlogs"]
            department_id = existing["department_id"]

            if "roll_number" in data:
                val = str(data["roll_number"]).strip().upper()
                if not val or len(val) > 30:
                    return error_response("Roll number cannot be empty or exceed 30 characters.")
                roll_number = val

            if "student_name" in data:
                val = str(data["student_name"]).strip()
                if not val or len(val) > 100:
                    return error_response("Student name cannot be empty or exceed 100 characters.")
                student_name = val

            if "email" in data:
                val = str(data["email"]).strip().lower()
                if not validate_email(val):
                    return error_response("Invalid email format.")
                email = val

            if "date_of_birth" in data:
                try:
                    val = parse_date(data["date_of_birth"])
                    if val >= date.today():
                        return error_response("Date of birth must be a past date.")
                    dob = val
                except ValueError as ve:
                    return error_response(str(ve))

            if "batch_year" in data:
                try:
                    val = int(data["batch_year"])
                    if val < 1990 or val > 2100:
                        return error_response("Batch year must be between 1990 and 2100.")
                    batch_year = val
                except (ValueError, TypeError):
                    return error_response("Batch year must be a valid integer.")

            if "cgpa" in data:
                try:
                    val = float(data["cgpa"])
                    if val < 0.0 or val > 10.0:
                        return error_response("CGPA must be between 0.0 and 10.0.")
                    cgpa = val
                except (ValueError, TypeError):
                    return error_response("CGPA must be a valid decimal number.")

            if "active_backlogs" in data:
                try:
                    val = int(data["active_backlogs"])
                    if val < 0:
                        return error_response("Active backlogs cannot be negative.")
                    active_backlogs = val
                except (ValueError, TypeError):
                    return error_response("Active backlogs must be a valid non-negative integer.")

            if "department_id" in data:
                try:
                    val = int(data["department_id"])
                    cursor.execute("SELECT department_id FROM department WHERE department_id = %s", (val,))
                    if not cursor.fetchone():
                        return error_response(f"Department with ID {val} does not exist.", status_code=400)
                    department_id = val
                except (ValueError, TypeError):
                    return error_response("Department ID must be a valid integer.")

            # Update core student table
            update_query = """
                UPDATE student SET
                    roll_number = %s,
                    student_name = %s,
                    email = %s,
                    date_of_birth = %s,
                    batch_year = %s,
                    cgpa = %s,
                    active_backlogs = %s,
                    department_id = %s
                WHERE student_id = %s
            """
            cursor.execute(
                update_query,
                (roll_number, student_name, email, dob, batch_year, cgpa, active_backlogs, department_id, student_id)
            )

            # Update phone numbers if provided
            if "phone_numbers" in data and isinstance(data["phone_numbers"], list):
                # Clean and insert new numbers
                cursor.execute("DELETE FROM student_phone WHERE student_id = %s", (student_id,))
                for p in data["phone_numbers"]:
                    if isinstance(p, dict) and p.get("phone_number"):
                        num = str(p["phone_number"]).strip()
                        ptype = str(p.get("phone_type", "Primary")).strip() or "Primary"
                        if num and len(num) <= 20:
                            cursor.execute("""
                                INSERT INTO student_phone (student_id, phone_number, phone_type)
                                VALUES (%s, %s, %s)
                                ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                            """, (student_id, num, ptype))
                    elif isinstance(p, str) and p.strip():
                        num = p.strip()
                        if len(num) <= 20:
                            cursor.execute("""
                                INSERT INTO student_phone (student_id, phone_number, phone_type)
                                VALUES (%s, %s, %s)
                                ON DUPLICATE KEY UPDATE phone_type = VALUES(phone_type)
                            """, (student_id, num, "Primary"))
            elif "phone" in data and str(data["phone"]).strip():
                # Single phone legacy update
                num = str(data["phone"]).strip()
                cursor.execute("DELETE FROM student_phone WHERE student_id = %s", (student_id,))
                cursor.execute("""
                    INSERT INTO student_phone (student_id, phone_number, phone_type)
                    VALUES (%s, %s, 'Primary')
                """, (student_id, num))

            cursor.execute("""
                SELECT 
                    s.student_id, s.roll_number, s.student_name, s.email,
                    s.date_of_birth, s.batch_year, s.cgpa, s.active_backlogs, s.department_id,
                    d.department_code, d.department_name
                FROM student s
                LEFT JOIN department d ON s.department_id = d.department_id
                WHERE s.student_id = %s
            """, (student_id,))
            updated_student = cursor.fetchone()
            _attach_student_phones(cursor, [updated_student])

            return success_response(
                data=updated_student,
                message="Student updated successfully."
            )
    except Exception as e:
        return handle_db_error(e)


@student_bp.route("/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """Delete a student by ID."""
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT student_id FROM student WHERE student_id = %s", (student_id,))
            if not cursor.fetchone():
                return error_response(f"Student with ID {student_id} not found.", status_code=404)

            # Deletion cascades to student_phone via FK CONSTRAINT
            cursor.execute("DELETE FROM student WHERE student_id = %s", (student_id,))
            return success_response(message="Student deleted successfully.")
    except Exception as e:
        return handle_db_error(e)
