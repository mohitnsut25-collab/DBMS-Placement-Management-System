import unittest
from unittest.mock import patch, MagicMock
import mysql.connector
from datetime import date, datetime
from decimal import Decimal

from app import app


class TestPlacementSystemAPI(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    # =============================================================
    # 1. Health and Home Endpoints
    # =============================================================
    def test_home_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        self.assertIn("Placement &amp; Recruitment Dashboard", response.get_data(as_text=True))

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "Connected Successfully")
        self.assertIn("tables", data)
        self.assertEqual(data["total_tables"], 10)

    # =============================================================
    # 2. Department Endpoints (CRUD, 404, Duplicates, FK restriction)
    # =============================================================
    @patch("routes.department.get_db_cursor")
    def test_get_departments_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"department_id": 1, "department_code": "CSE", "department_name": "Computer Science"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/departments")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 1)

    @patch("routes.department.get_db_cursor")
    def test_get_department_by_id_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"department_id": 1, "department_code": "CSE", "department_name": "Computer Science"}
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/departments/1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["department_code"], "CSE")

    @patch("routes.department.get_db_cursor")
    def test_get_department_by_id_not_found(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/departments/999")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.get_json()["success"])

    @patch("routes.department.get_db_cursor")
    def test_create_department_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = {
            "department_id": 1,
            "department_code": "CSE",
            "department_name": "Computer Science & Engineering"
        }
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"department_code": "CSE", "department_name": "Computer Science & Engineering"}
        response = self.client.post("/api/departments", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["department_code"], "CSE")

    def test_create_department_missing_fields(self):
        response = self.client.post("/api/departments", json={"department_code": ""})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    @patch("routes.department.get_db_cursor")
    def test_create_department_duplicate_409(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        error = mysql.connector.Error(errno=1062, msg="Duplicate entry 'CSE' for key 'department.uq_department_code'")
        mock_cursor.execute.side_effect = error
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"department_code": "CSE", "department_name": "Computer Science"}
        response = self.client.post("/api/departments", json=payload)
        self.assertEqual(response.status_code, 409)

    @patch("routes.department.get_db_cursor")
    def test_update_department_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"department_id": 1, "department_code": "CSE", "department_name": "Comp Sci"},
            {"department_id": 1, "department_code": "CS", "department_name": "Computer Science"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"department_code": "CS", "department_name": "Computer Science"}
        response = self.client.put("/api/departments/1", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["department_code"], "CS")

    @patch("routes.department.get_db_cursor")
    def test_delete_department_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"department_id": 1}
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.delete("/api/departments/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.get_json()["message"])

    @patch("routes.department.get_db_cursor")
    def test_delete_department_foreign_key_restriction_409(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"department_id": 1}
        error = mysql.connector.Error(errno=1451, msg="Cannot delete or update a parent row: a foreign key constraint fails")
        mock_cursor.execute.side_effect = [None, error]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.delete("/api/departments/1")
        self.assertEqual(response.status_code, 409)

    # =============================================================
    # 3. Student Endpoints (CRUD, Validations, FK Checks)
    # =============================================================
    @patch("routes.student.get_db_cursor")
    def test_get_all_students(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"student_id": 1, "roll_number": "CS01", "student_name": "Alice"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["data"]), 1)

    @patch("routes.student.get_db_cursor")
    def test_get_student_by_id_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"student_id": 1, "roll_number": "CS01", "student_name": "Alice"}
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/students/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["roll_number"], "CS01")

    @patch("routes.student.get_db_cursor")
    def test_create_student_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        # 1st fetchone: check department exists, 2nd: return created student
        mock_cursor.fetchone.side_effect = [
            {"department_id": 1},
            {
                "student_id": 1,
                "roll_number": "CS202601",
                "student_name": "Alex Smith",
                "email": "alex@example.com",
                "phone": "9876543210",
                "date_of_birth": "2002-05-15",
                "batch_year": 2026,
                "cgpa": 8.75,
                "active_backlogs": 0,
                "department_id": 1
            }
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "roll_number": "CS202601",
            "student_name": "Alex Smith",
            "email": "alex@example.com",
            "phone": "9876543210",
            "date_of_birth": "2002-05-15",
            "batch_year": 2026,
            "cgpa": 8.75,
            "department_id": 1
        }
        response = self.client.post("/api/students", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["data"]["roll_number"], "CS202601")

    def test_create_student_invalid_cgpa(self):
        payload = {
            "roll_number": "CS202601",
            "student_name": "Alex Smith",
            "email": "alex@example.com",
            "phone": "9876543210",
            "date_of_birth": "2002-05-15",
            "batch_year": 2026,
            "cgpa": 11.5,
            "department_id": 1
        }
        response = self.client.post("/api/students", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("CGPA must be between 0.0 and 10.0", response.get_json()["error"])

    def test_create_student_negative_backlogs(self):
        payload = {
            "roll_number": "CS202601",
            "student_name": "Alex Smith",
            "email": "alex@example.com",
            "phone": "9876543210",
            "date_of_birth": "2002-05-15",
            "batch_year": 2026,
            "cgpa": 8.5,
            "active_backlogs": -2,
            "department_id": 1
        }
        response = self.client.post("/api/students", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Active backlogs cannot be negative", response.get_json()["error"])

    def test_create_student_invalid_email(self):
        payload = {
            "roll_number": "CS202601",
            "student_name": "Alex Smith",
            "email": "not-an-email",
            "phone": "9876543210",
            "date_of_birth": "2002-05-15",
            "batch_year": 2026,
            "cgpa": 8.5,
            "department_id": 1
        }
        response = self.client.post("/api/students", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid email format", response.get_json()["error"])

    @patch("routes.student.get_db_cursor")
    def test_create_student_department_not_found(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "roll_number": "CS202601",
            "student_name": "Alex Smith",
            "email": "alex@example.com",
            "phone": "9876543210",
            "date_of_birth": "2002-05-15",
            "batch_year": 2026,
            "cgpa": 8.5,
            "department_id": 999
        }
        response = self.client.post("/api/students", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Department with ID 999 does not exist", response.get_json()["error"])

    @patch("routes.student.get_db_cursor")
    def test_update_student_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        existing = {
            "student_id": 1, "roll_number": "CS01", "student_name": "Alex", "email": "a@ex.com",
            "phone": "1234567890", "date_of_birth": date(2002, 1, 1), "batch_year": 2026,
            "cgpa": Decimal("8.00"), "active_backlogs": 0, "department_id": 1
        }
        updated = dict(existing, cgpa=Decimal("9.20"))
        mock_cursor.fetchone.side_effect = [existing, updated]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.put("/api/students/1", json={"cgpa": 9.20})
        self.assertEqual(response.status_code, 200)

    @patch("routes.student.get_db_cursor")
    def test_delete_student_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"student_id": 1}
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.delete("/api/students/1")
        self.assertEqual(response.status_code, 200)

    # =============================================================
    # 4. Company Endpoints (CRUD, Duplicate website/name, 404)
    # =============================================================
    @patch("routes.company.get_db_cursor")
    def test_get_all_companies(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"company_id": 1, "company_name": "Google", "industry": "IT"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/companies")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["data"]), 1)

    @patch("routes.company.get_db_cursor")
    def test_get_company_by_id_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"company_id": 1, "company_name": "Google"}
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/companies/1")
        self.assertEqual(response.status_code, 200)

    @patch("routes.company.get_db_cursor")
    def test_create_company_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = {
            "company_id": 1,
            "company_name": "Google",
            "industry": "Information Technology",
            "website": "https://google.com",
            "hr_contact_name": "John Doe",
            "hr_email": "hr@google.com",
            "hr_phone": "1234567890",
            "company_address": "Mountain View, CA"
        }
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "company_name": "Google",
            "industry": "Information Technology",
            "website": "https://google.com",
            "hr_contact_name": "John Doe",
            "hr_email": "hr@google.com",
            "hr_phone": "1234567890",
            "company_address": "Mountain View, CA"
        }
        response = self.client.post("/api/companies", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])

    @patch("routes.company.get_db_cursor")
    def test_update_company_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        existing = {
            "company_id": 1, "company_name": "Google", "industry": "IT",
            "website": "https://google.com", "hr_contact_name": "John",
            "hr_email": "hr@google.com", "hr_phone": "123", "company_address": "CA"
        }
        updated = dict(existing, hr_phone="9876543210")
        mock_cursor.fetchone.side_effect = [existing, updated]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.put("/api/companies/1", json={"hr_phone": "9876543210"})
        self.assertEqual(response.status_code, 200)

    @patch("routes.company.get_db_cursor")
    def test_delete_company_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"company_id": 1}
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.delete("/api/companies/1")
        self.assertEqual(response.status_code, 200)

    # =============================================================
    # 5. Job Endpoints (CRUD, Validations, FK Checks)
    # =============================================================
    @patch("routes.job.get_db_cursor")
    def test_get_all_jobs(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"job_id": 1, "job_title": "SDE"}]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)

    @patch("routes.job.get_db_cursor")
    def test_create_job_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [
            {"company_id": 1},  # Company check
            {"job_id": 1, "job_title": "Software Engineer"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "company_id": 1,
            "job_title": "Software Engineer",
            "job_description": "Full-stack development",
            "job_type": "Full-time",
            "job_location": "Bangalore",
            "minimum_cgpa": 7.0,
            "minimum_package": 600000,
            "maximum_package": 1200000,
            "number_of_openings": 5,
            "posting_date": "2026-10-01",
            "application_deadline": "2026-12-31"
        }
        response = self.client.post("/api/jobs", json=payload)
        self.assertEqual(response.status_code, 201)

    def test_create_job_invalid_package_range(self):
        payload = {
            "company_id": 1,
            "job_title": "Software Engineer",
            "job_description": "Develop full-stack applications",
            "job_type": "Full-time",
            "job_location": "Bangalore",
            "minimum_cgpa": 7.5,
            "minimum_package": 1200000,
            "maximum_package": 800000,
            "number_of_openings": 5,
            "posting_date": "2026-10-01",
            "application_deadline": "2026-12-31"
        }
        response = self.client.post("/api/jobs", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Maximum package cannot be less than minimum package", response.get_json()["error"])

    def test_create_job_invalid_deadline(self):
        payload = {
            "company_id": 1,
            "job_title": "Software Engineer",
            "job_description": "Develop full-stack applications",
            "job_type": "Full-time",
            "job_location": "Bangalore",
            "minimum_cgpa": 7.5,
            "minimum_package": 600000,
            "maximum_package": 1200000,
            "number_of_openings": 5,
            "posting_date": "2026-11-01",
            "application_deadline": "2026-10-01"
        }
        response = self.client.post("/api/jobs", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Application deadline cannot be earlier than posting date", response.get_json()["error"])

    def test_create_job_invalid_type(self):
        payload = {
            "company_id": 1,
            "job_title": "Software Engineer",
            "job_description": "Develop full-stack applications",
            "job_type": "Freelance",
            "job_location": "Bangalore",
            "minimum_cgpa": 7.5,
            "minimum_package": 600000,
            "maximum_package": 1200000,
            "number_of_openings": 5,
            "posting_date": "2026-10-01",
            "application_deadline": "2026-12-31"
        }
        response = self.client.post("/api/jobs", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid job type", response.get_json()["error"])

    # =============================================================
    # 6. Application Endpoints (CRUD, Business Validation)
    # =============================================================
    @patch("routes.application.get_db_cursor")
    def test_get_all_applications(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"application_id": 1, "student_id": 1, "job_id": 1}]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/applications")
        self.assertEqual(response.status_code, 200)

    @patch("routes.application.get_db_cursor")
    def test_application_ineligible_cgpa(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"student_id": 1, "student_name": "Bob", "cgpa": Decimal("6.50"), "active_backlogs": 0},
            {"job_id": 1, "job_title": "SDE", "job_status": "Open", "application_deadline": date(2027, 1, 1),
             "minimum_cgpa": Decimal("7.50"), "maximum_backlogs": 0},
            None
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"student_id": 1, "job_id": 1}
        response = self.client.post("/api/applications", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Eligibility check failed", response.get_json()["error"])
        self.assertIn("below the required minimum CGPA", response.get_json()["error"])

    @patch("routes.application.get_db_cursor")
    def test_application_ineligible_backlogs(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"student_id": 1, "student_name": "Bob", "cgpa": Decimal("8.50"), "active_backlogs": 2},
            {"job_id": 1, "job_title": "SDE", "job_status": "Open", "application_deadline": date(2027, 1, 1),
             "minimum_cgpa": Decimal("7.50"), "maximum_backlogs": 0},
            None
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"student_id": 1, "job_id": 1}
        response = self.client.post("/api/applications", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Eligibility check failed", response.get_json()["error"])
        self.assertIn("exceeds the maximum allowed", response.get_json()["error"])

    @patch("routes.application.get_db_cursor")
    def test_application_closed_job(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"student_id": 1, "student_name": "Bob", "cgpa": Decimal("8.50"), "active_backlogs": 0},
            {"job_id": 1, "job_title": "SDE", "job_status": "Closed", "application_deadline": date(2027, 1, 1),
             "minimum_cgpa": Decimal("7.50"), "maximum_backlogs": 0},
            None
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"student_id": 1, "job_id": 1}
        response = self.client.post("/api/applications", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only 'Open' vacancies accept applications", response.get_json()["error"])

    @patch("routes.application.get_db_cursor")
    def test_application_expired_deadline(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"student_id": 1, "student_name": "Bob", "cgpa": Decimal("8.50"), "active_backlogs": 0},
            {"job_id": 1, "job_title": "SDE", "job_status": "Open", "application_deadline": date(2020, 1, 1),
             "minimum_cgpa": Decimal("7.50"), "maximum_backlogs": 0},
            None
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"student_id": 1, "job_id": 1}
        response = self.client.post("/api/applications", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Application deadline", response.get_json()["error"])

    @patch("routes.application.get_db_cursor")
    def test_application_duplicate_409(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"student_id": 1, "student_name": "Bob", "cgpa": Decimal("8.50"), "active_backlogs": 0},
            {"job_id": 1, "job_title": "SDE", "job_status": "Open", "application_deadline": date(2027, 1, 1),
             "minimum_cgpa": Decimal("7.50"), "maximum_backlogs": 0},
            {"application_id": 10}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"student_id": 1, "job_id": 1}
        response = self.client.post("/api/applications", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("already applied", response.get_json()["error"])

    @patch("routes.application.get_db_cursor")
    def test_application_create_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [
            {"student_id": 1, "student_name": "Bob", "cgpa": Decimal("8.50"), "active_backlogs": 0},
            {"job_id": 1, "job_title": "SDE", "job_status": "Open", "application_deadline": date(2027, 1, 1),
             "minimum_cgpa": Decimal("7.50"), "maximum_backlogs": 0},
            None,  # No duplicate
            {"application_id": 1, "student_id": 1, "job_id": 1, "application_status": "Applied"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {"student_id": 1, "job_id": 1}
        response = self.client.post("/api/applications", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])

    # =============================================================
    # 7. Interview Endpoints (CRUD, Validations)
    # =============================================================
    @patch("routes.interview.get_db_cursor")
    def test_get_all_interviews(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"interview_id": 1, "round_number": 1}]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/interviews")
        self.assertEqual(response.status_code, 200)

    @patch("routes.interview.get_db_cursor")
    def test_create_interview_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [
            {"application_id": 1},  # Application exists
            None,  # Round not yet scheduled
            {"interview_id": 1, "round_number": 1, "interview_mode": "Online"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "application_id": 1,
            "round_number": 1,
            "interview_date": "2026-11-15 10:00:00",
            "interview_mode": "Online",
            "interview_result": "Pending"
        }
        response = self.client.post("/api/interviews", json=payload)
        self.assertEqual(response.status_code, 201)

    def test_create_interview_invalid_mode(self):
        payload = {
            "application_id": 1,
            "round_number": 1,
            "interview_date": "2026-11-15 10:00:00",
            "interview_mode": "Metaverse"
        }
        response = self.client.post("/api/interviews", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid interview mode", response.get_json()["error"])

    def test_create_interview_invalid_round_number(self):
        payload = {
            "application_id": 1,
            "round_number": 0,
            "interview_date": "2026-11-15 10:00:00",
            "interview_mode": "Online"
        }
        response = self.client.post("/api/interviews", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Round number must be a positive integer", response.get_json()["error"])

    # =============================================================
    # 8. Offer Endpoints (CRUD, Business Validation)
    # =============================================================
    @patch("routes.offer.get_db_cursor")
    def test_get_all_offers(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"offer_id": 1, "offered_ctc": 1200000}]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        response = self.client.get("/api/offers")
        self.assertEqual(response.status_code, 200)

    @patch("routes.offer.get_db_cursor")
    def test_create_offer_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [
            {"application_id": 1, "application_status": "Selected"},
            None,  # No existing offer
            {"offer_id": 1, "offered_ctc": 1200000, "offer_status": "Pending"}
        ]
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "application_id": 1,
            "offered_ctc": 1200000,
            "offer_date": "2026-11-01",
            "joining_date": "2027-01-01"
        }
        response = self.client.post("/api/offers", json=payload)
        self.assertEqual(response.status_code, 201)

    @patch("routes.offer.get_db_cursor")
    def test_offer_application_not_selected(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "application_id": 1,
            "application_status": "Under Review"
        }
        mock_get_db.return_value.__enter__.return_value = (mock_conn, mock_cursor)

        payload = {
            "application_id": 1,
            "offered_ctc": 1200000,
            "offer_date": "2026-11-01",
            "joining_date": "2027-01-01"
        }
        response = self.client.post("/api/offers", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Offers can only be issued for applications with status 'Selected'", response.get_json()["error"])

    def test_offer_invalid_joining_date(self):
        payload = {
            "application_id": 1,
            "offered_ctc": 1200000,
            "offer_date": "2026-11-10",
            "joining_date": "2026-11-01"
        }
        response = self.client.post("/api/offers", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Joining date cannot be earlier than offer date", response.get_json()["error"])

    def test_offer_invalid_ctc(self):
        payload = {
            "application_id": 1,
            "offered_ctc": -50000,
            "offer_date": "2026-11-01",
            "joining_date": "2027-01-01"
        }
        response = self.client.post("/api/offers", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Offered CTC must be greater than zero", response.get_json()["error"])

    # =============================================================
    # 9. Generic Error Handlers (404, 405)
    # =============================================================
    def test_nonexistent_route_404(self):
        response = self.client.get("/api/nonexistent")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
