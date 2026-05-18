-- ============================================================
-- ACADEMIC PERFORMANCE EVALUATION SYSTEM
-- REC CSE Department | Regulation 2023
-- Database Schema + Seed Data
-- ============================================================

CREATE DATABASE IF NOT EXISTS academic_eval CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE academic_eval;

-- ============================================================
-- USERS TABLE (Admin, Mentor, Student)
-- ============================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role ENUM('admin', 'mentor', 'student') NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================
-- DEPARTMENTS
-- ============================================================
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL
);

-- ============================================================
-- STUDENTS (extends users)
-- ============================================================
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    reg_no VARCHAR(20) UNIQUE NOT NULL,
    department_id INT NOT NULL,
    batch_year INT NOT NULL,        -- e.g. 2023 (year of joining)
    current_semester INT DEFAULT 1,
    mentor_id INT,                  -- FK to users (mentor)
    scholars_eligible BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (mentor_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- MENTORS (extends users)
-- ============================================================
CREATE TABLE mentors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    department_id INT NOT NULL,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- ============================================================
-- SUBJECTS MASTER
-- subject_type: 'theory' | 'lot' | 'lab' | 'soft_skills' | 'project' | 'internship' | 'non_credit'
-- For semesters 7-8, admin can add subjects dynamically
-- ============================================================
CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    department_id INT NOT NULL,
    semester INT NOT NULL,          -- 1 to 8
    subject_type ENUM('theory','lot','lab','soft_skills','project','internship','non_credit') NOT NULL,
    credits INT NOT NULL DEFAULT 0,
    l_hours INT DEFAULT 0,          -- Lecture hours
    t_hours INT DEFAULT 0,          -- Tutorial hours
    p_hours INT DEFAULT 0,          -- Practical hours
    is_elective BOOLEAN DEFAULT FALSE,  -- Professional/Open electives
    elective_group VARCHAR(50),     -- e.g. 'PE-I', 'OE-I', 'PE-III'
    lot_model_max INT DEFAULT 25,   -- For LOT: 25 or 50 (student picks)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- ============================================================
-- STUDENT SUBJECT SELECTION (for electives)
-- ============================================================
CREATE TABLE student_elective_choices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    elective_group VARCHAR(50) NOT NULL,  -- 'PE-I', 'OE-I'
    subject_id INT NOT NULL,
    semester INT NOT NULL,
    UNIQUE KEY unique_elective (student_id, elective_group, semester),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- MARKS TABLE (actual saved academic record)
-- ============================================================
CREATE TABLE marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    semester INT NOT NULL,
    academic_year VARCHAR(10) NOT NULL,  -- e.g. '2023-24'

    -- Theory fields
    cat1 DECIMAL(5,2),              -- out of 75
    cat2 DECIMAL(5,2),              -- out of 75
    quiz DECIMAL(5,2),              -- out of 50
    end_sem_theory DECIMAL(5,2),    -- out of 100

    -- Practical fields (LOT + Lab)
    model_lab DECIMAL(5,2),         -- out of 25 or 50 (LOT), 25 (Lab)
    model_max INT DEFAULT 25,       -- 25 or 50 (student selected for LOT)
    end_sem_practical DECIMAL(5,2), -- out of 100

    -- Soft Skills fields
    ss_cat1 DECIMAL(5,2),           -- out of 100
    ss_cat2 DECIMAL(5,2),           -- out of 100
    ss_cat3 DECIMAL(5,2),           -- out of 100

    -- Computed fields
    internal_marks DECIMAL(5,2),    -- computed internal
    total_marks DECIMAL(5,2),       -- final /100
    grade VARCHAR(3),               -- O, A+, A, B+, B, C+, C, F
    grade_point DECIMAL(4,2),       -- 10, 9, 8, 7, 6, 5, 4, 0

    -- Pass/Fail for non-credit/internship
    pass_fail ENUM('pass','fail','pending') DEFAULT 'pending',

    is_arrear BOOLEAN DEFAULT FALSE,
    arrear_cleared BOOLEAN DEFAULT FALSE,
    arrear_cleared_date DATE,

    entry_mode ENUM('academic','simulation') DEFAULT 'academic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_mark (student_id, subject_id, academic_year, entry_mode),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- SEMESTER GPA RECORDS
-- ============================================================
CREATE TABLE semester_gpa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester INT NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    gpa DECIMAL(4,2) NOT NULL,
    total_credits INT NOT NULL,
    earned_credits INT NOT NULL,    -- Credits where grade >= C
    subjects_passed INT NOT NULL,
    subjects_failed INT NOT NULL,
    non_credit_failed INT DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_sem_gpa (student_id, semester, academic_year),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ============================================================
-- CGPA RECORDS
-- ============================================================
CREATE TABLE cgpa_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT UNIQUE NOT NULL,
    overall_cgpa DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    total_credits_completed INT DEFAULT 0,
    total_credits_required INT DEFAULT 160,
    standing_arrears INT DEFAULT 0,  -- Current uncleared arrears
    total_arrears_ever INT DEFAULT 0,
    scholars_eligible BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ============================================================
-- ARREAR HISTORY
-- ============================================================
CREATE TABLE arrear_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    semester INT NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    grade_obtained VARCHAR(3),
    cleared BOOLEAN DEFAULT FALSE,
    cleared_in_year VARCHAR(10),
    cleared_grade VARCHAR(3),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- ACADEMIC EVALUATION (Annual)
-- ============================================================
CREATE TABLE evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    cgpa_at_evaluation DECIMAL(4,2),
    standing_arrears INT DEFAULT 0,
    status ENUM('good_standing','academic_warning','probation','dismissed') NOT NULL,
    scholars_status BOOLEAN DEFAULT FALSE,
    notes TEXT,
    evaluated_by INT,               -- admin user id
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (evaluated_by) REFERENCES users(id)
);

-- ============================================================
-- EVALUATION CRITERIA (Admin configurable)
-- ============================================================
CREATE TABLE evaluation_criteria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status_label VARCHAR(50) NOT NULL,
    min_cgpa DECIMAL(4,2) NOT NULL,
    max_cgpa DECIMAL(4,2) NOT NULL,
    max_arrears INT DEFAULT 0,
    color_code VARCHAR(10) NOT NULL,  -- hex color
    action_required TEXT,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- ============================================================
-- MENTOR NOTES
-- ============================================================
CREATE TABLE mentor_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mentor_id INT NOT NULL,
    student_id INT NOT NULL,
    note TEXT NOT NULL,
    is_private BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (mentor_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ============================================================
-- BADGES / MILESTONES
-- ============================================================
CREATE TABLE badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),               -- emoji or icon class
    color VARCHAR(10)
);

CREATE TABLE student_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    badge_id INT NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_badge (student_id, badge_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(id)
);

-- ============================================================
-- PARENT SHARE LINKS (one-time, read-only)
-- ============================================================
CREATE TABLE parent_share_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    mentor_id INT NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (mentor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- LEADERBOARD SETTINGS
-- ============================================================
CREATE TABLE leaderboard_preferences (
    student_id INT PRIMARY KEY,
    opt_in BOOLEAN DEFAULT FALSE,
    display_name VARCHAR(100),     -- anonymous alias option
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ============================================================
-- ============================================================
-- SEED DATA
-- ============================================================
-- ============================================================

-- Departments
INSERT INTO departments (name, code) VALUES
('Computer Science and Engineering', 'CSE'),
('Electronics and Communication Engineering', 'ECE'),
('Mechanical Engineering', 'MECH'),
('Civil Engineering', 'CIVIL'),
('Electrical and Electronics Engineering', 'EEE');

-- Default Admin User (password: Admin@123)
INSERT INTO users (name, email, password_hash, role) VALUES
('System Administrator', 'admin@rec.edu', 'pbkdf2:sha256:600000$placeholder_admin_hash', 'admin'),
('Dr. Priya Sharma', 'mentor1@rec.edu', 'pbkdf2:sha256:600000$placeholder_mentor_hash', 'mentor'),
('Dr. Rajesh Kumar', 'mentor2@rec.edu', 'pbkdf2:sha256:600000$placeholder_mentor_hash', 'mentor'),
('Arjun Krishnamurthy', 'student1@rec.edu', 'pbkdf2:sha256:600000$placeholder_student_hash', 'student'),
('Priya Venkatesh', 'student2@rec.edu', 'pbkdf2:sha256:600000$placeholder_student_hash', 'student');

-- Mentors
INSERT INTO mentors (user_id, department_id, employee_id) VALUES
(2, 1, 'EMP001'),
(3, 1, 'EMP002');

-- Students
INSERT INTO students (user_id, reg_no, department_id, batch_year, current_semester, mentor_id) VALUES
(4, '211CS001', 1, 2023, 3, 2),
(5, '211CS002', 1, 2023, 3, 2);

-- CGPA Records init
INSERT INTO cgpa_records (student_id, overall_cgpa, total_credits_completed, standing_arrears) VALUES
(1, 0.00, 0, 0),
(2, 0.00, 0, 0);

-- Evaluation Criteria (default)
INSERT INTO evaluation_criteria (status_label, min_cgpa, max_cgpa, max_arrears, color_code, action_required) VALUES
('Good Standing', 7.00, 10.00, 0, '#22c55e', 'No action required. Student is performing well.'),
('Academic Warning', 5.00, 6.99, 5, '#eab308', 'Notify student and mentor. Schedule counseling session.'),
('Probation', 3.00, 4.99, 10, '#f97316', 'Mark for review. Mandatory mentoring sessions required.'),
('Dismissed from Program', 0.00, 2.99, 99, '#ef4444', 'Flag record. Initiate academic dismissal process.');

-- Badges
INSERT INTO badges (code, name, description, icon, color) VALUES
('first_semester', 'Fresh Start', 'Completed first semester', '🎓', '#6366f1'),
('perfect_gpa', 'Perfect Score', 'Achieved 10.0 GPA in a semester', '⭐', '#f59e0b'),
('scholars_entry', 'Scholars Club', 'Achieved Scholars Program eligibility (CGPA ≥ 8.5)', '🏆', '#10b981'),
('scholars_maintained', 'Scholar Streak', 'Maintained Scholars status for 2+ consecutive semesters', '🔥', '#ef4444'),
('no_arrears', 'Clean Slate', 'Completed a semester with no arrears', '✨', '#06b6d4'),
('improvement', 'Comeback Kid', 'Improved GPA by 1.0+ from previous semester', '📈', '#8b5cf6'),
('all_pass', 'Full Clear', 'Passed all subjects in a semester', '🎯', '#22c55e'),
('cgpa_8', 'Excellence Award', 'Achieved CGPA above 8.0', '🌟', '#f59e0b'),
('cgpa_9', 'Academic Star', 'Achieved CGPA above 9.0', '💫', '#ec4899');

-- ============================================================
-- CSE SUBJECTS — SEMESTER 1
-- ============================================================
INSERT INTO subjects (code, name, department_id, semester, subject_type, credits, l_hours, t_hours, p_hours, is_elective, lot_model_max) VALUES
('HS23111', 'Technical Communication I', 1, 1, 'theory', 2, 2, 0, 0, FALSE, NULL),
('MA23111', 'Linear Algebra and Calculus', 1, 1, 'theory', 4, 3, 1, 0, FALSE, NULL),
('GE23117', 'Heritage of Tamils', 1, 1, 'theory', 1, 1, 0, 0, FALSE, NULL),
('GE23131', 'Programming using C', 1, 1, 'lot', 4, 1, 0, 6, FALSE, 25),
('EE23133', 'Basic Electrical and Electronics Engineering', 1, 1, 'lot', 4, 3, 0, 2, FALSE, 25),
('PH23132', 'Physics for Information Science', 1, 1, 'lot', 4, 3, 0, 2, FALSE, 25),
('GE23121', 'Engineering Practices - Civil and Mechanical', 1, 1, 'lab', 1, 0, 0, 2, FALSE, NULL),
('MC23111', 'Indian Constitution and Freedom Movement', 1, 1, 'non_credit', 0, 3, 0, 0, FALSE, NULL);

-- ============================================================
-- CSE SUBJECTS — SEMESTER 2
-- ============================================================
INSERT INTO subjects (code, name, department_id, semester, subject_type, credits, l_hours, t_hours, p_hours, is_elective, lot_model_max) VALUES
('MA23213', 'Discrete Mathematical Structures', 1, 2, 'theory', 4, 3, 1, 0, FALSE, NULL),
('GE23217', 'Tamils and Technology', 1, 2, 'theory', 1, 1, 0, 0, FALSE, NULL),
('EC23232', 'Digital Logic and Microprocessor', 1, 2, 'lot', 4, 3, 0, 2, FALSE, 25),
('GE23111', 'Engineering Graphics', 1, 2, 'lot', 4, 2, 0, 4, FALSE, 25),
('CS23231', 'Data Structures', 1, 2, 'lot', 5, 3, 0, 4, FALSE, 25),
('HS23221', 'Technical Communication II / English for Professional Competence', 1, 2, 'lab', 1, 0, 0, 2, FALSE, NULL),
('GE23122', 'Engineering Practices - Electrical and Electronics', 1, 2, 'lab', 1, 0, 0, 2, FALSE, NULL),
('CS23221', 'Python Programming Lab', 1, 2, 'lab', 2, 0, 0, 4, FALSE, NULL),
('MC23112', 'Environmental Science and Engineering', 1, 2, 'non_credit', 0, 3, 0, 0, FALSE, NULL);

-- ============================================================
-- CSE SUBJECTS — SEMESTER 3
-- ============================================================
INSERT INTO subjects (code, name, department_id, semester, subject_type, credits, l_hours, t_hours, p_hours, is_elective, lot_model_max) VALUES
('MA23312', 'Fourier Series and Number Theory', 1, 3, 'theory', 4, 3, 1, 0, FALSE, NULL),
('CS23311', 'Computer Architecture', 1, 3, 'theory', 3, 3, 0, 0, FALSE, NULL),
('CS23331', 'Design and Analysis of Algorithms', 1, 3, 'lot', 4, 3, 0, 2, FALSE, 25),
('CS23332', 'Database Management Systems', 1, 3, 'lot', 5, 3, 0, 4, FALSE, 25),
('CS23333', 'Object Oriented Programming Using Java', 1, 3, 'lot', 4, 1, 0, 6, FALSE, 25),
('CS23334', 'Fundamentals of Data Science', 1, 3, 'lot', 4, 3, 0, 2, FALSE, 25);

-- ============================================================
-- CSE SUBJECTS — SEMESTER 4
-- ============================================================
INSERT INTO subjects (code, name, department_id, semester, subject_type, credits, l_hours, t_hours, p_hours, is_elective, elective_group, lot_model_max) VALUES
('OE23411', 'Open Elective - I', 1, 4, 'theory', 3, 3, 0, 0, TRUE, 'OE-I', NULL),
('PE23411', 'Professional Elective - I', 1, 4, 'theory', 3, 3, 0, 0, TRUE, 'PE-I', NULL),
('MA23435', 'Probability, Statistics and Simulation', 1, 4, 'lot', 4, 3, 0, 2, FALSE, NULL, 25),
('CS23431', 'Operating Systems', 1, 4, 'lot', 5, 3, 0, 4, FALSE, NULL, 25),
('CS23432', 'Software Construction', 1, 4, 'lot', 4, 3, 0, 2, FALSE, NULL, 25),
('GE23627', 'Design Thinking and Innovation', 1, 4, 'theory', 3, 3, 0, 0, FALSE, NULL, NULL),
('GE23421', 'Soft Skills - I', 1, 4, 'soft_skills', 1, 0, 0, 2, FALSE, NULL, NULL),
('CS23421', 'Internship (2 weeks)', 1, 4, 'internship', 1, 0, 0, 2, FALSE, NULL, NULL);

-- ============================================================
-- CSE SUBJECTS — SEMESTER 5
-- ============================================================
INSERT INTO subjects (code, name, department_id, semester, subject_type, credits, l_hours, t_hours, p_hours, is_elective, elective_group, lot_model_max) VALUES
('CS23511', 'Theory of Computation', 1, 5, 'theory', 4, 3, 1, 0, FALSE, NULL, NULL),
('CS23512', 'Fundamentals of Mobile Computing', 1, 5, 'theory', 3, 3, 0, 0, FALSE, NULL, NULL),
('PE23511', 'Professional Elective - II', 1, 5, 'theory', 3, 3, 0, 0, TRUE, 'PE-II', NULL),
('CS23531', 'Web Programming', 1, 5, 'lot', 4, 1, 0, 6, FALSE, NULL, 25),
('CS23532', 'Computer Networks', 1, 5, 'lot', 5, 3, 0, 4, FALSE, NULL, 25),
('CS23533', 'Foundations of Artificial Intelligence', 1, 5, 'lot', 4, 3, 0, 2, FALSE, NULL, 25),
('GE23521', 'Soft Skills - II', 1, 5, 'soft_skills', 1, 0, 0, 2, FALSE, NULL, NULL);

-- ============================================================
-- CSE SUBJECTS — SEMESTER 6
-- ============================================================
INSERT INTO subjects (code, name, department_id, semester, subject_type, credits, l_hours, t_hours, p_hours, is_elective, lot_model_max) VALUES
('CS23631', 'Compiler Design', 1, 6, 'lot', 4, 3, 0, 2, FALSE, 25),
('CS23632', 'Cryptography and Network Security', 1, 6, 'lot', 3, 2, 0, 2, FALSE, 25),
('CS23633', 'Cloud Computing', 1, 6, 'lot', 3, 2, 0, 2, FALSE, 25),
('CS23634', 'Fundamentals of Generative AI and Prompt Engineering', 1, 6, 'lot', 3, 2, 0, 2, FALSE, 25),
('AI23331', 'Fundamentals of Machine Learning', 1, 6, 'lot', 4, 3, 0, 2, FALSE, 25),
('CS23621', 'Mobile Application Development Laboratory', 1, 6, 'lab', 2, 0, 0, 4, FALSE, NULL),
('GE23621', 'Problem Solving Techniques', 1, 6, 'soft_skills', 1, 0, 0, 2, FALSE, NULL);
