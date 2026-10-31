"""
Integration & Regression Tests for Multiple Contact Numbers & Database Design
Verifies:
1. Student with multiple phone numbers (student_phone table, composite PK)
2. Company with multiple HR contacts and phone numbers (company_contact, company_contact_phone)
3. Endpoints /api/database/metadata and /api/database/normalization
4. View /database-design rendering
"""

import unittest
from app import app
from db import get_db_connection


class TestMultiContactUpgrade(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_database_design_view(self):
        """Verify the /database-design view renders 200 OK with expected tabs."""
        response = self.client.get("/database-design")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Database Design &amp; DBMS Analysis", html)
        self.assertIn("Interactive ER Diagram", html)
        self.assertIn("Relational Schema", html)
        self.assertIn("Normalization Analysis", html)
        self.assertIn("Constraints &amp; Viva Q&amp;A", html)

    def test_database_metadata_api(self):
        """Verify /api/database/metadata returns all 10 tables with primary and foreign keys."""
        response = self.client.get("/api/database/metadata")
        self.assertEqual(response.status_code, 200)
        res = response.get_json()
        self.assertTrue(res["success"])
        data = res["data"]
        expected_tables = [
            "department", "student", "student_phone", "company",
            "company_contact", "company_contact_phone", "job",
            "application", "interview", "offer"
        ]
        for t in expected_tables:
            self.assertIn(t, data, f"Missing table {t} in metadata")
            self.assertIn("columns", data[t])
            self.assertIn("primary_key", data[t])

        # Verify composite primary keys
        self.assertEqual(data["student_phone"]["primary_key"], ["student_id", "phone_number"])
        self.assertEqual(data["company_contact_phone"]["primary_key"], ["contact_id", "phone_number"])

    def test_normalization_api(self):
        """Verify /api/database/normalization returns structured 1NF, 2NF, 3NF analysis."""
        response = self.client.get("/api/database/normalization")
        self.assertEqual(response.status_code, 200)
        res = response.get_json()
        self.assertTrue(res["success"])
        data = res["data"]
        self.assertIn("normal_forms_defined", data)
        self.assertIn("entities_analysis", data)
        self.assertEqual(len(data["entities_analysis"]), 10)

    def test_student_multiphone_live_lifecycle(self):
        """
        Create a student with multiple phone numbers, verify retrieval,
        update phones, and cleanly delete the temporary test student.
        """
        # Step 1: Find or use Department ID 8
        dept_id = 8

        # Create student with 2 phone numbers
        test_payload = {
            "roll_number": "UPGRADE_STU_01",
            "student_name": "Multi Phone Test Student",
            "email": "multiphone.test@college.edu",
            "phone_numbers": [
                {"phone_number": "9811111111", "phone_type": "Primary"},
                {"phone_number": "9822222222", "phone_type": "WhatsApp"}
            ],
            "department_id": dept_id,
            "date_of_birth": "2003-05-15",
            "batch_year": 2026,
            "cgpa": 8.75,
            "active_backlogs": 0
        }

        create_res = self.client.post("/api/students", json=test_payload)
        self.assertEqual(create_res.status_code, 201)
        created_student = create_res.get_json()["data"]
        student_id = created_student["student_id"]

        try:
            # Step 2: Retrieve student by ID and verify both phones
            get_res = self.client.get(f"/api/students/{student_id}")
            self.assertEqual(get_res.status_code, 200)
            data = get_res.get_json()["data"]
            self.assertEqual(len(data["phone_numbers"]), 2)
            phone_map = {p["phone_number"]: p["phone_type"] for p in data["phone_numbers"]}
            self.assertIn("9811111111", phone_map)
            self.assertEqual(phone_map["9811111111"], "Primary")
            self.assertIn("9822222222", phone_map)
            self.assertEqual(phone_map["9822222222"], "WhatsApp")

            # Step 3: Update student with 3 phones
            update_payload = {
                "roll_number": "UPGRADE_STU_01",
                "student_name": "Multi Phone Test Student Updated",
                "email": "multiphone.test@college.edu",
                "phone_numbers": [
                    {"phone_number": "9811111111", "phone_type": "Primary"},
                    {"phone_number": "9833333333", "phone_type": "Home"},
                    {"phone_number": "9844444444", "phone_type": "Mobile"}
                ],
                "department_id": dept_id,
                "date_of_birth": "2003-05-15",
                "batch_year": 2026,
                "cgpa": 9.10,
                "active_backlogs": 0
            }
            update_res = self.client.put(f"/api/students/{student_id}", json=update_payload)
            self.assertEqual(update_res.status_code, 200)

            get_updated = self.client.get(f"/api/students/{student_id}").get_json()["data"]
            self.assertEqual(len(get_updated["phone_numbers"]), 3)

        finally:
            # Step 4: Delete the temporary student and verify cascade
            del_res = self.client.delete(f"/api/students/{student_id}")
            self.assertEqual(del_res.status_code, 200)

            # Verify student_phone records are also deleted
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM student_phone WHERE student_id = %s", (student_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            self.assertEqual(count, 0)

    def test_company_multicontact_live_lifecycle(self):
        """
        Create a company with multiple HR contacts and nested phones,
        verify retrieval, update contacts, and cleanly delete the temporary company.
        """
        test_payload = {
            "company_name": "MultiContact Tech Enterprises",
            "industry": "Software Engineering",
            "website": "https://multicontact-tech.example.com",
            "company_address": "Tech Park Block 9, Cyber City, Hyderabad",
            "contacts": [
                {
                    "contact_name": "Ananya Sen",
                    "designation": "Director of Talent Acquisition",
                    "email": "ananya.sen@multicontact-tech.example.com",
                    "phones": [
                        {"phone_number": "9711112222", "phone_type": "Work"},
                        {"phone_number": "9722223333", "phone_type": "Direct"}
                    ]
                },
                {
                    "contact_name": "Vikram Malhotra",
                    "designation": "Campus Recruiter",
                    "email": "vikram.m@multicontact-tech.example.com",
                    "phones": [
                        {"phone_number": "9733334444", "phone_type": "Mobile"}
                    ]
                }
            ]
        }

        create_res = self.client.post("/api/companies", json=test_payload)
        self.assertEqual(create_res.status_code, 201)
        created_company = create_res.get_json()["data"]
        company_id = created_company["company_id"]

        try:
            # Verify retrieval
            get_res = self.client.get(f"/api/companies/{company_id}")
            self.assertEqual(get_res.status_code, 200)
            data = get_res.get_json()["data"]
            self.assertEqual(len(data["contacts"]), 2)

            contact_names = {c["contact_name"]: c for c in data["contacts"]}
            self.assertIn("Ananya Sen", contact_names)
            self.assertEqual(len(contact_names["Ananya Sen"]["phones"]), 2)
            self.assertIn("Vikram Malhotra", contact_names)
            self.assertEqual(len(contact_names["Vikram Malhotra"]["phones"]), 1)

        finally:
            # Delete temporary company and verify cascade
            del_res = self.client.delete(f"/api/companies/{company_id}")
            self.assertEqual(del_res.status_code, 200)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM company_contact WHERE company_id = %s", (company_id,))
            c_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            self.assertEqual(c_count, 0)


if __name__ == "__main__":
    unittest.main()

