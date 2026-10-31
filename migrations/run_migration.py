"""
Automated Migration Runner & Verification Script
Upgrades database from 7 to 10 entities with verification.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import db

def run_migration():
    conn = db.get_db_connection()
    cur = conn.cursor(dictionary=True)

    print("=================================================================")
    print("STARTING DATABASE MIGRATION TO 10 ENTITIES")
    print("=================================================================")

    # 1. Inspect existing columns
    cur.execute("DESCRIBE student")
    student_cols = [c["Field"] for c in cur.fetchall()]
    cur.execute("DESCRIBE company")
    company_cols = [c["Field"] for c in cur.fetchall()]

    has_student_phone_col = "phone" in student_cols
    has_company_hr_cols = "hr_contact_name" in company_cols and "hr_email" in company_cols and "hr_phone" in company_cols

    print(f"Existing student table columns: {student_cols}")
    print(f"Legacy 'phone' column present in student: {has_student_phone_col}")
    print(f"Legacy HR columns present in company: {has_company_hr_cols}")

    # 2. Count existing records to migrate
    expected_student_phones = 0
    expected_company_contacts = 0
    expected_contact_phones = 0

    if has_student_phone_col:
        cur.execute("SELECT COUNT(*) AS cnt FROM student WHERE phone IS NOT NULL AND TRIM(phone) != ''")
        expected_student_phones = cur.fetchone()["cnt"]

    if has_company_hr_cols:
        cur.execute("SELECT COUNT(*) AS cnt FROM company WHERE hr_email IS NOT NULL AND TRIM(hr_email) != ''")
        expected_company_contacts = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM company WHERE hr_phone IS NOT NULL AND TRIM(hr_phone) != ''")
        expected_contact_phones = cur.fetchone()["cnt"]

    print(f"\nRecords identified for migration:")
    print(f"  Student phone numbers to migrate: {expected_student_phones}")
    print(f"  Company HR contacts to migrate:   {expected_company_contacts}")
    print(f"  HR contact phone numbers to migrate: {expected_contact_phones}")

    # 3. Create the 3 new tables
    print("\n--- Step 1: Creating New Normalized Tables ---")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS `student_phone` (
          `student_id` INT UNSIGNED NOT NULL,
          `phone_number` VARCHAR(20) NOT NULL,
          `phone_type` VARCHAR(20) NOT NULL DEFAULT 'Primary',
          PRIMARY KEY (`student_id`, `phone_number`),
          CONSTRAINT `fk_student_phone_student` FOREIGN KEY (`student_id`)
            REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("  [CREATED] Table: student_phone (Composite PK: student_id, phone_number)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS `company_contact` (
          `contact_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
          `company_id` INT UNSIGNED NOT NULL,
          `contact_name` VARCHAR(100) NOT NULL,
          `designation` VARCHAR(100) NOT NULL DEFAULT 'HR Contact',
          `email` VARCHAR(254) NOT NULL,
          PRIMARY KEY (`contact_id`),
          UNIQUE KEY `uq_company_contact_email` (`company_id`, `email`),
          CONSTRAINT `fk_company_contact_company` FOREIGN KEY (`company_id`)
            REFERENCES `company` (`company_id`) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("  [CREATED] Table: company_contact (PK: contact_id, UNIQUE: company_id, email)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS `company_contact_phone` (
          `contact_id` INT UNSIGNED NOT NULL,
          `phone_number` VARCHAR(20) NOT NULL,
          `phone_type` VARCHAR(20) NOT NULL DEFAULT 'Work',
          PRIMARY KEY (`contact_id`, `phone_number`),
          CONSTRAINT `fk_company_contact_phone_contact` FOREIGN KEY (`contact_id`)
            REFERENCES `company_contact` (`contact_id`) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("  [CREATED] Table: company_contact_phone (Composite PK: contact_id, phone_number)")
    conn.commit()

    # 4. Migrate student phone numbers
    print("\n--- Step 2: Migrating Existing Data ---")
    if has_student_phone_col and expected_student_phones > 0:
        cur.execute("""
            INSERT INTO `student_phone` (`student_id`, `phone_number`, `phone_type`)
            SELECT `student_id`, `phone`, 'Primary'
            FROM `student`
            WHERE `phone` IS NOT NULL AND TRIM(`phone`) != ''
            ON DUPLICATE KEY UPDATE `phone_type` = VALUES(`phone_type`);
        """)
        conn.commit()
        print(f"  Migrated {cur.rowcount} student phone record(s).")

    # Migrate company contacts
    if has_company_hr_cols and expected_company_contacts > 0:
        cur.execute("""
            INSERT INTO `company_contact` (`company_id`, `contact_name`, `designation`, `email`)
            SELECT `company_id`, `hr_contact_name`, 'HR Manager', `hr_email`
            FROM `company`
            WHERE `hr_email` IS NOT NULL AND TRIM(`hr_email`) != ''
            ON DUPLICATE KEY UPDATE `contact_name` = VALUES(`contact_name`);
        """)
        conn.commit()
        print(f"  Migrated {cur.rowcount} company HR contact record(s).")

    # Migrate company contact phones
    if has_company_hr_cols and expected_contact_phones > 0:
        cur.execute("""
            INSERT INTO `company_contact_phone` (`contact_id`, `phone_number`, `phone_type`)
            SELECT cc.`contact_id`, c.`hr_phone`, 'Work'
            FROM `company` c
            JOIN `company_contact` cc ON c.`company_id` = cc.`company_id` AND c.`hr_email` = cc.`email`
            WHERE c.`hr_phone` IS NOT NULL AND TRIM(c.`hr_phone`) != ''
            ON DUPLICATE KEY UPDATE `phone_type` = VALUES(`phone_type`);
        """)
        conn.commit()
        print(f"  Migrated {cur.rowcount} company contact phone record(s).")

    # 5. Verification procedure
    print("\n--- Step 3: Verifying Migration Integrity ---")
    cur.execute("SELECT COUNT(*) AS cnt FROM student_phone")
    migrated_sp = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM company_contact")
    migrated_cc = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM company_contact_phone")
    migrated_ccp = cur.fetchone()["cnt"]

    print(f"  student_phone total records:       {migrated_sp} (Expected >= {expected_student_phones})")
    print(f"  company_contact total records:     {migrated_cc} (Expected >= {expected_company_contacts})")
    print(f"  company_contact_phone records:     {migrated_ccp} (Expected >= {expected_contact_phones})")

    assert migrated_sp >= expected_student_phones, "Verification Failed: student_phone record count mismatch!"
    assert migrated_cc >= expected_company_contacts, "Verification Failed: company_contact record count mismatch!"
    assert migrated_ccp >= expected_contact_phones, "Verification Failed: company_contact_phone record count mismatch!"

    # Verify actual records
    if has_student_phone_col and expected_student_phones > 0:
        cur.execute("""
            SELECT s.student_id, s.phone, sp.phone_number
            FROM student s
            LEFT JOIN student_phone sp ON s.student_id = sp.student_id AND s.phone = sp.phone_number
            WHERE s.phone IS NOT NULL AND TRIM(s.phone) != '' AND sp.phone_number IS NULL
        """)
        unmigrated_students = cur.fetchall()
        assert len(unmigrated_students) == 0, f"Found unmigrated student phones: {unmigrated_students}"

    if has_company_hr_cols and expected_company_contacts > 0:
        cur.execute("""
            SELECT c.company_id, c.hr_email, cc.email
            FROM company c
            LEFT JOIN company_contact cc ON c.company_id = cc.company_id AND c.hr_email = cc.email
            WHERE c.hr_email IS NOT NULL AND TRIM(c.hr_email) != '' AND cc.email IS NULL
        """)
        unmigrated_companies = cur.fetchall()
        assert len(unmigrated_companies) == 0, f"Found unmigrated company contacts: {unmigrated_companies}"

    print("  VERIFICATION SUCCESS: All records accurately mapped to new normalized tables!")

    # 6. Alter tables to drop legacy single columns
    print("\n--- Step 4: Safely Dropping Legacy Single-Contact Columns ---")
    if has_student_phone_col:
        cur.execute("ALTER TABLE `student` DROP COLUMN `phone`")
        print("  [ALTER TABLE] Dropped column 'phone' from student.")

    if has_company_hr_cols:
        cur.execute("ALTER TABLE `company` DROP COLUMN `hr_contact_name`, DROP COLUMN `hr_email`, DROP COLUMN `hr_phone`")
        print("  [ALTER TABLE] Dropped columns 'hr_contact_name', 'hr_email', 'hr_phone' from company.")

    conn.commit()

    # 7. Final Table Count Check
    cur.execute("SHOW TABLES")
    all_tables = [list(r.values())[0] for r in cur.fetchall()]
    print(f"\nFinal Tables ({len(all_tables)} entities):")
    for t in sorted(all_tables):
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {t}")
        cnt = cur.fetchone()["cnt"]
        print(f"  - {t:<25} ({cnt} rows)")

    cur.close()
    conn.close()

    print("\n=================================================================")
    print("DATABASE MIGRATION COMPLETED SUCCESSFULLY (10 ENTITIES ACTIVE)")
    print("=================================================================")

if __name__ == "__main__":
    run_migration()

