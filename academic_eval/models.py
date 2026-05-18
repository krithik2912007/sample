"""
Database Models — Academic Performance Evaluation System
"""

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('admin', 'mentor', 'student'), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('Student', foreign_keys='Student.user_id', back_populates='user', uselist=False)
    mentor_profile = db.relationship('Mentor', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)

    subjects = db.relationship('Subject', back_populates='department')
    students = db.relationship('Student', back_populates='department')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'code': self.code}


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    reg_no = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    current_semester = db.Column(db.Integer, default=1)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    scholars_eligible = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='student_profile')
    department = db.relationship('Department', back_populates='students')
    mentor = db.relationship('User', foreign_keys=[mentor_id])
    marks = db.relationship('Mark', back_populates='student')
    semester_gpas = db.relationship('SemesterGPA', back_populates='student')
    cgpa_record = db.relationship('CGPARecord', back_populates='student', uselist=False)
    arrears = db.relationship('ArrearHistory', back_populates='student')
    badges = db.relationship('StudentBadge', back_populates='student')
    mentor_notes = db.relationship('MentorNote', back_populates='student')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.name if self.user else '',
            'email': self.user.email if self.user else '',
            'reg_no': self.reg_no,
            'department': self.department.to_dict() if self.department else None,
            'batch_year': self.batch_year,
            'current_semester': self.current_semester,
            'mentor_id': self.mentor_id,
            'mentor_name': self.mentor.name if self.mentor else None,
            'scholars_eligible': self.scholars_eligible,
            'cgpa': self.cgpa_record.overall_cgpa if self.cgpa_record else 0.00
        }


class Mentor(db.Model):
    __tablename__ = 'mentors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)

    user = db.relationship('User', back_populates='mentor_profile')
    department = db.relationship('Department')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.name if self.user else '',
            'email': self.user.email if self.user else '',
            'employee_id': self.employee_id,
            'department': self.department.to_dict() if self.department else None
        }


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    subject_type = db.Column(db.Enum('theory', 'lot', 'lab', 'soft_skills', 'project', 'internship', 'non_credit'), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=0)
    l_hours = db.Column(db.Integer, default=0)
    t_hours = db.Column(db.Integer, default=0)
    p_hours = db.Column(db.Integer, default=0)
    is_elective = db.Column(db.Boolean, default=False)
    elective_group = db.Column(db.String(50), nullable=True)
    lot_model_max = db.Column(db.Integer, default=25)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', back_populates='subjects')
    marks = db.relationship('Mark', back_populates='subject')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'semester': self.semester,
            'subject_type': self.subject_type,
            'credits': self.credits,
            'l_hours': self.l_hours,
            't_hours': self.t_hours,
            'p_hours': self.p_hours,
            'is_elective': self.is_elective,
            'elective_group': self.elective_group,
            'lot_model_max': self.lot_model_max
        }


class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)

    # Theory
    cat1 = db.Column(db.Numeric(5, 2), nullable=True)
    cat2 = db.Column(db.Numeric(5, 2), nullable=True)
    quiz = db.Column(db.Numeric(5, 2), nullable=True)
    end_sem_theory = db.Column(db.Numeric(5, 2), nullable=True)

    # Practical
    model_lab = db.Column(db.Numeric(5, 2), nullable=True)
    model_max = db.Column(db.Integer, default=25)
    end_sem_practical = db.Column(db.Numeric(5, 2), nullable=True)

    # Soft Skills
    ss_cat1 = db.Column(db.Numeric(5, 2), nullable=True)
    ss_cat2 = db.Column(db.Numeric(5, 2), nullable=True)
    ss_cat3 = db.Column(db.Numeric(5, 2), nullable=True)

    # Computed
    internal_marks = db.Column(db.Numeric(5, 2), nullable=True)
    total_marks = db.Column(db.Numeric(5, 2), nullable=True)
    grade = db.Column(db.String(3), nullable=True)
    grade_point = db.Column(db.Numeric(4, 2), nullable=True)

    pass_fail = db.Column(db.Enum('pass', 'fail', 'pending'), default='pending')
    is_arrear = db.Column(db.Boolean, default=False)
    arrear_cleared = db.Column(db.Boolean, default=False)
    arrear_cleared_date = db.Column(db.Date, nullable=True)

    entry_mode = db.Column(db.Enum('academic', 'simulation'), default='academic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('Student', back_populates='marks')
    subject = db.relationship('Subject', back_populates='marks')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else '',
            'subject_code': self.subject.code if self.subject else '',
            'subject_type': self.subject.subject_type if self.subject else '',
            'semester': self.semester,
            'academic_year': self.academic_year,
            'cat1': float(self.cat1) if self.cat1 else None,
            'cat2': float(self.cat2) if self.cat2 else None,
            'quiz': float(self.quiz) if self.quiz else None,
            'end_sem_theory': float(self.end_sem_theory) if self.end_sem_theory else None,
            'model_lab': float(self.model_lab) if self.model_lab else None,
            'model_max': self.model_max,
            'end_sem_practical': float(self.end_sem_practical) if self.end_sem_practical else None,
            'ss_cat1': float(self.ss_cat1) if self.ss_cat1 else None,
            'ss_cat2': float(self.ss_cat2) if self.ss_cat2 else None,
            'ss_cat3': float(self.ss_cat3) if self.ss_cat3 else None,
            'internal_marks': float(self.internal_marks) if self.internal_marks else None,
            'total_marks': float(self.total_marks) if self.total_marks else None,
            'grade': self.grade,
            'grade_point': float(self.grade_point) if self.grade_point else None,
            'pass_fail': self.pass_fail,
            'is_arrear': self.is_arrear,
            'entry_mode': self.entry_mode
        }


class SemesterGPA(db.Model):
    __tablename__ = 'semester_gpa'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    gpa = db.Column(db.Numeric(4, 2), nullable=False)
    total_credits = db.Column(db.Integer, nullable=False)
    earned_credits = db.Column(db.Integer, nullable=False)
    subjects_passed = db.Column(db.Integer, nullable=False)
    subjects_failed = db.Column(db.Integer, nullable=False)
    non_credit_failed = db.Column(db.Integer, default=0)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='semester_gpas')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'semester': self.semester,
            'academic_year': self.academic_year,
            'gpa': float(self.gpa),
            'total_credits': self.total_credits,
            'earned_credits': self.earned_credits,
            'subjects_passed': self.subjects_passed,
            'subjects_failed': self.subjects_failed,
            'non_credit_failed': self.non_credit_failed
        }


class CGPARecord(db.Model):
    __tablename__ = 'cgpa_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    overall_cgpa = db.Column(db.Numeric(4, 2), nullable=False, default=0.00)
    total_credits_completed = db.Column(db.Integer, default=0)
    total_credits_required = db.Column(db.Integer, default=160)
    standing_arrears = db.Column(db.Integer, default=0)
    total_arrears_ever = db.Column(db.Integer, default=0)
    scholars_eligible = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('Student', back_populates='cgpa_record')

    def to_dict(self):
        return {
            'overall_cgpa': float(self.overall_cgpa),
            'total_credits_completed': self.total_credits_completed,
            'total_credits_required': self.total_credits_required,
            'standing_arrears': self.standing_arrears,
            'total_arrears_ever': self.total_arrears_ever,
            'scholars_eligible': self.scholars_eligible,
            'completion_percentage': round((self.total_credits_completed / self.total_credits_required) * 100, 1) if self.total_credits_required else 0
        }


class ArrearHistory(db.Model):
    __tablename__ = 'arrear_history'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    grade_obtained = db.Column(db.String(3), nullable=True)
    cleared = db.Column(db.Boolean, default=False)
    cleared_in_year = db.Column(db.String(10), nullable=True)
    cleared_grade = db.Column(db.String(3), nullable=True)

    student = db.relationship('Student', back_populates='arrears')
    subject = db.relationship('Subject')

    def to_dict(self):
        return {
            'id': self.id,
            'subject_name': self.subject.name if self.subject else '',
            'subject_code': self.subject.code if self.subject else '',
            'semester': self.semester,
            'academic_year': self.academic_year,
            'grade_obtained': self.grade_obtained,
            'cleared': self.cleared,
            'cleared_in_year': self.cleared_in_year,
            'cleared_grade': self.cleared_grade
        }


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    cgpa_at_evaluation = db.Column(db.Numeric(4, 2), nullable=True)
    standing_arrears = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('good_standing', 'academic_warning', 'probation', 'dismissed'), nullable=False)
    scholars_status = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    evaluated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    evaluator = db.relationship('User', foreign_keys=[evaluated_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.name if self.student and self.student.user else '',
            'academic_year': self.academic_year,
            'cgpa_at_evaluation': float(self.cgpa_at_evaluation) if self.cgpa_at_evaluation else None,
            'standing_arrears': self.standing_arrears,
            'status': self.status,
            'scholars_status': self.scholars_status,
            'notes': self.notes,
            'evaluated_at': self.evaluated_at.isoformat()
        }


class EvaluationCriteria(db.Model):
    __tablename__ = 'evaluation_criteria'
    id = db.Column(db.Integer, primary_key=True)
    status_label = db.Column(db.String(50), nullable=False)
    min_cgpa = db.Column(db.Numeric(4, 2), nullable=False)
    max_cgpa = db.Column(db.Numeric(4, 2), nullable=False)
    max_arrears = db.Column(db.Integer, default=0)
    color_code = db.Column(db.String(10), nullable=False)
    action_required = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'status_label': self.status_label,
            'min_cgpa': float(self.min_cgpa),
            'max_cgpa': float(self.max_cgpa),
            'max_arrears': self.max_arrears,
            'color_code': self.color_code,
            'action_required': self.action_required
        }


class MentorNote(db.Model):
    __tablename__ = 'mentor_notes'
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mentor = db.relationship('User', foreign_keys=[mentor_id])
    student = db.relationship('Student', back_populates='mentor_notes')

    def to_dict(self):
        return {
            'id': self.id,
            'mentor_name': self.mentor.name if self.mentor else '',
            'note': self.note,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat()
        }


class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'code': self.code, 'name': self.name,
                'description': self.description, 'icon': self.icon, 'color': self.color}


class StudentBadge(db.Model):
    __tablename__ = 'student_badges'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='badges')
    badge = db.relationship('Badge')

    def to_dict(self):
        return {
            'badge': self.badge.to_dict() if self.badge else None,
            'awarded_at': self.awarded_at.isoformat()
        }


class ParentShareLink(db.Model):
    __tablename__ = 'parent_share_links'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    mentor = db.relationship('User', foreign_keys=[mentor_id])


class LeaderboardPreference(db.Model):
    __tablename__ = 'leaderboard_preferences'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    opt_in = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.String(100), nullable=True)

    student = db.relationship('Student')
