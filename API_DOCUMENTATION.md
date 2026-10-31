# Placement & Recruitment Management System - API Documentation

Backend REST API documentation for the College Training and Placement (TNP) Department Management System.

Built with **Python Flask**, **MySQL 8.0**, and **mysql-connector-python**.

---

## 1. System Overview & Base URL

- **Base URL**: `http://127.0.0.1:5000`
- **Content-Type**: `application/json`
- **Database**: MySQL `placement_recruitment_db` (Normalized to 3NF)

### Standard HTTP Status Codes

| Status Code | Description | Usage Scenario |
|-------------|-------------|----------------|
| `200 OK` | Request succeeded | Successful GET, PUT, or DELETE operation |
| `201 Created` | Resource created | Successful POST operation |
| `400 Bad Request` | Client validation error | Missing fields, invalid types, failed business rules |
| `404 Not Found` | Resource not found | Target ID does not exist in the database |
| `409 Conflict` | Constraint conflict | Duplicate unique key or foreign-key deletion restriction |
| `500 Server Error` | Database/server error | Internal unhandled database or server exception |

---

## 2. System Endpoints

### 2.1 System Status & Health

#### Home Endpoint
- **URL**: `GET /`
- **Description**: Verifies the Flask backend is active.
- **Response `200 OK`**:
```json
{
  "message": "Placement & Recruitment Management System",
  "status": "Backend is running"
}
```

#### MySQL Database Health Check
- **URL**: `GET /api/health`
- **Description**: Verifies MySQL connectivity and table presence across all 10 normalized entities.
- **Response `200 OK`**:
```json
{
  "database": "placement_recruitment_db",
  "mysql_version": "8.0.46",
  "status": "Connected Successfully",
  "tables": [
    "application",
    "company",
    "company_contact",
    "company_contact_phone",
    "department",
    "interview",
    "job",
    "offer",
    "student",
    "student_phone"
  ],
  "total_tables": 10
}
```

---

## 3. Entity CRUD APIs

---

### 3.1 Department Module (`/api/departments`)

Manages academic departments offering programs within the institution.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/departments` | List all departments |
| `GET` | `/api/departments/<id>` | Get department by ID |
| `POST` | `/api/departments` | Create new department |
| `PUT` | `/api/departments/<id>` | Update department |
| `DELETE` | `/api/departments/<id>` | Delete department |

#### Create Department
- **POST** `/api/departments`
- **Required Fields**: `department_code` (str, max 15, unique), `department_name` (str, max 100, unique)
- **Request Body**:
```json
{
  "department_code": "CSE",
  "department_name": "Computer Science & Engineering"
}
```
- **Response `201 Created`**:
```json
{
  "data": {
    "department_code": "CSE",
    "department_id": 1,
    "department_name": "Computer Science & Engineering"
  },
  "message": "Department created successfully.",
  "success": true
}
```

#### Update Department
- **PUT** `/api/departments/1`
- **Request Body** (accepts partial or full update):
```json
{
  "department_name": "Computer Science and Engineering"
}
```
- **Response `200 OK`**:
```json
{
  "data": {
    "department_code": "CSE",
    "department_id": 1,
    "department_name": "Computer Science and Engineering"
  },
  "message": "Department updated successfully.",
  "success": true
}
```

#### Delete Department
- **DELETE** `/api/departments/1`
- **Response `200 OK`**:
```json
{
  "message": "Department deleted successfully.",
  "success": true
}
```
- *Note*: Returns `409 Conflict` if students are enrolled in this department.

---

### 3.2 Student Module (`/api/students`)

Manages student academic records, backlogs, department affiliation, and multiple normalized contact phone numbers (`student_phone`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/students` | List all students (with department details and phone numbers list) |
| `GET` | `/api/students/<id>` | Get student by ID (includes `phone_numbers` array) |
| `POST` | `/api/students` | Register a student with multiple phone numbers |
| `PUT` | `/api/students/<id>` | Update student details and synchronize contact numbers |
| `DELETE` | `/api/students/<id>` | Delete student (cascades to `student_phone`) |

#### Business Rules & Validations:
- `cgpa`: Must be between `0.0` and `10.0`.
- `active_backlogs`: Must be non-negative (`>= 0`).
- `date_of_birth`: Must be a valid date in the past (`YYYY-MM-DD`).
- `batch_year`: Valid integer between `1990` and `2100`.
- `email`: Valid email syntax, max 254 characters, unique.
- `roll_number`: Unique alphanumeric string, max 30 characters.
- `department_id`: Must refer to an existing department.
- `phone_numbers`: Array of `{phone_number: str, phone_type: str}`. Composite PK `(student_id, phone_number)` prevents duplicates per student.

#### Create Student
- **POST** `/api/students`
- **Request Body**:
```json
{
  "roll_number": "2026CS101",
  "student_name": "John Doe",
  "email": "john.doe@college.edu",
  "phone_numbers": [
    {"phone_number": "9876543210", "phone_type": "Primary"},
    {"phone_number": "9876543211", "phone_type": "WhatsApp"}
  ],
  "date_of_birth": "2003-05-20",
  "batch_year": 2026,
  "cgpa": 8.75,
  "active_backlogs": 0,
  "department_id": 1
}
```
*(Backward compatibility: Single `"phone": "9876543210"` string is also accepted).*
- **Response `201 Created`**:
```json
{
  "data": {
    "active_backlogs": 0,
    "batch_year": 2026,
    "cgpa": 8.75,
    "date_of_birth": "2003-05-20",
    "department_code": "CSE",
    "department_id": 1,
    "department_name": "Computer Science & Engineering",
    "email": "john.doe@college.edu",
    "phone": "9876543210",
    "phone_numbers": [
      {"phone_number": "9876543210", "phone_type": "Primary"},
      {"phone_number": "9876543211", "phone_type": "WhatsApp"}
    ],
    "roll_number": "2026CS101",
    "student_id": 1,
    "student_name": "John Doe"
  },
  "message": "Student registered successfully.",
  "success": true
}
```

---

### 3.3 Company Module (`/api/companies`)

Manages recruiting partner companies, sectors, and multiple normalized HR contacts (`company_contact`) with multiple phone lines (`company_contact_phone`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/companies` | List all companies with nested contacts and phone directories |
| `GET` | `/api/companies/<id>` | Get company by ID with full contact information |
| `POST` | `/api/companies` | Register a recruiting company with multiple HR contacts |
| `PUT` | `/api/companies/<id>` | Update company details and synchronize HR contacts |
| `DELETE` | `/api/companies/<id>` | Delete company (cascades to contacts and phones) |
| `GET` | `/api/companies/<id>/contacts` | List HR contacts for a specific company |
| `POST` | `/api/companies/<id>/contacts` | Add a new HR contact to a company |
| `PUT` | `/api/companies/contacts/<contact_id>` | Update a specific HR contact |
| `DELETE` | `/api/companies/contacts/<contact_id>` | Delete a specific HR contact |

#### Create Company
- **POST** `/api/companies`
- **Required Fields**: `company_name`, `industry`, `company_address`, `contacts` array
- **Optional Fields**: `website` (unique if provided)
- **Request Body**:
```json
{
  "company_name": "Infosys Technologies",
  "industry": "Information Technology",
  "website": "https://www.infosys.com",
  "company_address": "Electronic City, Bangalore, Karnataka",
  "contacts": [
    {
      "contact_name": "Priya Sharma",
      "designation": "Lead Campus Recruiter",
      "email": "priya.sharma@infosys.com",
      "phones": [
        {"phone_number": "9812345678", "phone_type": "Work"},
        {"phone_number": "9812345679", "phone_type": "Mobile"}
      ]
    }
  ]
}
```
*(Backward compatibility: Legacy fields `hr_contact_name`, `hr_email`, `hr_phone` are also supported).*
- **Response `201 Created`**:
```json
{
  "data": {
    "company_address": "Electronic City, Bangalore, Karnataka",
    "company_id": 1,
    "company_name": "Infosys Technologies",
    "contacts": [
      {
        "contact_id": 1,
        "contact_name": "Priya Sharma",
        "designation": "Lead Campus Recruiter",
        "email": "priya.sharma@infosys.com",
        "phones": [
          {"phone_number": "9812345678", "phone_type": "Work"},
          {"phone_number": "9812345679", "phone_type": "Mobile"}
        ]
      }
    ],
    "hr_contact_name": "Priya Sharma",
    "hr_email": "priya.sharma@infosys.com",
    "hr_phone": "9812345678",
    "industry": "Information Technology",
    "website": "https://www.infosys.com"
  },
  "message": "Company registered successfully.",
  "success": true
}
```

---

### 3.4 Job Module (`/api/jobs`)

Manages recruitment vacancies posted by companies.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs` | List all jobs with company name |
| `GET` | `/api/jobs/<id>` | Get job vacancy by ID |
| `POST` | `/api/jobs` | Post a new job vacancy |
| `PUT` | `/api/jobs/<id>` | Update job vacancy |
| `DELETE` | `/api/jobs/<id>` | Delete job vacancy |

#### Business Rules & Validations:
- `job_type`: Must be one of `['Full-time', 'Internship', 'Contract']`.
- `job_status`: Must be one of `['Open', 'Closed', 'On Hold', 'Cancelled']`. Default: `'Open'`.
- `minimum_cgpa`: Between `0.0` and `10.0`.
- `maximum_backlogs`: Non-negative integer (`>= 0`). Default: `0`.
- `minimum_package`: Non-negative decimal (`>= 0`).
- `maximum_package`: Must be `>= minimum_package`.
- `number_of_openings`: Positive integer (`> 0`).
- `application_deadline`: Must be on or after `posting_date`.

#### Create Job
- **POST** `/api/jobs`
- **Request Body**:
```json
{
  "company_id": 1,
  "job_title": "Associate Software Engineer",
  "job_description": "Core software engineering in Java/Python and cloud platforms.",
  "job_type": "Full-time",
  "job_location": "Bangalore / Hybrid",
  "minimum_cgpa": 7.00,
  "maximum_backlogs": 0,
  "minimum_package": 650000.00,
  "maximum_package": 900000.00,
  "number_of_openings": 10,
  "posting_date": "2026-10-01",
  "application_deadline": "2026-12-31",
  "job_status": "Open"
}
```
- **Response `201 Created`**:
```json
{
  "data": {
    "application_deadline": "2026-12-31",
    "company_id": 1,
    "company_name": "Infosys Technologies",
    "job_description": "Core software engineering in Java/Python and cloud platforms.",
    "job_id": 1,
    "job_location": "Bangalore / Hybrid",
    "job_status": "Open",
    "job_title": "Associate Software Engineer",
    "job_type": "Full-time",
    "maximum_backlogs": 0,
    "maximum_package": 900000.0,
    "minimum_cgpa": 7.0,
    "minimum_package": 650000.0,
    "number_of_openings": 10,
    "posting_date": "2026-10-01"
  },
  "message": "Job vacancy created successfully.",
  "success": true
}
```

---

### 3.5 Application Module (`/api/applications`)

Connects eligible students with active job postings.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/applications` | List applications (with student & company details) |
| `GET` | `/api/applications/<id>` | Get application by ID |
| `POST` | `/api/applications` | Submit application |
| `PUT` | `/api/applications/<id>` | Update application status |
| `DELETE` | `/api/applications/<id>` | Delete application |

#### Business Rules & Validations:
1. **Student Eligibility**:
   - `student.cgpa >= job.minimum_cgpa`: Ineligible students are rejected with `400 Bad Request`.
   - `student.active_backlogs <= job.maximum_backlogs`: Excess backlogs rejected with `400 Bad Request`.
2. **Vacancy Status**:
   - Job must have `job_status == 'Open'`. Applications for Closed/On Hold jobs are rejected with `400 Bad Request`.
3. **Application Deadline**:
   - Current date must not exceed `job.application_deadline`. Expired deadlines are rejected with `400 Bad Request`.
4. **Duplicate Prevention**:
   - A student can only apply once to a given job vacancy (`UNIQUE(student_id, job_id)`). Reapplying returns `409 Conflict`.
5. **Allowed Statuses**:
   - `['Applied', 'Under Review', 'Shortlisted', 'Rejected', 'Selected', 'Withdrawn']`.

#### Create Application
- **POST** `/api/applications`
- **Request Body**:
```json
{
  "student_id": 1,
  "job_id": 1
}
```
- **Response `201 Created`**:
```json
{
  "data": {
    "application_date": "2026-10-31T18:15:25",
    "application_id": 1,
    "application_status": "Applied",
    "job_id": 1,
    "job_title": "Associate Software Engineer",
    "roll_number": "2026CS101",
    "student_id": 1,
    "student_name": "John Doe"
  },
  "message": "Application submitted successfully.",
  "success": true
}
```

#### Update Application Status
- **PUT** `/api/applications/1`
- **Request Body**:
```json
{
  "application_status": "Selected"
}
```
- **Response `200 OK`**:
```json
{
  "data": {
    "application_date": "2026-10-31T18:15:25",
    "application_id": 1,
    "application_status": "Selected",
    "job_id": 1,
    "job_title": "Associate Software Engineer",
    "roll_number": "2026CS101",
    "student_id": 1,
    "student_name": "John Doe"
  },
  "message": "Application updated successfully.",
  "success": true
}
```

---

### 3.6 Interview Module (`/api/interviews`)

Manages rounds, evaluation modes, schedules, and interview performance feedback.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/interviews` | List all scheduled interviews |
| `GET` | `/api/interviews/<id>` | Get interview by ID |
| `POST` | `/api/interviews` | Schedule interview round |
| `PUT` | `/api/interviews/<id>` | Update interview round or result |
| `DELETE` | `/api/interviews/<id>` | Delete interview round |

#### Business Rules & Validations:
- `round_number`: Positive integer (`> 0`).
- `UNIQUE(application_id, round_number)`: Each round number for a given application must be unique. Duplicate round returns `409 Conflict`.
- `interview_mode`: Must be in `['Online', 'Offline', 'Hybrid']`.
- `interview_result`: Must be in `['Pending', 'Cleared', 'Rejected', 'No Show']`. Default: `'Pending'`.

#### Schedule Interview
- **POST** `/api/interviews`
- **Request Body**:
```json
{
  "application_id": 1,
  "round_number": 1,
  "interview_date": "2026-11-10 10:30:00",
  "interview_mode": "Online",
  "interview_result": "Cleared",
  "feedback": "Strong problem-solving and algorithms knowledge."
}
```
- **Response `201 Created`**:
```json
{
  "data": {
    "application_id": 1,
    "feedback": "Strong problem-solving and algorithms knowledge.",
    "interview_date": "2026-11-10T10:30:00",
    "interview_id": 1,
    "interview_mode": "Online",
    "interview_result": "Cleared",
    "job_title": "Associate Software Engineer",
    "round_number": 1,
    "student_name": "John Doe"
  },
  "message": "Interview scheduled successfully.",
  "success": true
}
```

---

### 3.7 Offer Module (`/api/offers`)

Maintains placement job offers, CTC compensation packages, and acceptance statuses.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/offers` | List all job offers |
| `GET` | `/api/offers/<id>` | Get offer by ID |
| `POST` | `/api/offers` | Issue job offer |
| `PUT` | `/api/offers/<id>` | Update offer status or joining date |
| `DELETE` | `/api/offers/<id>` | Delete offer |

#### Business Rules & Validations:
1. **Selection Precondition**:
   - An offer can **only** be issued if `application.application_status == 'Selected'`. Non-selected applications are rejected with `400 Bad Request`.
2. **CTC Positive**:
   - `offered_ctc > 0`. Zero or negative CTC returns `400 Bad Request`.
3. **Date Consistency**:
   - `joining_date >= offer_date`. Earlier joining date returns `400 Bad Request`.
4. **Single Offer per Application**:
   - `UNIQUE(application_id)`. Multiple offers for the same application return `409 Conflict`.
5. **Allowed Statuses**:
   - `['Pending', 'Accepted', 'Declined', 'Expired']`. Default: `'Pending'`.

#### Issue Offer
- **POST** `/api/offers`
- **Request Body**:
```json
{
  "application_id": 1,
  "offered_ctc": 800000.00,
  "offer_date": "2026-11-15",
  "joining_date": "2027-01-10",
  "offer_status": "Pending"
}
```
- **Response `201 Created`**:
```json
{
  "data": {
    "application_id": 1,
    "company_name": "Infosys Technologies",
    "job_title": "Associate Software Engineer",
    "joining_date": "2027-01-10",
    "offer_date": "2026-11-15",
    "offer_id": 1,
    "offer_status": "Pending",
    "offered_ctc": 800000.0,
    "student_name": "John Doe"
  },
  "message": "Offer issued successfully.",
  "success": true
}
```

---

### 3.8 Database Design & Metadata Module (`/api/database`)

Provides live schema introspection from MySQL `INFORMATION_SCHEMA` and academic DBMS 3NF normalization analysis.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/database/metadata` | Live metadata for all 10 tables: columns, types, nullability, PK, FK, and check constraints |
| `GET` | `/api/database/normalization` | Academic 1NF, 2NF, 3NF functional dependencies and decomposition analysis |

#### Get Live Database Metadata
- **GET** `/api/database/metadata`
- **Response `200 OK`**:
```json
{
  "data": {
    "student": {
      "table_name": "student",
      "row_count": 1,
      "columns": [...],
      "primary_key": ["student_id"],
      "foreign_keys": [...],
      "check_constraints": [...]
    },
    "student_phone": {
      "table_name": "student_phone",
      "row_count": 1,
      "primary_key": ["student_id", "phone_number"],
      "is_composite_pk": true,
      ...
    }
  },
  "success": true
}
```

---

## 4. How to Test the APIs

### 4.1 Running Automated Unit Tests
To run all 47 unit and validation tests:
```powershell
py -m unittest discover tests -v
```

### 4.2 Starting the Flask Backend Server
To start the Flask development server:
```powershell
py app.py
```
The server will run on: `http://127.0.0.1:5000`

---

## 5. Sample PowerShell Commands for Manual CRUD Testing

Use the PowerShell commands below to test all operations from your terminal:

```powershell
# Set Base URL variable
$BASE = "http://127.0.0.1:5000"

# 1. Health Check
Invoke-RestMethod -Uri "$BASE/api/health" -Method GET

# 2. CREATE Department
$dept = Invoke-RestMethod -Uri "$BASE/api/departments" -Method POST -ContentType "application/json" -Body (@{
    department_code = "CSE"
    department_name = "Computer Science & Engineering"
} | ConvertTo-Json)
$deptId = $dept.data.department_id
Write-Host "Created Department ID: $deptId"

# 3. GET All Departments
Invoke-RestMethod -Uri "$BASE/api/departments" -Method GET

# 4. GET Department By ID
Invoke-RestMethod -Uri "$BASE/api/departments/$deptId" -Method GET

# 5. CREATE Company
$company = Invoke-RestMethod -Uri "$BASE/api/companies" -Method POST -ContentType "application/json" -Body (@{
    company_name = "Tech Solutions Ltd"
    industry = "IT Services"
    website = "https://techsolutions.io"
    hr_contact_name = "Alice Johnson"
    hr_email = "alice@techsolutions.io"
    hr_phone = "9876543210"
    company_address = "Cyber City, Hyderabad"
} | ConvertTo-Json)
$companyId = $company.data.company_id
Write-Host "Created Company ID: $companyId"

# 6. CREATE Student
$student = Invoke-RestMethod -Uri "$BASE/api/students" -Method POST -ContentType "application/json" -Body (@{
    roll_number = "2026CSE001"
    student_name = "Rohan Sharma"
    email = "rohan.sharma@college.edu"
    phone = "9123456780"
    date_of_birth = "2003-08-12"
    batch_year = 2026
    cgpa = 8.85
    active_backlogs = 0
    department_id = $deptId
} | ConvertTo-Json)
$studentId = $student.data.student_id
Write-Host "Created Student ID: $studentId"

# 7. CREATE Job Posting
$job = Invoke-RestMethod -Uri "$BASE/api/jobs" -Method POST -ContentType "application/json" -Body (@{
    company_id = $companyId
    job_title = "Backend Developer"
    job_description = "Develop microservices with Flask and MySQL"
    job_type = "Full-time"
    job_location = "Hyderabad"
    minimum_cgpa = 7.50
    maximum_backlogs = 0
    minimum_package = 700000.00
    maximum_package = 1000000.00
    number_of_openings = 5
    posting_date = "2026-10-01"
    application_deadline = "2026-12-31"
    job_status = "Open"
} | ConvertTo-Json)
$jobId = $job.data.job_id
Write-Host "Created Job ID: $jobId"

# 8. SUBMIT Application (Student applies for Job)
$appRecord = Invoke-RestMethod -Uri "$BASE/api/applications" -Method POST -ContentType "application/json" -Body (@{
    student_id = $studentId
    job_id = $jobId
} | ConvertTo-Json)
$appId = $appRecord.data.application_id
Write-Host "Created Application ID: $appId"

# 9. UPDATE Application Status to 'Selected'
Invoke-RestMethod -Uri "$BASE/api/applications/$appId" -Method PUT -ContentType "application/json" -Body (@{
    application_status = "Selected"
} | ConvertTo-Json)

# 10. SCHEDULE Interview
$interview = Invoke-RestMethod -Uri "$BASE/api/interviews" -Method POST -ContentType "application/json" -Body (@{
    application_id = $appId
    round_number = 1
    interview_date = "2026-11-15 11:00:00"
    interview_mode = "Online"
    interview_result = "Cleared"
    feedback = "Demonstrated deep database indexing knowledge"
} | ConvertTo-Json)
$interviewId = $interview.data.interview_id
Write-Host "Created Interview ID: $interviewId"

# 11. ISSUE Job Offer
$offer = Invoke-RestMethod -Uri "$BASE/api/offers" -Method POST -ContentType "application/json" -Body (@{
    application_id = $appId
    offered_ctc = 950000.00
    offer_date = "2026-11-20"
    joining_date = "2027-01-15"
    offer_status = "Pending"
} | ConvertTo-Json)
$offerId = $offer.data.offer_id
Write-Host "Created Offer ID: $offerId"

# 12. UPDATE Offer Status (Student Accepts)
Invoke-RestMethod -Uri "$BASE/api/offers/$offerId" -Method PUT -ContentType "application/json" -Body (@{
    offer_status = "Accepted"
} | ConvertTo-Json)

# 13. TEST Foreign-Key Deletion Restriction (Expect 409 Conflict)
try {
    Invoke-RestMethod -Uri "$BASE/api/departments/$deptId" -Method DELETE
} catch {
    Write-Host "Expected Deletion Error: $($_.Exception.Message)"
}

# 14. CLEANUP Deletions in Reverse Order
Invoke-RestMethod -Uri "$BASE/api/offers/$offerId" -Method DELETE
Invoke-RestMethod -Uri "$BASE/api/interviews/$interviewId" -Method DELETE
Invoke-RestMethod -Uri "$BASE/api/applications/$appId" -Method DELETE
Invoke-RestMethod -Uri "$BASE/api/jobs/$jobId" -Method DELETE
Invoke-RestMethod -Uri "$BASE/api/students/$studentId" -Method DELETE
Invoke-RestMethod -Uri "$BASE/api/companies/$companyId" -Method DELETE
Invoke-RestMethod -Uri "$BASE/api/departments/$deptId" -Method DELETE
Write-Host "Complete cleanup executed successfully."
```

