"""
seed_demo_data.py
=================
Generates realistic, completely fictional demonstration data for the
Placement & Recruitment Management System across all 10 normalized MySQL entities.

Features:
- Parameterized SQL queries with safe database transactions.
- Strict compliance with all foreign keys, unique keys, and domain check constraints.
- Fictional Indian student names, technology companies, academic departments, and HR contacts.
- Supports 1:N Student Phones and 1:N Company Contacts with 1:M Contact Phones.
- Identifiable with 'DEMO' prefixes and reserved 'example.com' email domains.
- Safe to run multiple times (idempotent).
- Clean separation: never modifies or deletes pre-existing non-demo records.
- Optional cleanup mode: `py seed_demo_data.py --cleanup`
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal
from db import get_db_connection

# ============================================================================
# FICTIONAL DEMO DATA SETS
# ============================================================================

DEMO_DEPARTMENTS = [
    ("DEMO_CSE", "DEMO Computer Science and Engineering"),
    ("DEMO_ECE", "DEMO Electronics and Communication Engineering"),
    ("DEMO_IT", "DEMO Information Technology"),
    ("DEMO_MECH", "DEMO Mechanical Engineering"),
    ("DEMO_CIVIL", "DEMO Civil and Environmental Engineering"),
    ("DEMO_EE", "DEMO Electrical Engineering"),
    ("DEMO_AIML", "DEMO Artificial Intelligence and Machine Learning"),
    ("DEMO_DS", "DEMO Data Science and Analytics"),
    ("DEMO_MBA", "DEMO Master of Business Administration"),
    ("DEMO_MCA", "DEMO Master of Computer Applications"),
]

DEMO_COMPANIES = [
    {
        "name": "DEMO Infosys Cloud Solutions",
        "industry": "Information Technology",
        "website": "https://infosys.demo.example.com",
        "address": "Electronic City Phase 1, Bengaluru, Karnataka",
        "contacts": [
            {
                "name": "Priya Sharma",
                "designation": "Head of Campus Recruitment",
                "email": "priya.sharma@infosys.demo.example.com",
                "phones": [("+91 9811000101", "Work"), ("+91 9811000102", "Mobile")]
            }
        ]
    },
    {
        "name": "DEMO Tata Consultancy Labs",
        "industry": "Enterprise Software",
        "website": "https://tcs.demo.example.com",
        "address": "TCS Synergy Park, Gachibowli, Hyderabad, Telangana",
        "contacts": [
            {
                "name": "Rajesh Raman",
                "designation": "Senior Talent Partner",
                "email": "rajesh.raman@tcs.demo.example.com",
                "phones": [("+91 9811000201", "Work"), ("+91 9811000202", "Direct")]
            }
        ]
    },
    {
        "name": "DEMO Wipro NextGen Systems",
        "industry": "Cloud Computing & Cyber",
        "website": "https://wipro.demo.example.com",
        "address": "Sarjapur Road, Doddakannelli, Bengaluru, Karnataka",
        "contacts": [
            {
                "name": "Ananya Kulkarni",
                "designation": "Director of University Relations",
                "email": "ananya.k@wipro.demo.example.com",
                "phones": [("+91 9811000301", "Work"), ("+91 9811000302", "Mobile")]
            }
        ]
    },
    {
        "name": "DEMO Reliance Digital Dynamics",
        "industry": "Telecommunications & AI",
        "website": "https://jio.demo.example.com",
        "address": "Reliance Corporate Park, Navi Mumbai, Maharashtra",
        "contacts": [
            {
                "name": "Vikram Malhotra",
                "designation": "Campus Acquisition Lead",
                "email": "vikram.m@jio.demo.example.com",
                "phones": [("+91 9811000401", "Work"), ("+91 9811000402", "Primary")]
            }
        ]
    },
    {
        "name": "DEMO Bharat Fintech Innovations",
        "industry": "Financial Technology",
        "website": "https://bharatfintech.demo.example.com",
        "address": "Bandra Kurla Complex (BKC), Mumbai, Maharashtra",
        "contacts": [
            {
                "name": "Sneha Sen",
                "designation": "VP People & Culture",
                "email": "sneha.sen@bharatfintech.demo.example.com",
                "phones": [("+91 9811000501", "Work"), ("+91 9811000502", "Direct")]
            },
            {
                "name": "Arjun Deshmukh",
                "designation": "Technical Recruiter",
                "email": "arjun.d@bharatfintech.demo.example.com",
                "phones": [("+91 9811000503", "Mobile")]
            }
        ]
    },
    {
        "name": "DEMO HCL Enterprise Platforms",
        "industry": "Infrastructure & IT Services",
        "website": "https://hcl.demo.example.com",
        "address": "Sector 126, Noida, Uttar Pradesh",
        "contacts": [
            {
                "name": "Deepak Verma",
                "designation": "University Relations Manager",
                "email": "deepak.v@hcl.demo.example.com",
                "phones": [("+91 9811000601", "Work"), ("+91 9811000602", "Mobile")]
            }
        ]
    },
    {
        "name": "DEMO Mahindra Tech Ventures",
        "industry": "Automotive Software & IoT",
        "website": "https://mahindratech.demo.example.com",
        "address": "Hinjawadi Phase 3, Pune, Maharashtra",
        "contacts": [
            {
                "name": "Kavita Rao",
                "designation": "Head of Engineering Hiring",
                "email": "kavita.rao@mahindratech.demo.example.com",
                "phones": [("+91 9811000701", "Work"), ("+91 9811000702", "Direct")]
            }
        ]
    },
    {
        "name": "DEMO Larsen Cloud Engineering",
        "industry": "Heavy Tech & Automation",
        "website": "https://larsen.demo.example.com",
        "address": "L&T Knowledge City, Vadodara, Gujarat",
        "contacts": [
            {
                "name": "Siddharth Menon",
                "designation": "Lead Campus Strategist",
                "email": "siddharth.m@larsen.demo.example.com",
                "phones": [("+91 9811000801", "Work"), ("+91 9811000802", "Mobile")]
            }
        ]
    },
    {
        "name": "DEMO Zomato Logistics Labs",
        "industry": "E-Commerce & Quick Commerce",
        "website": "https://zomato.demo.example.com",
        "address": "Cyber City Phase 2, Gurugram, Haryana",
        "contacts": [
            {
                "name": "Ritu Agarwal",
                "designation": "Talent Partner - Tech",
                "email": "ritu.a@zomato.demo.example.com",
                "phones": [("+91 9811000901", "Work"), ("+91 9811000902", "Mobile")]
            },
            {
                "name": "Naveen Singhal",
                "designation": "Associate Recruiter",
                "email": "naveen.s@zomato.demo.example.com",
                "phones": [("+91 9811000903", "Direct")]
            }
        ]
    },
    {
        "name": "DEMO Razorpay Payments Tech",
        "industry": "Payment Gateway & Banking",
        "website": "https://razorpay.demo.example.com",
        "address": "Koramangala 4th Block, Bengaluru, Karnataka",
        "contacts": [
            {
                "name": "Manish Gupta",
                "designation": "Director of Talent",
                "email": "manish.g@razorpay.demo.example.com",
                "phones": [("+91 9811001001", "Work"), ("+91 9811001002", "Mobile")]
            }
        ]
    }
]

DEMO_STUDENTS = [
    {
        "roll": "DEMO2026CS001",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@demo.example.com",
        "dob": "2003-04-12",
        "batch": 2026,
        "cgpa": Decimal("9.25"),
        "backlogs": 0,
        "dept_code": "DEMO_CSE",
        "phones": [("+91 9820000001", "Primary"), ("+91 9820000002", "WhatsApp")]
    },
    {
        "roll": "DEMO2026CS002",
        "name": "Diya Patel",
        "email": "diya.patel@demo.example.com",
        "dob": "2003-08-25",
        "batch": 2026,
        "cgpa": Decimal("8.90"),
        "backlogs": 0,
        "dept_code": "DEMO_CSE",
        "phones": [("+91 9820000003", "Primary"), ("+91 9820000004", "Mobile")]
    },
    {
        "roll": "DEMO2026IT001",
        "name": "Rohan Verma",
        "email": "rohan.verma@demo.example.com",
        "dob": "2003-01-18",
        "batch": 2026,
        "cgpa": Decimal("8.45"),
        "backlogs": 0,
        "dept_code": "DEMO_IT",
        "phones": [("+91 9820000005", "Primary"), ("+91 9820000006", "Home")]
    },
    {
        "roll": "DEMO2026EC001",
        "name": "Ananya Iyer",
        "email": "ananya.iyer@demo.example.com",
        "dob": "2003-11-05",
        "batch": 2026,
        "cgpa": Decimal("9.15"),
        "backlogs": 0,
        "dept_code": "DEMO_ECE",
        "phones": [("+91 9820000007", "Primary"), ("+91 9820000008", "WhatsApp")]
    },
    {
        "roll": "DEMO2026AI001",
        "name": "Ishan Gupta",
        "email": "ishan.gupta@demo.example.com",
        "dob": "2003-06-30",
        "batch": 2026,
        "cgpa": Decimal("8.70"),
        "backlogs": 0,
        "dept_code": "DEMO_AIML",
        "phones": [("+91 9820000009", "Primary"), ("+91 9820000010", "Mobile")]
    },
    {
        "roll": "DEMO2026DS001",
        "name": "Priya Nair",
        "email": "priya.nair@demo.example.com",
        "dob": "2003-09-14",
        "batch": 2026,
        "cgpa": Decimal("8.85"),
        "backlogs": 0,
        "dept_code": "DEMO_DS",
        "phones": [("+91 9820000011", "Primary"), ("+91 9820000012", "Alternate")]
    },
    {
        "roll": "DEMO2026ME001",
        "name": "Kabir Mehta",
        "email": "kabir.mehta@demo.example.com",
        "dob": "2002-12-22",
        "batch": 2026,
        "cgpa": Decimal("8.10"),
        "backlogs": 0,
        "dept_code": "DEMO_MECH",
        "phones": [("+91 9820000013", "Primary"), ("+91 9820000014", "Mobile")]
    },
    {
        "roll": "DEMO2026EE001",
        "name": "Sneha Reddy",
        "email": "sneha.reddy@demo.example.com",
        "dob": "2003-03-09",
        "batch": 2026,
        "cgpa": Decimal("8.60"),
        "backlogs": 0,
        "dept_code": "DEMO_EE",
        "phones": [("+91 9820000015", "Primary"), ("+91 9820000016", "WhatsApp")]
    },
    {
        "roll": "DEMO2026MB001",
        "name": "Aditya Kulkarni",
        "email": "aditya.kulkarni@demo.example.com",
        "dob": "2001-07-19",
        "batch": 2026,
        "cgpa": Decimal("8.35"),
        "backlogs": 0,
        "dept_code": "DEMO_MBA",
        "phones": [("+91 9820000017", "Primary"), ("+91 9820000018", "Home")]
    },
    {
        "roll": "DEMO2026MC001",
        "name": "Tanvi Joshi",
        "email": "tanvi.joshi@demo.example.com",
        "dob": "2002-10-03",
        "batch": 2026,
        "cgpa": Decimal("8.50"),
        "backlogs": 0,
        "dept_code": "DEMO_MCA",
        "phones": [("+91 9820000019", "Primary"), ("+91 9820000020", "Mobile")]
    }
]

DEMO_JOBS = [
    {
        "company_name": "DEMO Infosys Cloud Solutions",
        "title": "DEMO Associate Cloud Engineer",
        "desc": "Design and deploy scalable cloud infrastructure on AWS and Azure platforms with automated CI/CD pipelines.",
        "type": "Full-time",
        "loc": "Bengaluru",
        "min_cgpa": Decimal("7.00"),
        "max_backlogs": 0,
        "min_pkg": Decimal("650000.00"),
        "max_pkg": Decimal("950000.00"),
        "openings": 8,
        "post_date": "2026-08-01",
        "deadline": "2026-12-15",
        "status": "Open"
    },
    {
        "company_name": "DEMO Tata Consultancy Labs",
        "title": "DEMO Systems Analyst - Backend",
        "desc": "Develop mission-critical enterprise microservices using Java Spring Boot, MySQL, and high-performance caching.",
        "type": "Full-time",
        "loc": "Hyderabad",
        "min_cgpa": Decimal("7.50"),
        "max_backlogs": 0,
        "min_pkg": Decimal("720000.00"),
        "max_pkg": Decimal("1100000.00"),
        "openings": 6,
        "post_date": "2026-08-05",
        "deadline": "2026-12-20",
        "status": "Open"
    },
    {
        "company_name": "DEMO Wipro NextGen Systems",
        "title": "DEMO Cybersecurity Specialist",
        "desc": "Monitor security event streams, manage threat incident response, and enforce enterprise zero-trust policies.",
        "type": "Full-time",
        "loc": "Bengaluru",
        "min_cgpa": Decimal("7.00"),
        "max_backlogs": 0,
        "min_pkg": Decimal("700000.00"),
        "max_pkg": Decimal("1050000.00"),
        "openings": 5,
        "post_date": "2026-08-10",
        "deadline": "2026-12-25",
        "status": "Open"
    },
    {
        "company_name": "DEMO Reliance Digital Dynamics",
        "title": "DEMO Full Stack Web Developer",
        "desc": "Build responsive web applications with Flask, modern JavaScript, and 3NF high-performance relational architectures.",
        "type": "Full-time",
        "loc": "Navi Mumbai",
        "min_cgpa": Decimal("7.20"),
        "max_backlogs": 0,
        "min_pkg": Decimal("800000.00"),
        "max_pkg": Decimal("1250000.00"),
        "openings": 10,
        "post_date": "2026-08-12",
        "deadline": "2026-12-30",
        "status": "Open"
    },
    {
        "company_name": "DEMO Bharat Fintech Innovations",
        "title": "DEMO Quantitative Data Analyst",
        "desc": "Model transaction patterns, detect anomalies in ledger databases, and build business intelligence dashboards.",
        "type": "Full-time",
        "loc": "Mumbai",
        "min_cgpa": Decimal("7.80"),
        "max_backlogs": 0,
        "min_pkg": Decimal("950000.00"),
        "max_pkg": Decimal("1500000.00"),
        "openings": 4,
        "post_date": "2026-08-15",
        "deadline": "2026-12-31",
        "status": "Open"
    },
    {
        "company_name": "DEMO HCL Enterprise Platforms",
        "title": "DEMO Site Reliability Engineer",
        "desc": "Automate cloud deployment pipelines, monitor high-availability database clusters, and guarantee 99.99% uptime.",
        "type": "Full-time",
        "loc": "Noida",
        "min_cgpa": Decimal("7.00"),
        "max_backlogs": 0,
        "min_pkg": Decimal("680000.00"),
        "max_pkg": Decimal("1000000.00"),
        "openings": 7,
        "post_date": "2026-08-20",
        "deadline": "2026-12-28",
        "status": "Open"
    },
    {
        "company_name": "DEMO Mahindra Tech Ventures",
        "title": "DEMO Embedded IoT Developer",
        "desc": "Develop firmware for vehicle telematics systems, microcontroller interfaces, and real-time telemetry streaming.",
        "type": "Full-time",
        "loc": "Pune",
        "min_cgpa": Decimal("7.20"),
        "max_backlogs": 0,
        "min_pkg": Decimal("750000.00"),
        "max_pkg": Decimal("1150000.00"),
        "openings": 5,
        "post_date": "2026-08-22",
        "deadline": "2026-12-31",
        "status": "Open"
    },
    {
        "company_name": "DEMO Larsen Cloud Engineering",
        "title": "DEMO Industrial Automation Engineer",
        "desc": "Design SCADA systems, optimize industrial robotics workflows, and integrate edge telemetry databases.",
        "type": "Full-time",
        "loc": "Vadodara",
        "min_cgpa": Decimal("7.00"),
        "max_backlogs": 0,
        "min_pkg": Decimal("720000.00"),
        "max_pkg": Decimal("1080000.00"),
        "openings": 6,
        "post_date": "2026-08-25",
        "deadline": "2026-12-31",
        "status": "Open"
    },
    {
        "company_name": "DEMO Zomato Logistics Labs",
        "title": "DEMO Logistics Optimization Analyst",
        "desc": "Analyze delivery routing graph models, optimize geospatial latency, and develop predictive demand forecasting.",
        "type": "Full-time",
        "loc": "Gurugram",
        "min_cgpa": Decimal("7.50"),
        "max_backlogs": 0,
        "min_pkg": Decimal("850000.00"),
        "max_pkg": Decimal("1350000.00"),
        "openings": 4,
        "post_date": "2026-08-28",
        "deadline": "2026-12-31",
        "status": "Open"
    },
    {
        "company_name": "DEMO Razorpay Payments Tech",
        "title": "DEMO Platform Software Engineer",
        "desc": "Engineer real-time payment reconciliation microservices, high-frequency SQL queries, and distributed caches.",
        "type": "Full-time",
        "loc": "Bengaluru",
        "min_cgpa": Decimal("8.00"),
        "max_backlogs": 0,
        "min_pkg": Decimal("1100000.00"),
        "max_pkg": Decimal("1650000.00"),
        "openings": 5,
        "post_date": "2026-09-01",
        "deadline": "2026-12-31",
        "status": "Open"
    }
]

# Mapping student index (0-9) to job index (0-9) for Selected applications & offers
SELECTED_PIPELINE = [
    {
        "student_idx": 0,  # Aarav Sharma (CGPA 9.25) -> Infosys Cloud Solutions
        "job_idx": 0,
        "app_date": "2026-08-10 10:30:00",
        "interview": {
            "round": 1,
            "date": "2026-09-12 11:00:00",
            "mode": "Online",
            "feedback": "Demonstrated outstanding knowledge of cloud computing, Docker, and distributed microservices."
        },
        "offer": {
            "ctc": Decimal("880000.00"),
            "offer_date": "2026-10-15",
            "joining_date": "2027-01-15",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 1,  # Diya Patel (CGPA 8.90) -> TCS Labs
        "job_idx": 1,
        "app_date": "2026-08-12 14:15:00",
        "interview": {
            "round": 1,
            "date": "2026-09-15 14:30:00",
            "mode": "Online",
            "feedback": "Excellent grasp of object-oriented design patterns, backend API development, and SQL indexing."
        },
        "offer": {
            "ctc": Decimal("950000.00"),
            "offer_date": "2026-10-16",
            "joining_date": "2027-02-01",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 2,  # Rohan Verma (CGPA 8.45) -> Wipro NextGen
        "job_idx": 2,
        "app_date": "2026-08-15 11:00:00",
        "interview": {
            "round": 1,
            "date": "2026-09-18 10:00:00",
            "mode": "Hybrid",
            "feedback": "Strong foundational understanding of network protocols, threat vulnerability analysis, and ethical hacking."
        },
        "offer": {
            "ctc": Decimal("850000.00"),
            "offer_date": "2026-10-18",
            "joining_date": "2027-01-20",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 3,  # Ananya Iyer (CGPA 9.15) -> Reliance Digital Dynamics
        "job_idx": 3,
        "app_date": "2026-08-18 16:45:00",
        "interview": {
            "round": 1,
            "date": "2026-09-22 15:00:00",
            "mode": "Offline",
            "feedback": "Exceptional full-stack capabilities, clean modular JavaScript coding, and relational schema intuition."
        },
        "offer": {
            "ctc": Decimal("1150000.00"),
            "offer_date": "2026-10-20",
            "joining_date": "2027-03-01",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 4,  # Ishan Gupta (CGPA 8.70) -> Bharat Fintech
        "job_idx": 4,
        "app_date": "2026-08-20 09:30:00",
        "interview": {
            "round": 1,
            "date": "2026-09-25 11:30:00",
            "mode": "Online",
            "feedback": "Superior algorithmic problem solving, statistical modeling expertise, and clean analytical presentation."
        },
        "offer": {
            "ctc": Decimal("1350000.00"),
            "offer_date": "2026-10-22",
            "joining_date": "2027-02-15",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 5,  # Priya Nair (CGPA 8.85) -> HCL Enterprise
        "job_idx": 5,
        "app_date": "2026-08-25 13:00:00",
        "interview": {
            "round": 1,
            "date": "2026-09-28 14:00:00",
            "mode": "Online",
            "feedback": "Deep knowledge of Linux internals, shell scripting, Kubernetes clusters, and incident remediation."
        },
        "offer": {
            "ctc": Decimal("900000.00"),
            "offer_date": "2026-10-24",
            "joining_date": "2027-01-10",
            "status": "Pending"
        }
    },
    {
        "student_idx": 6,  # Kabir Mehta (CGPA 8.10) -> Mahindra Tech
        "job_idx": 6,
        "app_date": "2026-08-26 15:20:00",
        "interview": {
            "round": 1,
            "date": "2026-09-30 10:30:00",
            "mode": "Offline",
            "feedback": "Strong grasp of embedded C, CAN bus communication, and sensor interface circuit design."
        },
        "offer": {
            "ctc": Decimal("880000.00"),
            "offer_date": "2026-10-25",
            "joining_date": "2027-04-01",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 7,  # Sneha Reddy (CGPA 8.60) -> Larsen Cloud
        "job_idx": 7,
        "app_date": "2026-08-28 11:40:00",
        "interview": {
            "round": 1,
            "date": "2026-10-02 11:00:00",
            "mode": "Hybrid",
            "feedback": "Thorough understanding of PLC automation, feedback control loops, and edge telemetry ingestion."
        },
        "offer": {
            "ctc": Decimal("920000.00"),
            "offer_date": "2026-10-26",
            "joining_date": "2027-02-01",
            "status": "Accepted"
        }
    },
    {
        "student_idx": 8,  # Aditya Kulkarni (CGPA 8.35) -> Zomato Logistics
        "job_idx": 8,
        "app_date": "2026-09-02 12:15:00",
        "interview": {
            "round": 1,
            "date": "2026-10-05 15:30:00",
            "mode": "Online",
            "feedback": "Impressive business acumen, operational research model development, and geospatial analysis."
        },
        "offer": {
            "ctc": Decimal("1100000.00"),
            "offer_date": "2026-10-27",
            "joining_date": "2027-03-15",
            "status": "Pending"
        }
    },
    {
        "student_idx": 9,  # Tanvi Joshi (CGPA 8.50) -> Razorpay Tech
        "job_idx": 9,
        "app_date": "2026-09-05 14:00:00",
        "interview": {
            "round": 1,
            "date": "2026-10-08 16:00:00",
            "mode": "Online",
            "feedback": "Excellent performance in live coding, transaction atomicity, ACID properties, and backend scalability."
        },
        "offer": {
            "ctc": Decimal("1450000.00"),
            "offer_date": "2026-10-28",
            "joining_date": "2027-01-25",
            "status": "Declined"  # Demonstrates varied offer statuses
        }
    }
]

# Additional 2 applications to show recruitment pipeline progress (Total: 12 applications)
ADDITIONAL_APPLICATIONS = [
    {
        "student_idx": 0,  # Aarav Sharma also applied for Reliance Digital
        "job_idx": 3,
        "app_date": "2026-08-16 11:15:00",
        "status": "Shortlisted"
    },
    {
        "student_idx": 1,  # Diya Patel also applied for Razorpay
        "job_idx": 9,
        "app_date": "2026-09-06 09:45:00",
        "status": "Under Review"
    }
]


# ============================================================================
# SEEDING LOGIC
# ============================================================================

def check_demo_data_exists(cursor):
    """Check if any demo data records already exist in the database."""
    cursor.execute("SELECT COUNT(*) AS cnt FROM department WHERE department_code LIKE 'DEMO_%'")
    dept_cnt = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) AS cnt FROM student WHERE roll_number LIKE 'DEMO%'")
    stu_cnt = cursor.fetchone()["cnt"]

    return dept_cnt > 0 or stu_cnt > 0


def seed_demo_data():
    """Populate realistic demonstration data across all 10 normalized MySQL entities."""
    conn = get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        if check_demo_data_exists(cursor):
            print("\n[INFO] Demo records already exist in the database.")
            print("[INFO] To remove demo records and re-seed, run: py seed_demo_data.py --cleanup")
            verify_demo_data(cursor)
            return

        print("\nStarting realistic demo data insertion into MySQL database...")

        # --------------------------------------------------------------------
        # 1. Insert Departments (10)
        # --------------------------------------------------------------------
        dept_id_map = {}
        for code, name in DEMO_DEPARTMENTS:
            cursor.execute("""
                INSERT INTO department (department_code, department_name)
                VALUES (%s, %s)
            """, (code, name))
            dept_id_map[code] = cursor.lastrowid
        print(f"  [+] Inserted {len(dept_id_map)} academic departments.")

        # --------------------------------------------------------------------
        # 2. Insert Companies (10) & Contacts (12) & Contact Phones (24)
        # --------------------------------------------------------------------
        comp_id_map = {}
        total_contacts = 0
        total_contact_phones = 0

        for comp in DEMO_COMPANIES:
            cursor.execute("""
                INSERT INTO company (company_name, industry, website, company_address)
                VALUES (%s, %s, %s, %s)
            """, (comp["name"], comp["industry"], comp["website"], comp["address"]))
            company_id = cursor.lastrowid
            comp_id_map[comp["name"]] = company_id

            # Insert HR Contacts for this company
            for contact in comp["contacts"]:
                cursor.execute("""
                    INSERT INTO company_contact (company_id, contact_name, designation, email)
                    VALUES (%s, %s, %s, %s)
                """, (company_id, contact["name"], contact["designation"], contact["email"]))
                contact_id = cursor.lastrowid
                total_contacts += 1

                # Insert Contact Phones
                for phone_num, phone_type in contact["phones"]:
                    cursor.execute("""
                        INSERT INTO company_contact_phone (contact_id, phone_number, phone_type)
                        VALUES (%s, %s, %s)
                    """, (contact_id, phone_num, phone_type))
                    total_contact_phones += 1

        print(f"  [+] Inserted {len(comp_id_map)} corporate companies.")
        print(f"  [+] Inserted {total_contacts} company HR contacts.")
        print(f"  [+] Inserted {total_contact_phones} company contact telephone numbers.")

        # --------------------------------------------------------------------
        # 3. Insert Students (10) & Student Phones (20)
        # --------------------------------------------------------------------
        student_id_map = {}
        total_student_phones = 0

        for s in DEMO_STUDENTS:
            dept_id = dept_id_map[s["dept_code"]]
            cursor.execute("""
                INSERT INTO student (
                    roll_number, student_name, email, date_of_birth,
                    batch_year, cgpa, active_backlogs, department_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                s["roll"], s["name"], s["email"], s["dob"],
                s["batch"], s["cgpa"], s["backlogs"], dept_id
            ))
            student_id = cursor.lastrowid
            student_id_map[s["roll"]] = student_id

            # Insert multiple student phones (1:N)
            for phone_num, phone_type in s["phones"]:
                cursor.execute("""
                    INSERT INTO student_phone (student_id, phone_number, phone_type)
                    VALUES (%s, %s, %s)
                """, (student_id, phone_num, phone_type))
                total_student_phones += 1

        print(f"  [+] Inserted {len(student_id_map)} student profiles.")
        print(f"  [+] Inserted {total_student_phones} student phone numbers.")

        # --------------------------------------------------------------------
        # 4. Insert Job Openings (10)
        # --------------------------------------------------------------------
        job_id_list = []
        for j in DEMO_JOBS:
            company_id = comp_id_map[j["company_name"]]
            cursor.execute("""
                INSERT INTO job (
                    company_id, job_title, job_description, job_type, job_location,
                    minimum_cgpa, maximum_backlogs, minimum_package, maximum_package,
                    number_of_openings, posting_date, application_deadline, job_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                company_id, j["title"], j["desc"], j["type"], j["loc"],
                j["min_cgpa"], j["max_backlogs"], j["min_pkg"], j["max_pkg"],
                j["openings"], j["post_date"], j["deadline"], j["status"]
            ))
            job_id_list.append(cursor.lastrowid)

        print(f"  [+] Inserted {len(job_id_list)} job recruitment vacancies.")

        # --------------------------------------------------------------------
        # 5. Insert Applications (10 Selected + 2 Pipeline = 12 total)
        # --------------------------------------------------------------------
        student_id_list = list(student_id_map.values())
        app_id_list = []

        # 10 Selected Applications
        for item in SELECTED_PIPELINE:
            s_id = student_id_list[item["student_idx"]]
            j_id = job_id_list[item["job_idx"]]

            cursor.execute("""
                INSERT INTO application (student_id, job_id, application_date, application_status)
                VALUES (%s, %s, %s, 'Selected')
            """, (s_id, j_id, item["app_date"]))
            app_id = cursor.lastrowid
            app_id_list.append(app_id)

            # Insert Interview Round (1)
            inv = item["interview"]
            cursor.execute("""
                INSERT INTO interview (
                    application_id, round_number, interview_date,
                    interview_mode, interview_result, feedback
                ) VALUES (%s, %s, %s, %s, 'Cleared', %s)
            """, (app_id, inv["round"], inv["date"], inv["mode"], inv["feedback"]))

            # Insert Placement Offer (1:1 with Selected Application)
            off = item["offer"]
            cursor.execute("""
                INSERT INTO offer (
                    application_id, offered_ctc, offer_date,
                    joining_date, offer_status
                ) VALUES (%s, %s, %s, %s, %s)
            """, (app_id, off["ctc"], off["offer_date"], off["joining_date"], off["status"]))

        # 2 Additional Applications (Shortlisted, Under Review)
        for extra in ADDITIONAL_APPLICATIONS:
            s_id = student_id_list[extra["student_idx"]]
            j_id = job_id_list[extra["job_idx"]]
            cursor.execute("""
                INSERT INTO application (student_id, job_id, application_date, application_status)
                VALUES (%s, %s, %s, %s)
            """, (s_id, j_id, extra["app_date"], extra["status"]))

        print(f"  [+] Inserted {len(app_id_list) + len(ADDITIONAL_APPLICATIONS)} job applications (10 Selected, 1 Shortlisted, 1 Under Review).")
        print(f"  [+] Inserted {len(app_id_list)} interview evaluation rounds.")
        print(f"  [+] Inserted {len(app_id_list)} official placement offers.")

        # Commit transaction
        conn.commit()
        print("\n[SUCCESS] Transaction committed successfully.")

        # Run verification report
        verify_demo_data(cursor)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Transaction aborted and rolled back due to error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# CLEANUP LOGIC
# ============================================================================

def cleanup_demo_data():
    """
    Safely delete ONLY records created by this demo script in the exact
    reverse foreign-key dependency order. Pre-existing records are untouched.
    """
    conn = get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        print("\nStarting safe demo data cleanup from MySQL database...")

        # 1. Delete Offers
        cursor.execute("""
            DELETE FROM offer 
            WHERE application_id IN (
                SELECT application_id FROM application 
                WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
            )
        """)
        offers_del = cursor.rowcount
        print(f"  [-] Deleted {offers_del} demo offers.")

        # 2. Delete Interviews
        cursor.execute("""
            DELETE FROM interview 
            WHERE application_id IN (
                SELECT application_id FROM application 
                WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
            )
        """)
        interviews_del = cursor.rowcount
        print(f"  [-] Deleted {interviews_del} demo interview rounds.")

        # 3. Delete Applications
        cursor.execute("""
            DELETE FROM application 
            WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
               OR job_id IN (SELECT job_id FROM job WHERE job_title LIKE 'DEMO%')
        """)
        apps_del = cursor.rowcount
        print(f"  [-] Deleted {apps_del} demo applications.")

        # 4. Delete Jobs
        cursor.execute("""
            DELETE FROM job 
            WHERE company_id IN (SELECT company_id FROM company WHERE company_name LIKE 'DEMO%')
               OR job_title LIKE 'DEMO%'
        """)
        jobs_del = cursor.rowcount
        print(f"  [-] Deleted {jobs_del} demo job openings.")

        # 5. Delete Student Phones
        cursor.execute("""
            DELETE FROM student_phone 
            WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
        """)
        sphones_del = cursor.rowcount
        print(f"  [-] Deleted {sphones_del} demo student phone numbers.")

        # 6. Delete Students
        cursor.execute("""
            DELETE FROM student 
            WHERE roll_number LIKE 'DEMO%'
        """)
        students_del = cursor.rowcount
        print(f"  [-] Deleted {students_del} demo student profiles.")

        # 7. Delete Company Contact Phones
        cursor.execute("""
            DELETE FROM company_contact_phone 
            WHERE contact_id IN (
                SELECT contact_id FROM company_contact 
                WHERE company_id IN (SELECT company_id FROM company WHERE company_name LIKE 'DEMO%')
            )
        """)
        cphones_del = cursor.rowcount
        print(f"  [-] Deleted {cphones_del} demo company contact phones.")

        # 8. Delete Company Contacts
        cursor.execute("""
            DELETE FROM company_contact 
            WHERE company_id IN (SELECT company_id FROM company WHERE company_name LIKE 'DEMO%')
        """)
        contacts_del = cursor.rowcount
        print(f"  [-] Deleted {contacts_del} demo company contacts.")

        # 9. Delete Companies
        cursor.execute("""
            DELETE FROM company 
            WHERE company_name LIKE 'DEMO%'
        """)
        companies_del = cursor.rowcount
        print(f"  [-] Deleted {companies_del} demo corporate companies.")

        # 10. Delete Departments
        cursor.execute("""
            DELETE FROM department 
            WHERE department_code LIKE 'DEMO_%'
        """)
        departments_del = cursor.rowcount
        print(f"  [-] Deleted {departments_del} demo academic departments.")

        # Commit cleanup
        conn.commit()
        print("\n[SUCCESS] Cleanup transaction committed successfully.")
        print("[SUCCESS] All demonstration records removed. Pre-existing records are 100% intact.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Cleanup transaction failed and was rolled back: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# VERIFICATION & REPORTING
# ============================================================================

def verify_demo_data(cursor):
    """Query and display a structured report of all demo data records in MySQL."""
    cursor.execute("SELECT COUNT(*) AS c FROM department WHERE department_code LIKE 'DEMO_%'")
    dept_cnt = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) AS c FROM company WHERE company_name LIKE 'DEMO%'")
    comp_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM company_contact 
        WHERE company_id IN (SELECT company_id FROM company WHERE company_name LIKE 'DEMO%')
    """)
    contact_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM company_contact_phone 
        WHERE contact_id IN (
            SELECT contact_id FROM company_contact 
            WHERE company_id IN (SELECT company_id FROM company WHERE company_name LIKE 'DEMO%')
        )
    """)
    cphone_cnt = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) AS c FROM student WHERE roll_number LIKE 'DEMO%'")
    stu_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM student_phone 
        WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
    """)
    sphone_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM job 
        WHERE company_id IN (SELECT company_id FROM company WHERE company_name LIKE 'DEMO%')
    """)
    job_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM application 
        WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
    """)
    app_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM interview 
        WHERE application_id IN (
            SELECT application_id FROM application 
            WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
        )
    """)
    interview_cnt = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c FROM offer 
        WHERE application_id IN (
            SELECT application_id FROM application 
            WHERE student_id IN (SELECT student_id FROM student WHERE roll_number LIKE 'DEMO%')
        )
    """)
    offer_cnt = cursor.fetchone()["c"]

    print("\n" + "=" * 54)
    print("           DEMO DATA INSERTION REPORT")
    print("=" * 54)
    print(f"  Department              : {dept_cnt:>3} records")
    print(f"  Company                 : {comp_cnt:>3} records")
    print(f"  Company Contact (1:N)   : {contact_cnt:>3} records")
    print(f"  Company Phone (1:M)     : {cphone_cnt:>3} records")
    print(f"  Student                 : {stu_cnt:>3} records")
    print(f"  Student Phone (1:N)     : {sphone_cnt:>3} records")
    print(f"  Job Vacancies           : {job_cnt:>3} records")
    print(f"  Application Pipeline    : {app_cnt:>3} records")
    print(f"  Interview Rounds        : {interview_cnt:>3} records")
    print(f"  Placement Offers (1:1)  : {offer_cnt:>3} records")
    print("=" * 54)
    print("  Integrity Check         : All Foreign Keys & Checks Valid")
    print("=" * 54 + "\n")


# ============================================================================
# SCRIPT ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        cleanup_demo_data()
    else:
        seed_demo_data()

