"""
Verification Script for the 6 CRUD Modules:
1. Company
2. Student
3. Job
4. Application
5. Interview
6. Offer

Tests all 4 CRUD operations (CREATE, READ, UPDATE, DELETE) for each module,
respecting foreign-key dependencies, business validation rules, and proper cleanup.
"""

import sys
import json
from datetime import date, timedelta
from app import app
from db import get_db_connection


def run_verification():
    client = app.test_client()
    results = {}

    print("======================================================================")
    print("STARTING LIVE CRUD VERIFICATION FOR 6 MODULES")
    print("======================================================================")

    # Check database baseline
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    baseline_counts = {}
    tables = ['department', 'student', 'company', 'job', 'application', 'interview', 'offer']
    for t in tables:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {t}")
        baseline_counts[t] = cur.fetchone()['cnt']
    cur.close()
    conn.close()
    print("Baseline record counts:", baseline_counts)

    # Setup anchor department for student foreign keys
    anchor_dept_id = None
    try:
        # Check if a department exists; if not, create a temporary anchor department
        res = client.get("/api/departments")
        depts = res.get_json().get("data", [])
        if depts:
            anchor_dept_id = depts[0]["department_id"]
            created_anchor_dept = False
            print(f"Using pre-existing department ID {anchor_dept_id} for FK references.")
        else:
            dept_res = client.post("/api/departments", json={
                "department_code": "VERIFY_DEPT",
                "department_name": "Verification Department TNP"
            })
            assert dept_res.status_code == 201, f"Failed to create anchor dept: {dept_res.get_json()}"
            anchor_dept_id = dept_res.get_json()["data"]["department_id"]
            created_anchor_dept = True
            print(f"Created temporary anchor department ID {anchor_dept_id}")

        # ====================================================================
        # 1. COMPANY MODULE
        # ====================================================================
        print("\n--- [1/6] Verifying Company Module ---")
        comp_crud = {"CREATE": False, "READ": False, "UPDATE": False, "DELETE": False}
        try:
            # 1.1 CREATE
            comp_payload = {
                "company_name": "TestCorp Global Solutions",
                "industry": "Cloud Computing",
                "website": "https://testcorp-verify.example.com",
                "hr_contact_name": "Sarah Connor",
                "hr_email": "sarah.connor@testcorp-verify.com",
                "hr_phone": "+1-555-0199",
                "company_address": "400 Tech Hub Boulevard, Suite 500"
            }
            res = client.post("/api/companies", json=comp_payload)
            if res.status_code == 201 and res.get_json().get("success"):
                comp_data = res.get_json()["data"]
                company_id = comp_data["company_id"]
                comp_crud["CREATE"] = True
                print(f"  [CREATE] PASS - Company ID: {company_id}, Name: {comp_data['company_name']}")
            else:
                print(f"  [CREATE] FAIL - Status: {res.status_code}, Response: {res.get_json()}")
                raise Exception("Company CREATE failed")

            # 1.2 READ (All and By ID)
            res_all = client.get("/api/companies")
            res_one = client.get(f"/api/companies/{company_id}")
            if res_all.status_code == 200 and res_one.status_code == 200:
                one_data = res_one.get_json().get("data", {})
                all_ids = [c["company_id"] for c in res_all.get_json().get("data", [])]
                if company_id in all_ids and one_data.get("company_name") == comp_payload["company_name"]:
                    comp_crud["READ"] = True
                    print(f"  [READ] PASS - Retrieved successfully via GET /api/companies and GET /api/companies/{company_id}")
                else:
                    print("  [READ] FAIL - Data mismatch in GET response")
            else:
                print(f"  [READ] FAIL - Status all: {res_all.status_code}, one: {res_one.status_code}")

            # 1.3 UPDATE
            update_payload = {
                "hr_contact_name": "Sarah Connor-Reese",
                "hr_phone": "+1-555-0999",
                "company_address": "450 Innovation Parkway, Floor 12"
            }
            res_upd = client.put(f"/api/companies/{company_id}", json=update_payload)
            if res_upd.status_code == 200:
                upd_data = res_upd.get_json().get("data", {})
                if (upd_data.get("hr_contact_name") == "Sarah Connor-Reese" and
                    upd_data.get("hr_phone") == "+1-555-0999"):
                    comp_crud["UPDATE"] = True
                    print(f"  [UPDATE] PASS - Updated HR contact name & phone successfully")
                else:
                    print("  [UPDATE] FAIL - Returned data did not reflect update")
            else:
                print(f"  [UPDATE] FAIL - Status: {res_upd.status_code}, Response: {res_upd.get_json()}")

            # 1.4 DELETE
            res_del = client.delete(f"/api/companies/{company_id}")
            res_verify_del = client.get(f"/api/companies/{company_id}")
            if res_del.status_code == 200 and res_verify_del.status_code == 404:
                comp_crud["DELETE"] = True
                print(f"  [DELETE] PASS - Company ID {company_id} deleted and verified 404")
            else:
                print(f"  [DELETE] FAIL - Status del: {res_del.status_code}, get: {res_verify_del.status_code}")

        except Exception as e:
            print(f"  Company module exception: {e}")

        results["Company"] = comp_crud

        # Create persistent Company for downstream tests (Job -> Application -> ...)
        downstream_comp_res = client.post("/api/companies", json={
            "company_name": "Downstream Enterprise Ltd",
            "industry": "Enterprise Software",
            "website": "https://downstream-enterprise.com",
            "hr_contact_name": "David Miller",
            "hr_email": "hr@downstream-enterprise.com",
            "hr_phone": "+1-555-4321",
            "company_address": "100 Silicon Way"
        })
        assert downstream_comp_res.status_code == 201, f"Failed downstream company: {downstream_comp_res.get_json()}"
        ds_company_id = downstream_comp_res.get_json()["data"]["company_id"]
        print(f"Created downstream reference Company ID: {ds_company_id}")

        # ====================================================================
        # 2. STUDENT MODULE
        # ====================================================================
        print("\n--- [2/6] Verifying Student Module ---")
        stud_crud = {"CREATE": False, "READ": False, "UPDATE": False, "DELETE": False}
        try:
            # 2.1 CREATE
            stud_payload = {
                "roll_number": "TEST_ROLL_9901",
                "student_name": "Emily Watson",
                "email": "emily.watson.test@university.edu",
                "phone": "+91-9876543210",
                "date_of_birth": "2003-04-18",
                "batch_year": 2026,
                "cgpa": 9.15,
                "active_backlogs": 0,
                "department_id": anchor_dept_id
            }
            res = client.post("/api/students", json=stud_payload)
            if res.status_code == 201 and res.get_json().get("success"):
                stud_data = res.get_json()["data"]
                student_id = stud_data["student_id"]
                stud_crud["CREATE"] = True
                print(f"  [CREATE] PASS - Student ID: {student_id}, Roll: {stud_data['roll_number']}, Name: {stud_data['student_name']}")
            else:
                print(f"  [CREATE] FAIL - Status: {res.status_code}, Response: {res.get_json()}")
                raise Exception("Student CREATE failed")

            # 2.2 READ (All and By ID)
            res_all = client.get("/api/students")
            res_one = client.get(f"/api/students/{student_id}")
            if res_all.status_code == 200 and res_one.status_code == 200:
                one_data = res_one.get_json().get("data", {})
                all_ids = [s["student_id"] for s in res_all.get_json().get("data", [])]
                if student_id in all_ids and one_data.get("roll_number") == stud_payload["roll_number"]:
                    stud_crud["READ"] = True
                    print(f"  [READ] PASS - Retrieved successfully via GET /api/students and GET /api/students/{student_id}")
                else:
                    print("  [READ] FAIL - Data mismatch in GET response")
            else:
                print(f"  [READ] FAIL - Status all: {res_all.status_code}, one: {res_one.status_code}")

            # 2.3 UPDATE
            update_payload = {
                "phone": "+91-9876500000",
                "cgpa": 9.45
            }
            res_upd = client.put(f"/api/students/{student_id}", json=update_payload)
            if res_upd.status_code == 200:
                upd_data = res_upd.get_json().get("data", {})
                if upd_data.get("phone") == "+91-9876500000" and float(upd_data.get("cgpa")) == 9.45:
                    stud_crud["UPDATE"] = True
                    print("  [UPDATE] PASS - Updated student phone & CGPA to 9.45 successfully")
                else:
                    print("  [UPDATE] FAIL - Returned data did not reflect update")
            else:
                print(f"  [UPDATE] FAIL - Status: {res_upd.status_code}, Response: {res_upd.get_json()}")

            # 2.4 DELETE
            res_del = client.delete(f"/api/students/{student_id}")
            res_verify_del = client.get(f"/api/students/{student_id}")
            if res_del.status_code == 200 and res_verify_del.status_code == 404:
                stud_crud["DELETE"] = True
                print(f"  [DELETE] PASS - Student ID {student_id} deleted and verified 404")
            else:
                print(f"  [DELETE] FAIL - Status del: {res_del.status_code}, get: {res_verify_del.status_code}")

        except Exception as e:
            print(f"  Student module exception: {e}")

        results["Student"] = stud_crud

        # Create persistent Student for downstream tests (Application -> ...)
        downstream_stud_res = client.post("/api/students", json={
            "roll_number": "TEST_ROLL_DS_01",
            "student_name": "Marcus Aurelius",
            "email": "marcus.aurelius.test@university.edu",
            "phone": "+91-9123456789",
            "date_of_birth": "2003-01-10",
            "batch_year": 2026,
            "cgpa": 8.80,
            "active_backlogs": 0,
            "department_id": anchor_dept_id
        })
        assert downstream_stud_res.status_code == 201, f"Failed downstream student: {downstream_stud_res.get_json()}"
        ds_student_id = downstream_stud_res.get_json()["data"]["student_id"]
        print(f"Created downstream reference Student ID: {ds_student_id}")

        # ====================================================================
        # 3. JOB MODULE
        # ====================================================================
        print("\n--- [3/6] Verifying Job Module ---")
        job_crud = {"CREATE": False, "READ": False, "UPDATE": False, "DELETE": False}
        try:
            # 3.1 CREATE
            today = date.today()
            deadline = today + timedelta(days=60)
            job_payload = {
                "company_id": ds_company_id,
                "job_title": "Full Stack Software Engineer",
                "job_description": "Build scalable REST APIs and modern web applications.",
                "job_type": "Full-time",
                "job_location": "Remote / Bengaluru",
                "minimum_cgpa": 7.50,
                "maximum_backlogs": 0,
                "minimum_package": 800000.00,
                "maximum_package": 1200000.00,
                "number_of_openings": 4,
                "posting_date": today.isoformat(),
                "application_deadline": deadline.isoformat(),
                "job_status": "Open"
            }
            res = client.post("/api/jobs", json=job_payload)
            if res.status_code == 201 and res.get_json().get("success"):
                job_data = res.get_json()["data"]
                job_id = job_data["job_id"]
                job_crud["CREATE"] = True
                print(f"  [CREATE] PASS - Job ID: {job_id}, Title: {job_data['job_title']}")
            else:
                print(f"  [CREATE] FAIL - Status: {res.status_code}, Response: {res.get_json()}")
                raise Exception("Job CREATE failed")

            # 3.2 READ (All and By ID)
            res_all = client.get("/api/jobs")
            res_one = client.get(f"/api/jobs/{job_id}")
            if res_all.status_code == 200 and res_one.status_code == 200:
                one_data = res_one.get_json().get("data", {})
                all_ids = [j["job_id"] for j in res_all.get_json().get("data", [])]
                if job_id in all_ids and one_data.get("job_title") == job_payload["job_title"]:
                    job_crud["READ"] = True
                    print(f"  [READ] PASS - Retrieved successfully via GET /api/jobs and GET /api/jobs/{job_id}")
                else:
                    print("  [READ] FAIL - Data mismatch in GET response")
            else:
                print(f"  [READ] FAIL - Status all: {res_all.status_code}, one: {res_one.status_code}")

            # 3.3 UPDATE
            update_payload = {
                "job_location": "Hyderabad / Hybrid",
                "number_of_openings": 6,
                "maximum_package": 1400000.00
            }
            res_upd = client.put(f"/api/jobs/{job_id}", json=update_payload)
            if res_upd.status_code == 200:
                upd_data = res_upd.get_json().get("data", {})
                if (upd_data.get("job_location") == "Hyderabad / Hybrid" and
                    upd_data.get("number_of_openings") == 6 and
                    float(upd_data.get("maximum_package")) == 1400000.00):
                    job_crud["UPDATE"] = True
                    print("  [UPDATE] PASS - Updated location, openings & max package successfully")
                else:
                    print("  [UPDATE] FAIL - Returned data did not reflect update")
            else:
                print(f"  [UPDATE] FAIL - Status: {res_upd.status_code}, Response: {res_upd.get_json()}")

            # 3.4 DELETE
            res_del = client.delete(f"/api/jobs/{job_id}")
            res_verify_del = client.get(f"/api/jobs/{job_id}")
            if res_del.status_code == 200 and res_verify_del.status_code == 404:
                job_crud["DELETE"] = True
                print(f"  [DELETE] PASS - Job ID {job_id} deleted and verified 404")
            else:
                print(f"  [DELETE] FAIL - Status del: {res_del.status_code}, get: {res_verify_del.status_code}")

        except Exception as e:
            print(f"  Job module exception: {e}")

        results["Job"] = job_crud

        # Create persistent Job for downstream tests (Application -> ...)
        downstream_job_res = client.post("/api/jobs", json={
            "company_id": ds_company_id,
            "job_title": "Backend Systems Architect",
            "job_description": "Design core microservices with Python/Flask.",
            "job_type": "Full-time",
            "job_location": "Bengaluru",
            "minimum_cgpa": 7.00,
            "maximum_backlogs": 0,
            "minimum_package": 900000.00,
            "maximum_package": 1500000.00,
            "number_of_openings": 2,
            "posting_date": date.today().isoformat(),
            "application_deadline": (date.today() + timedelta(days=45)).isoformat(),
            "job_status": "Open"
        })
        assert downstream_job_res.status_code == 201, f"Failed downstream job: {downstream_job_res.get_json()}"
        ds_job_id = downstream_job_res.get_json()["data"]["job_id"]
        print(f"Created downstream reference Job ID: {ds_job_id}")

        # ====================================================================
        # 4. APPLICATION MODULE
        # ====================================================================
        print("\n--- [4/6] Verifying Application Module ---")
        app_crud = {"CREATE": False, "READ": False, "UPDATE": False, "DELETE": False}
        try:
            # 4.1 CREATE
            # Student ds_student_id (CGPA 8.80) applies for Job ds_job_id (Min CGPA 7.00)
            app_payload = {
                "student_id": ds_student_id,
                "job_id": ds_job_id,
                "application_status": "Applied"
            }
            res = client.post("/api/applications", json=app_payload)
            if res.status_code == 201 and res.get_json().get("success"):
                app_data = res.get_json()["data"]
                application_id = app_data["application_id"]
                app_crud["CREATE"] = True
                print(f"  [CREATE] PASS - Application ID: {application_id}, Status: {app_data['application_status']}")
            else:
                print(f"  [CREATE] FAIL - Status: {res.status_code}, Response: {res.get_json()}")
                raise Exception("Application CREATE failed")

            # 4.2 READ (All and By ID)
            res_all = client.get("/api/applications")
            res_one = client.get(f"/api/applications/{application_id}")
            if res_all.status_code == 200 and res_one.status_code == 200:
                one_data = res_one.get_json().get("data", {})
                all_ids = [a["application_id"] for a in res_all.get_json().get("data", [])]
                if application_id in all_ids and one_data.get("student_id") == ds_student_id:
                    app_crud["READ"] = True
                    print(f"  [READ] PASS - Retrieved successfully via GET /api/applications and GET /api/applications/{application_id}")
                else:
                    print("  [READ] FAIL - Data mismatch in GET response")
            else:
                print(f"  [READ] FAIL - Status all: {res_all.status_code}, one: {res_one.status_code}")

            # 4.3 UPDATE
            update_payload = {
                "application_status": "Under Review"
            }
            res_upd = client.put(f"/api/applications/{application_id}", json=update_payload)
            if res_upd.status_code == 200:
                upd_data = res_upd.get_json().get("data", {})
                if upd_data.get("application_status") == "Under Review":
                    app_crud["UPDATE"] = True
                    print("  [UPDATE] PASS - Updated application status to 'Under Review' successfully")
                else:
                    print("  [UPDATE] FAIL - Returned data did not reflect update")
            else:
                print(f"  [UPDATE] FAIL - Status: {res_upd.status_code}, Response: {res_upd.get_json()}")

            # 4.4 DELETE
            res_del = client.delete(f"/api/applications/{application_id}")
            res_verify_del = client.get(f"/api/applications/{application_id}")
            if res_del.status_code == 200 and res_verify_del.status_code == 404:
                app_crud["DELETE"] = True
                print(f"  [DELETE] PASS - Application ID {application_id} deleted and verified 404")
            else:
                print(f"  [DELETE] FAIL - Status del: {res_del.status_code}, get: {res_verify_del.status_code}")

        except Exception as e:
            print(f"  Application module exception: {e}")

        results["Application"] = app_crud

        # Create persistent Application for downstream tests (Interview -> Offer -> ...)
        downstream_app_res = client.post("/api/applications", json={
            "student_id": ds_student_id,
            "job_id": ds_job_id,
            "application_status": "Under Review"
        })
        assert downstream_app_res.status_code == 201, f"Failed downstream app: {downstream_app_res.get_json()}"
        ds_application_id = downstream_app_res.get_json()["data"]["application_id"]
        print(f"Created downstream reference Application ID: {ds_application_id}")

        # ====================================================================
        # 5. INTERVIEW MODULE
        # ====================================================================
        print("\n--- [5/6] Verifying Interview Module ---")
        int_crud = {"CREATE": False, "READ": False, "UPDATE": False, "DELETE": False}
        try:
            # 5.1 CREATE
            int_payload = {
                "application_id": ds_application_id,
                "round_number": 1,
                "interview_date": "2026-11-20 14:00:00",
                "interview_mode": "Online",
                "interview_result": "Pending",
                "feedback": "Initial technical screening scheduled."
            }
            res = client.post("/api/interviews", json=int_payload)
            if res.status_code == 201 and res.get_json().get("success"):
                int_data = res.get_json()["data"]
                interview_id = int_data["interview_id"]
                int_crud["CREATE"] = True
                print(f"  [CREATE] PASS - Interview ID: {interview_id}, Round: {int_data['round_number']}, Mode: {int_data['interview_mode']}")
            else:
                print(f"  [CREATE] FAIL - Status: {res.status_code}, Response: {res.get_json()}")
                raise Exception("Interview CREATE failed")

            # 5.2 READ (All and By ID)
            res_all = client.get("/api/interviews")
            res_one = client.get(f"/api/interviews/{interview_id}")
            if res_all.status_code == 200 and res_one.status_code == 200:
                one_data = res_one.get_json().get("data", {})
                all_ids = [i["interview_id"] for i in res_all.get_json().get("data", [])]
                if interview_id in all_ids and one_data.get("application_id") == ds_application_id:
                    int_crud["READ"] = True
                    print(f"  [READ] PASS - Retrieved successfully via GET /api/interviews and GET /api/interviews/{interview_id}")
                else:
                    print("  [READ] FAIL - Data mismatch in GET response")
            else:
                print(f"  [READ] FAIL - Status all: {res_all.status_code}, one: {res_one.status_code}")

            # 5.3 UPDATE
            update_payload = {
                "interview_result": "Cleared",
                "feedback": "Outstanding architectural depth, moves to next round."
            }
            res_upd = client.put(f"/api/interviews/{interview_id}", json=update_payload)
            if res_upd.status_code == 200:
                upd_data = res_upd.get_json().get("data", {})
                if (upd_data.get("interview_result") == "Cleared" and
                    "Outstanding" in upd_data.get("feedback", "")):
                    int_crud["UPDATE"] = True
                    print("  [UPDATE] PASS - Updated interview result to 'Cleared' and updated feedback")
                else:
                    print("  [UPDATE] FAIL - Returned data did not reflect update")
            else:
                print(f"  [UPDATE] FAIL - Status: {res_upd.status_code}, Response: {res_upd.get_json()}")

            # 5.4 DELETE
            res_del = client.delete(f"/api/interviews/{interview_id}")
            res_verify_del = client.get(f"/api/interviews/{interview_id}")
            if res_del.status_code == 200 and res_verify_del.status_code == 404:
                int_crud["DELETE"] = True
                print(f"  [DELETE] PASS - Interview ID {interview_id} deleted and verified 404")
            else:
                print(f"  [DELETE] FAIL - Status del: {res_del.status_code}, get: {res_verify_del.status_code}")

        except Exception as e:
            print(f"  Interview module exception: {e}")

        results["Interview"] = int_crud

        # ====================================================================
        # 6. OFFER MODULE
        # ====================================================================
        print("\n--- [6/6] Verifying Offer Module ---")
        offer_crud = {"CREATE": False, "READ": False, "UPDATE": False, "DELETE": False}
        try:
            # 6.0 Prerequisite check: Offer requires application_status == 'Selected'
            # First, update ds_application_id to 'Selected'
            upd_app_res = client.put(f"/api/applications/{ds_application_id}", json={
                "application_status": "Selected"
            })
            assert upd_app_res.status_code == 200, f"Failed updating app status: {upd_app_res.get_json()}"
            print("  [PREREQ] Application status successfully updated to 'Selected'")

            # 6.1 CREATE
            offer_date = date.today() + timedelta(days=5)
            joining_date = offer_date + timedelta(days=45)
            offer_payload = {
                "application_id": ds_application_id,
                "offered_ctc": 1250000.00,
                "offer_date": offer_date.isoformat(),
                "joining_date": joining_date.isoformat(),
                "offer_status": "Pending"
            }
            res = client.post("/api/offers", json=offer_payload)
            if res.status_code == 201 and res.get_json().get("success"):
                offer_data = res.get_json()["data"]
                offer_id = offer_data["offer_id"]
                offer_crud["CREATE"] = True
                print(f"  [CREATE] PASS - Offer ID: {offer_id}, CTC: {offer_data['offered_ctc']}, Status: {offer_data['offer_status']}")
            else:
                print(f"  [CREATE] FAIL - Status: {res.status_code}, Response: {res.get_json()}")
                raise Exception("Offer CREATE failed")

            # 6.2 READ (All and By ID)
            res_all = client.get("/api/offers")
            res_one = client.get(f"/api/offers/{offer_id}")
            if res_all.status_code == 200 and res_one.status_code == 200:
                one_data = res_one.get_json().get("data", {})
                all_ids = [o["offer_id"] for o in res_all.get_json().get("data", [])]
                if offer_id in all_ids and one_data.get("application_id") == ds_application_id:
                    offer_crud["READ"] = True
                    print(f"  [READ] PASS - Retrieved successfully via GET /api/offers and GET /api/offers/{offer_id}")
                else:
                    print("  [READ] FAIL - Data mismatch in GET response")
            else:
                print(f"  [READ] FAIL - Status all: {res_all.status_code}, one: {res_one.status_code}")

            # 6.3 UPDATE
            update_payload = {
                "offer_status": "Accepted",
                "offered_ctc": 1300000.00
            }
            res_upd = client.put(f"/api/offers/{offer_id}", json=update_payload)
            if res_upd.status_code == 200:
                upd_data = res_upd.get_json().get("data", {})
                if (upd_data.get("offer_status") == "Accepted" and
                    float(upd_data.get("offered_ctc")) == 1300000.00):
                    offer_crud["UPDATE"] = True
                    print("  [UPDATE] PASS - Updated offer status to 'Accepted' & CTC to 1,300,000")
                else:
                    print("  [UPDATE] FAIL - Returned data did not reflect update")
            else:
                print(f"  [UPDATE] FAIL - Status: {res_upd.status_code}, Response: {res_upd.get_json()}")

            # 6.4 DELETE
            res_del = client.delete(f"/api/offers/{offer_id}")
            res_verify_del = client.get(f"/api/offers/{offer_id}")
            if res_del.status_code == 200 and res_verify_del.status_code == 404:
                offer_crud["DELETE"] = True
                print(f"  [DELETE] PASS - Offer ID {offer_id} deleted and verified 404")
            else:
                print(f"  [DELETE] FAIL - Status del: {res_del.status_code}, get: {res_verify_del.status_code}")

        except Exception as e:
            print(f"  Offer module exception: {e}")

        results["Offer"] = offer_crud

        # ====================================================================
        # CLEANUP IN STRICT REVERSE FOREIGN-KEY ORDER
        # ====================================================================
        print("\n--- Cleaning up temporary downstream records in reverse foreign-key order ---")
        # 1. Application ds_application_id (Interview & Offer already deleted)
        del_app = client.delete(f"/api/applications/{ds_application_id}")
        print(f"  Deleted Downstream Application ID {ds_application_id}: status={del_app.status_code}")

        # 2. Job ds_job_id
        del_job = client.delete(f"/api/jobs/{ds_job_id}")
        print(f"  Deleted Downstream Job ID {ds_job_id}: status={del_job.status_code}")

        # 3. Student ds_student_id
        del_stud = client.delete(f"/api/students/{ds_student_id}")
        print(f"  Deleted Downstream Student ID {ds_student_id}: status={del_stud.status_code}")

        # 4. Company ds_company_id
        del_comp = client.delete(f"/api/companies/{ds_company_id}")
        print(f"  Deleted Downstream Company ID {ds_company_id}: status={del_comp.status_code}")

        # 5. Anchor Department (if created by this script)
        if created_anchor_dept:
            del_dept = client.delete(f"/api/departments/{anchor_dept_id}")
            print(f"  Deleted Temporary Anchor Department ID {anchor_dept_id}: status={del_dept.status_code}")

    except Exception as e:
        print(f"Verification script crashed with exception: {e}")
        import traceback
        traceback.print_exc()

    # Final database count verification
    print("\n--- Verifying final database row counts ---")
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    final_counts = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {t}")
        final_counts[t] = cur.fetchone()['cnt']
    cur.close()
    conn.close()
    print("Final record counts:", final_counts)
    assert final_counts == baseline_counts, f"Counts mismatch! Baseline: {baseline_counts}, Final: {final_counts}"
    print("Database is completely clean and matches baseline exactly!")

    # Summary table output
    print("\n======================================================================")
    print("SUMMARY RESULTS FOR 6 MODULES:")
    print("======================================================================")
    print(f"{'Module':<15} | {'CREATE':<8} | {'READ':<8} | {'UPDATE':<8} | {'DELETE':<8}")
    print("-" * 55)
    for mod, ops in results.items():
        c_str = "PASS" if ops["CREATE"] else "FAIL"
        r_str = "PASS" if ops["READ"] else "FAIL"
        u_str = "PASS" if ops["UPDATE"] else "FAIL"
        d_str = "PASS" if ops["DELETE"] else "FAIL"
        print(f"{mod:<15} | {c_str:<8} | {r_str:<8} | {u_str:<8} | {d_str:<8}")
    print("======================================================================")

    return results


if __name__ == "__main__":
    res = run_verification()
    # Check if all passed
    all_passed = True
    for mod, ops in res.items():
        if not all(ops.values()):
            all_passed = False
            break
    sys.exit(0 if all_passed else 1)

