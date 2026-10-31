-- ============================================================================
-- Migration: 001_upgrade_multicontact.sql
-- Purpose: Upgrade Placement & Recruitment System from 7 to 10 entities
--          Normalizing Student and Company contacts to support 1:N phone numbers
--          and multiple HR personnel per company.
-- ============================================================================

-- Step 1: Create student_phone table (Composite PK: student_id, phone_number)
CREATE TABLE IF NOT EXISTS `student_phone` (
  `student_id` INT UNSIGNED NOT NULL,
  `phone_number` VARCHAR(20) NOT NULL,
  `phone_type` VARCHAR(20) NOT NULL DEFAULT 'Primary',
  PRIMARY KEY (`student_id`, `phone_number`),
  CONSTRAINT `fk_student_phone_student` FOREIGN KEY (`student_id`)
    REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 2: Create company_contact table (1:N contacts per company)
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

-- Step 3: Create company_contact_phone table (1:N phone numbers per HR contact)
CREATE TABLE IF NOT EXISTS `company_contact_phone` (
  `contact_id` INT UNSIGNED NOT NULL,
  `phone_number` VARCHAR(20) NOT NULL,
  `phone_type` VARCHAR(20) NOT NULL DEFAULT 'Work',
  PRIMARY KEY (`contact_id`, `phone_number`),
  CONSTRAINT `fk_company_contact_phone_contact` FOREIGN KEY (`contact_id`)
    REFERENCES `company_contact` (`contact_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 4: Data Migration - Copy existing student phone numbers
INSERT INTO `student_phone` (`student_id`, `phone_number`, `phone_type`)
SELECT `student_id`, `phone`, 'Primary'
FROM `student`
WHERE `phone` IS NOT NULL AND TRIM(`phone`) != ''
ON DUPLICATE KEY UPDATE `phone_type` = VALUES(`phone_type`);

-- Step 5: Data Migration - Convert existing company HR details into company_contact
INSERT INTO `company_contact` (`company_id`, `contact_name`, `designation`, `email`)
SELECT `company_id`, `hr_contact_name`, 'HR Manager', `hr_email`
FROM `company`
WHERE `hr_email` IS NOT NULL AND TRIM(`hr_email`) != ''
ON DUPLICATE KEY UPDATE `contact_name` = VALUES(`contact_name`);

-- Step 6: Data Migration - Copy existing company HR phone into company_contact_phone
INSERT INTO `company_contact_phone` (`contact_id`, `phone_number`, `phone_type`)
SELECT cc.`contact_id`, c.`hr_phone`, 'Work'
FROM `company` c
JOIN `company_contact` cc ON c.`company_id` = cc.`company_id` AND c.`hr_email` = cc.`email`
WHERE c.`hr_phone` IS NOT NULL AND TRIM(c.`hr_phone`) != ''
ON DUPLICATE KEY UPDATE `phone_type` = VALUES(`phone_type`);

-- Step 7: Drop deprecated single-phone columns after verification
-- ALTER TABLE `student` DROP COLUMN `phone`;
-- ALTER TABLE `company` DROP COLUMN `hr_contact_name`, DROP COLUMN `hr_email`, DROP COLUMN `hr_phone`;

