from flask import Blueprint, jsonify
from routes.utils import get_db_cursor, success_response, handle_db_error

database_design_bp = Blueprint("database_design", __name__, url_prefix="/api/database")

ALL_TEN_TABLES = [
    "department",
    "student",
    "student_phone",
    "company",
    "company_contact",
    "company_contact_phone",
    "job",
    "application",
    "interview",
    "offer"
]


@database_design_bp.route("/metadata", methods=["GET"])
def get_database_metadata():
    """
    Retrieve live schema metadata from MySQL INFORMATION_SCHEMA for all 10 normalized tables.
    Includes columns, data types, nullability, defaults, PKs, FKs, unique keys, and check constraints.
    """
    try:
        with get_db_cursor() as (conn, cursor):
            metadata = {}

            for table_name in ALL_TEN_TABLES:
                # 1. Row count
                cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table_name}`")
                row_count = cursor.fetchone()["cnt"]

                # 2. Columns metadata
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE,
                        COLUMN_DEFAULT, EXTRA, COLUMN_KEY, CHARACTER_MAXIMUM_LENGTH
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION ASC
                """, (table_name,))
                columns = cursor.fetchall()

                # 3. Primary Key
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
                    ORDER BY ORDINAL_POSITION ASC
                """, (table_name,))
                pk_cols = [r["COLUMN_NAME"] for r in cursor.fetchall()]

                # 4. Foreign Keys
                cursor.execute("""
                    SELECT 
                        kcu.COLUMN_NAME, kcu.CONSTRAINT_NAME,
                        kcu.REFERENCED_TABLE_NAME, kcu.REFERENCED_COLUMN_NAME,
                        rc.DELETE_RULE, rc.UPDATE_RULE
                    FROM information_schema.KEY_COLUMN_USAGE kcu
                    JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                        ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
                    WHERE kcu.TABLE_SCHEMA = DATABASE() AND kcu.TABLE_NAME = %s AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
                """, (table_name,))
                fks = cursor.fetchall()

                # 5. Table Constraints (Unique, Check, Primary, Foreign)
                cursor.execute("""
                    SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
                    FROM information_schema.TABLE_CONSTRAINTS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                """, (table_name,))
                constraints = cursor.fetchall()

                # 6. Check Constraints clauses
                cursor.execute("""
                    SELECT cc.CONSTRAINT_NAME, cc.CHECK_CLAUSE
                    FROM information_schema.CHECK_CONSTRAINTS cc
                    JOIN information_schema.TABLE_CONSTRAINTS tc
                        ON cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME AND cc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
                    WHERE cc.CONSTRAINT_SCHEMA = DATABASE() AND tc.TABLE_NAME = %s
                """, (table_name,))
                checks = cursor.fetchall()

                metadata[table_name] = {
                    "table_name": table_name,
                    "row_count": row_count,
                    "columns": columns,
                    "primary_key": pk_cols,
                    "is_composite_pk": len(pk_cols) > 1,
                    "foreign_keys": fks,
                    "constraints": constraints,
                    "check_constraints": checks
                }

            return success_response(data=metadata)
    except Exception as e:
        return handle_db_error(e)


@database_design_bp.route("/normalization", methods=["GET"])
def get_normalization_analysis():
    """
    Returns structured academic DBMS normalization analysis for 1NF, 2NF, and 3NF
    with explicit Functional Dependencies, Candidate Keys, and Decomposition explanations.
    """
    analysis = {
        "overview": {
            "title": "Comprehensive Database Normalization Analysis (1NF, 2NF, 3NF)",
            "context": "College Training and Placement (TNP) Directorate Management System",
            "total_entities": 10,
            "normal_form_achieved": "Third Normal Form (3NF)"
        },
        "normal_forms_defined": {
            "1NF": {
                "name": "First Normal Form (1NF)",
                "definition": "A relation is in 1NF if and only if all underlying domains contain only atomic (indivisible) values, there are no repeating groups, and each attribute contains a single value from its domain.",
                "remedy_in_project": "The multi-valued student phone numbers and company HR contacts were decomposed into dedicated relational child tables (student_phone and company_contact_phone)."
            },
            "2NF": {
                "name": "Second Normal Form (2NF)",
                "definition": "A relation is in 2NF if it is in 1NF and every non-prime attribute is fully functionally dependent on the entire primary key (no partial dependencies on any proper subset of a composite candidate key).",
                "remedy_in_project": "Composite primary key entities (student_phone, company_contact_phone, application, interview) strictly have attributes that depend on the complete composite key."
            },
            "3NF": {
                "name": "Third Normal Form (3NF)",
                "definition": "A relation is in 3NF if it is in 2NF and there is no transitive dependency (for every non-trivial functional dependency X -> Y, either X is a superkey or Y is a prime attribute).",
                "remedy_in_project": "Separated Department from Student, Company from Job, and Offers from Application to eliminate transitive dependencies."
            }
        },
        "entities_analysis": [
            {
                "table": "department",
                "primary_key": ["department_id"],
                "candidate_keys": [["department_id"], ["department_code"], ["department_name"]],
                "functional_dependencies": [
                    "department_id -> department_code, department_name",
                    "department_code -> department_id, department_name",
                    "department_name -> department_id, department_code"
                ],
                "normal_form": "3NF",
                "explanation": "Every determinant is a candidate key. No partial dependencies (single-attribute key) and no transitive dependencies."
            },
            {
                "table": "student",
                "primary_key": ["student_id"],
                "candidate_keys": [["student_id"], ["roll_number"], ["email"]],
                "functional_dependencies": [
                    "student_id -> roll_number, student_name, email, date_of_birth, batch_year, cgpa, active_backlogs, department_id",
                    "roll_number -> student_id, student_name, email, date_of_birth, batch_year, cgpa, active_backlogs, department_id",
                    "email -> student_id, roll_number, student_name, date_of_birth, batch_year, cgpa, active_backlogs, department_id"
                ],
                "normal_form": "3NF",
                "explanation": "Separating department attributes (department_name, department_code) eliminates transitive dependency student_id -> department_id -> department_name. Separating phone numbers into student_phone achieves 1NF atomicity."
            },
            {
                "table": "student_phone",
                "primary_key": ["student_id", "phone_number"],
                "candidate_keys": [["student_id", "phone_number"]],
                "functional_dependencies": [
                    "{student_id, phone_number} -> phone_type"
                ],
                "normal_form": "3NF",
                "explanation": "Decomposed from Student to eliminate multi-valued phone attributes (1NF). The non-prime attribute 'phone_type' depends on the full composite key {student_id, phone_number}, satisfying 2NF."
            },
            {
                "table": "company",
                "primary_key": ["company_id"],
                "candidate_keys": [["company_id"], ["company_name"], ["website"]],
                "functional_dependencies": [
                    "company_id -> company_name, industry, website, company_address",
                    "company_name -> company_id, industry, website, company_address"
                ],
                "normal_form": "3NF",
                "explanation": "Company attributes are distinct from Job vacancies. Multiple HR representatives are decomposed into company_contact to prevent repeating groups."
            },
            {
                "table": "company_contact",
                "primary_key": ["contact_id"],
                "candidate_keys": [["contact_id"], ["company_id", "email"]],
                "functional_dependencies": [
                    "contact_id -> company_id, contact_name, designation, email",
                    "{company_id, email} -> contact_id, contact_name, designation"
                ],
                "normal_form": "3NF",
                "explanation": "Allows 1:N HR personnel per company. All non-prime attributes functionally depend on the candidate key."
            },
            {
                "table": "company_contact_phone",
                "primary_key": ["contact_id", "phone_number"],
                "candidate_keys": [["contact_id", "phone_number"]],
                "functional_dependencies": [
                    "{contact_id, phone_number} -> phone_type"
                ],
                "normal_form": "3NF",
                "explanation": "Enables multiple phone lines per HR contact without repeating groups. 1NF and 2NF satisfied."
            },
            {
                "table": "job",
                "primary_key": ["job_id"],
                "candidate_keys": [["job_id"]],
                "functional_dependencies": [
                    "job_id -> company_id, job_title, job_description, job_type, job_location, minimum_cgpa, maximum_backlogs, minimum_package, maximum_package, number_of_openings, posting_date, application_deadline, job_status"
                ],
                "normal_form": "3NF",
                "explanation": "Job vacancy attributes depend directly on job_id. Company details are referenced via FK company_id, preventing update anomalies when company addresses change."
            },
            {
                "table": "application",
                "primary_key": ["application_id"],
                "candidate_keys": [["application_id"], ["student_id", "job_id"]],
                "functional_dependencies": [
                    "application_id -> student_id, job_id, application_date, application_status",
                    "{student_id, job_id} -> application_id, application_date, application_status"
                ],
                "normal_form": "3NF",
                "explanation": "Resolves the Many-to-Many (M:N) relationship between Student and Job. The non-key attributes application_date and application_status depend strictly on the student applying for that specific vacancy."
            },
            {
                "table": "interview",
                "primary_key": ["interview_id"],
                "candidate_keys": [["interview_id"], ["application_id", "round_number"]],
                "functional_dependencies": [
                    "interview_id -> application_id, round_number, interview_date, interview_mode, interview_result, feedback",
                    "{application_id, round_number} -> interview_id, interview_date, interview_mode, interview_result, feedback"
                ],
                "normal_form": "3NF",
                "explanation": "Decomposed from Application because an application can have 1:N interview rounds. The composite candidate key {application_id, round_number} uniquely identifies every evaluation round."
            },
            {
                "table": "offer",
                "primary_key": ["offer_id"],
                "candidate_keys": [["offer_id"], ["application_id"]],
                "functional_dependencies": [
                    "offer_id -> application_id, offered_ctc, offer_date, joining_date, offer_status",
                    "application_id -> offer_id, offered_ctc, offer_date, joining_date, offer_status"
                ],
                "normal_form": "3NF",
                "explanation": "Maintained separately from Application to avoid NULL fields for non-selected candidates. Candidate key application_id enforces a strict 1:1 relationship for successful offers."
            }
        ]
    }
    return success_response(data=analysis)

