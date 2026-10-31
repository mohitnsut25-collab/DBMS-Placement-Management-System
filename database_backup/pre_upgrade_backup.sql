-- --------------------------------------------------------
-- Backup of database: placement_recruitment_db
-- Generated at: 2026-10-31T20:36:17.319359
-- --------------------------------------------------------

-- Table structure for table `application`
CREATE TABLE `application` (
  `application_id` int unsigned NOT NULL AUTO_INCREMENT,
  `student_id` int unsigned NOT NULL,
  `job_id` int unsigned NOT NULL,
  `application_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `application_status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Applied',
  PRIMARY KEY (`application_id`),
  UNIQUE KEY `uq_student_job` (`student_id`,`job_id`),
  KEY `fk_application_job` (`job_id`),
  CONSTRAINT `fk_application_job` FOREIGN KEY (`job_id`) REFERENCES `job` (`job_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_application_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_application_status` CHECK ((`application_status` in (_utf8mb4'Applied',_utf8mb4'Under Review',_utf8mb4'Shortlisted',_utf8mb4'Rejected',_utf8mb4'Selected',_utf8mb4'Withdrawn')))
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `application`
INSERT INTO `application` (`application_id`, `student_id`, `job_id`, `application_date`, `application_status`) VALUES (8, 8, 8, '2026-10-31T20:19:30', 'Selected');


-- Table structure for table `company`
CREATE TABLE `company` (
  `company_id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `industry` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `website` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hr_contact_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hr_email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hr_phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company_address` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`company_id`),
  UNIQUE KEY `uq_company_name` (`company_name`),
  UNIQUE KEY `uq_company_website` (`website`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `company`
INSERT INTO `company` (`company_id`, `company_name`, `industry`, `website`, `hr_contact_name`, `hr_email`, `hr_phone`, `company_address`) VALUES (8, 'google', 'it', 'https://poki.com/', 'priya sharma', 'hrgoogle@gmail.com', '98219873', 'new delhi');


-- Table structure for table `department`
CREATE TABLE `department` (
  `department_id` int unsigned NOT NULL AUTO_INCREMENT,
  `department_code` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`department_id`),
  UNIQUE KEY `uq_department_code` (`department_code`),
  UNIQUE KEY `uq_department_name` (`department_name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `department`
INSERT INTO `department` (`department_id`, `department_code`, `department_name`) VALUES (8, 'COCSE1240', 'computer science depatyment');


-- Table structure for table `interview`
CREATE TABLE `interview` (
  `interview_id` int unsigned NOT NULL AUTO_INCREMENT,
  `application_id` int unsigned NOT NULL,
  `round_number` int NOT NULL,
  `interview_date` datetime NOT NULL,
  `interview_mode` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `interview_result` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Pending',
  `feedback` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`interview_id`),
  UNIQUE KEY `uq_application_round` (`application_id`,`round_number`),
  CONSTRAINT `fk_interview_application` FOREIGN KEY (`application_id`) REFERENCES `application` (`application_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_interview_mode` CHECK ((`interview_mode` in (_utf8mb4'Online',_utf8mb4'Offline',_utf8mb4'Hybrid'))),
  CONSTRAINT `chk_interview_result` CHECK ((`interview_result` in (_utf8mb4'Pending',_utf8mb4'Cleared',_utf8mb4'Rejected',_utf8mb4'No Show'))),
  CONSTRAINT `chk_interview_round` CHECK ((`round_number` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `job`
CREATE TABLE `job` (
  `job_id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `job_title` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `job_description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `job_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `job_location` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `minimum_cgpa` decimal(4,2) NOT NULL,
  `maximum_backlogs` int NOT NULL DEFAULT '0',
  `minimum_package` decimal(10,2) NOT NULL,
  `maximum_package` decimal(10,2) NOT NULL,
  `number_of_openings` int NOT NULL,
  `posting_date` date NOT NULL,
  `application_deadline` date NOT NULL,
  `job_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Open',
  PRIMARY KEY (`job_id`),
  KEY `fk_job_company` (`company_id`),
  CONSTRAINT `fk_job_company` FOREIGN KEY (`company_id`) REFERENCES `company` (`company_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_job_backlogs` CHECK ((`maximum_backlogs` >= 0)),
  CONSTRAINT `chk_job_cgpa` CHECK ((`minimum_cgpa` between 0 and 10)),
  CONSTRAINT `chk_job_dates` CHECK ((`application_deadline` >= `posting_date`)),
  CONSTRAINT `chk_job_max_package` CHECK ((`maximum_package` >= `minimum_package`)),
  CONSTRAINT `chk_job_min_package` CHECK ((`minimum_package` >= 0)),
  CONSTRAINT `chk_job_openings` CHECK ((`number_of_openings` > 0)),
  CONSTRAINT `chk_job_status` CHECK ((`job_status` in (_utf8mb4'Open',_utf8mb4'Closed',_utf8mb4'On Hold',_utf8mb4'Cancelled'))),
  CONSTRAINT `chk_job_type` CHECK ((`job_type` in (_utf8mb4'Full-time',_utf8mb4'Internship',_utf8mb4'Contract')))
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `job`
INSERT INTO `job` (`job_id`, `company_id`, `job_title`, `job_description`, `job_type`, `job_location`, `minimum_cgpa`, `maximum_backlogs`, `minimum_package`, `maximum_package`, `number_of_openings`, `posting_date`, `application_deadline`, `job_status`) VALUES (8, 8, 'software engineers', 'help', 'Internship', 'delhi', 7.00, 0, 600000.00, 10000000.00, 20, '2026-11-12', '2026-12-15', 'Open');


-- Table structure for table `offer`
CREATE TABLE `offer` (
  `offer_id` int unsigned NOT NULL AUTO_INCREMENT,
  `application_id` int unsigned NOT NULL,
  `offered_ctc` decimal(10,2) NOT NULL,
  `offer_date` date NOT NULL,
  `joining_date` date NOT NULL,
  `offer_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (`offer_id`),
  UNIQUE KEY `uq_offer_application` (`application_id`),
  CONSTRAINT `fk_offer_application` FOREIGN KEY (`application_id`) REFERENCES `application` (`application_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_offer_ctc` CHECK ((`offered_ctc` > 0)),
  CONSTRAINT `chk_offer_dates` CHECK ((`joining_date` >= `offer_date`)),
  CONSTRAINT `chk_offer_status` CHECK ((`offer_status` in (_utf8mb4'Pending',_utf8mb4'Accepted',_utf8mb4'Declined',_utf8mb4'Expired')))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `student`
CREATE TABLE `student` (
  `student_id` int unsigned NOT NULL AUTO_INCREMENT,
  `roll_number` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `student_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_of_birth` date NOT NULL,
  `batch_year` smallint unsigned NOT NULL,
  `cgpa` decimal(4,2) NOT NULL,
  `active_backlogs` int NOT NULL DEFAULT '0',
  `department_id` int unsigned NOT NULL,
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `uq_student_roll` (`roll_number`),
  UNIQUE KEY `uq_student_email` (`email`),
  KEY `fk_student_department` (`department_id`),
  CONSTRAINT `fk_student_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`department_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_student_backlogs` CHECK ((`active_backlogs` >= 0)),
  CONSTRAINT `chk_student_cgpa` CHECK ((`cgpa` between 0 and 10))
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `student`
INSERT INTO `student` (`student_id`, `roll_number`, `student_name`, `email`, `phone`, `date_of_birth`, `batch_year`, `cgpa`, `active_backlogs`, `department_id`) VALUES (8, 'ERRW324', 'wer345', 'afinwef@gmail.com', '987438544', '2006-02-10', 2029, 8.50, 0, 8);

