"""
Marks Routes
Enter marks, auto-calculate grades, save academic records.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import (db, Student, Subject, Mark, SemesterGPA,
                    CGPARecord, ArrearHistory, StudentBadge, Badge)
from utils.calculator import (calculate_marks_for_subject, calculate_gpa,
                               calculate_cgpa, scholars_status,
                               generate_recommendations, cgpa_needed_for_scholars)
from datetime import datetime

marks_bp = Blueprint('marks', __name__)


def get_academic_year(semester: int, batch_year: int) -> str:
    """Derive academic year string from semester and batch year."""
    year_offset = (semester - 1) // 2
    start = batch_year + year_offset
    return f"{start}-{str(start + 1)[-2:]}"


@marks_bp.route('/calculate', methods=['POST'])
def calculate_preview():
    """
    Preview grade calculation without saving.
    Works for both simulator and academic modes.
    """
    data = request.get_json()
    subject_type = data.get('subject_type')
    if not subject_type:
        return jsonify({'error': 'subject_type is required'}), 400

    result = calculate_marks_for_subject(subject_type, data)
    return jsonify(result), 200


@marks_bp.route('/save', methods=['POST'])
@jwt_required()
def save_marks():
    """Save academic marks for a subject (academic mode only)."""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    data = request.get_json()

    # Students save their own marks
    if claims['role'] == 'student':
        student = Student.query.filter_by(user_id=user_id).first()
        if not student:
            return jsonify({'error': 'Student profile not found'}), 404
        student_id = student.id
    elif claims['role'] in ('admin', 'mentor'):
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'error': 'student_id required'}), 400
    else:
        return jsonify({'error': 'Access denied'}), 403

    subject_id = data.get('subject_id')
    if not subject_id:
        return jsonify({'error': 'subject_id required'}), 400

    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404

    student = Student.query.get(student_id)
    academic_year = get_academic_year(subject.semester, student.batch_year)

    # Calculate marks
    calc = calculate_marks_for_subject(subject.subject_type, data)

    # Find or create mark record
    mark = Mark.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        academic_year=academic_year,
        entry_mode='academic'
    ).first()

    if not mark:
        mark = Mark(
            student_id=student_id,
            subject_id=subject_id,
            semester=subject.semester,
            academic_year=academic_year,
            entry_mode='academic'
        )
        db.session.add(mark)

    # Set raw input fields
    mark.cat1 = data.get('cat1')
    mark.cat2 = data.get('cat2')
    mark.quiz = data.get('quiz')
    mark.end_sem_theory = data.get('end_sem_theory')
    mark.model_lab = data.get('model_lab')
    mark.model_max = data.get('model_max', 25)
    mark.end_sem_practical = data.get('end_sem_practical')
    mark.ss_cat1 = data.get('ss_cat1')
    mark.ss_cat2 = data.get('ss_cat2')
    mark.ss_cat3 = data.get('ss_cat3')

    # Set calculated fields
    if subject.subject_type in ('internship', 'non_credit'):
        mark.pass_fail = data.get('pass_fail', 'pending')
        mark.total_marks = 0
        mark.grade = None
        mark.grade_point = 0
    else:
        mark.internal_marks = calc.get('internal')
        mark.total_marks = calc.get('total')
        mark.grade = calc.get('grade')
        mark.grade_point = calc.get('grade_point')

        if mark.grade == 'F':
            mark.pass_fail = 'fail'
            mark.is_arrear = True
        else:
            mark.pass_fail = 'pass'
            mark.is_arrear = False

    db.session.commit()

    # Update arrear history
    _update_arrear_history(student_id, subject_id, subject.semester,
                           academic_year, mark)

    # Recalculate semester GPA + CGPA
    gpa_data = _recalculate_semester_gpa(student_id, subject.semester, academic_year)
    _recalculate_cgpa(student_id)

    # Check and award badges
    _check_badges(student_id)

    return jsonify({
        'message': 'Marks saved successfully',
        'calculation': calc,
        'grade': mark.grade,
        'total': float(mark.total_marks) if mark.total_marks else 0,
        'semester_gpa': gpa_data
    }), 200


@marks_bp.route('/semester/<int:semester>', methods=['GET'])
@jwt_required()
def get_semester_marks(semester):
    """Get all marks for a student in a semester."""
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims['role'] == 'student':
        student = Student.query.filter_by(user_id=user_id).first()
    else:
        student_id = request.args.get('student_id')
        student = Student.query.get(student_id)

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    academic_year = get_academic_year(semester, student.batch_year)

    # Get subjects for this semester
    subjects = Subject.query.filter_by(
        department_id=student.department_id,
        semester=semester,
        is_active=True
    ).all()

    result = []
    for subject in subjects:
        mark = Mark.query.filter_by(
            student_id=student.id,
            subject_id=subject.id,
            academic_year=academic_year,
            entry_mode='academic'
        ).first()

        result.append({
            'subject': subject.to_dict(),
            'mark': mark.to_dict() if mark else None
        })

    # Semester GPA if calculated
    sem_gpa = SemesterGPA.query.filter_by(
        student_id=student.id,
        semester=semester,
        academic_year=academic_year
    ).first()

    # Generate recommendations (only theory/lot with partial marks)
    partial_marks = [
        {**m['subject'], **(m['mark'] or {})}
        for m in result
        if m['mark'] and m['subject']['subject_type'] in ('theory', 'lot')
        and m['mark'].get('end_sem_theory') is None  # internals only
    ]
    recommendations = generate_recommendations(
        partial_marks,
        float(student.cgpa_record.overall_cgpa) if student.cgpa_record else 0
    )

    return jsonify({
        'semester': semester,
        'academic_year': academic_year,
        'subjects_with_marks': result,
        'semester_gpa': sem_gpa.to_dict() if sem_gpa else None,
        'recommendations': recommendations
    }), 200


@marks_bp.route('/simulate', methods=['POST'])
def simulate():
    """
    Simulation mode: calculate grades + GPA without saving.
    No auth required.
    """
    data = request.get_json()
    subjects = data.get('subjects', [])

    results = []
    for s in subjects:
        calc = calculate_marks_for_subject(s['subject_type'], s)
        results.append({
            'subject_name': s.get('subject_name', 'Subject'),
            'credits': s.get('credits', 0),
            'subject_type': s['subject_type'],
            'total': calc.get('total', 0),
            'grade': calc.get('grade', 'F'),
            'grade_point': calc.get('grade_point', 0),
            'breakdown': calc.get('breakdown', {})
        })

    gpa_data = calculate_gpa(results)

    return jsonify({
        'subjects': results,
        'gpa': gpa_data['gpa'],
        'total_credits': gpa_data['total_credits'],
        'subjects_passed': gpa_data['subjects_passed'],
        'subjects_failed': gpa_data['subjects_failed']
    }), 200


def _recalculate_semester_gpa(student_id: int, semester: int, academic_year: str) -> dict:
    """Internal: recalculate and save semester GPA."""
    marks = Mark.query.filter_by(
        student_id=student_id,
        semester=semester,
        academic_year=academic_year,
        entry_mode='academic'
    ).all()

    subjects_data = []
    for m in marks:
        subjects_data.append({
            'subject_type': m.subject.subject_type if m.subject else 'theory',
            'credits': m.subject.credits if m.subject else 0,
            'grade_point': float(m.grade_point) if m.grade_point else 0,
            'grade': m.grade or 'F',
            'pass_fail': m.pass_fail
        })

    if not subjects_data:
        return {}

    gpa_result = calculate_gpa(subjects_data)

    sem_gpa = SemesterGPA.query.filter_by(
        student_id=student_id,
        semester=semester,
        academic_year=academic_year
    ).first()

    if not sem_gpa:
        sem_gpa = SemesterGPA(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year
        )
        db.session.add(sem_gpa)

    sem_gpa.gpa = gpa_result['gpa']
    sem_gpa.total_credits = gpa_result['total_credits']
    sem_gpa.earned_credits = gpa_result['earned_credits']
    sem_gpa.subjects_passed = gpa_result['subjects_passed']
    sem_gpa.subjects_failed = gpa_result['subjects_failed']
    sem_gpa.non_credit_failed = gpa_result['non_credit_failed']
    db.session.commit()

    return gpa_result


def _recalculate_cgpa(student_id: int):
    """Internal: recalculate CGPA from all semester GPAs."""
    sem_gpas = SemesterGPA.query.filter_by(student_id=student_id).all()
    if not sem_gpas:
        return

    cgpa = calculate_cgpa([
        {'gpa': float(s.gpa), 'total_credits': s.total_credits}
        for s in sem_gpas
    ])

    # Count standing arrears
    standing_arrears = ArrearHistory.query.filter_by(
        student_id=student_id, cleared=False
    ).count()

    cgpa_rec = CGPARecord.query.filter_by(student_id=student_id).first()
    if not cgpa_rec:
        cgpa_rec = CGPARecord(student_id=student_id)
        db.session.add(cgpa_rec)

    cgpa_rec.overall_cgpa = cgpa
    cgpa_rec.total_credits_completed = sum(s.earned_credits for s in sem_gpas)
    cgpa_rec.standing_arrears = standing_arrears
    cgpa_rec.scholars_eligible = (cgpa >= 8.5 and standing_arrears == 0)

    db.session.commit()


def _update_arrear_history(student_id, subject_id, semester, academic_year, mark):
    """Internal: update arrear records based on mark result."""
    existing = ArrearHistory.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        academic_year=academic_year
    ).first()

    if mark.grade == 'F' or mark.pass_fail == 'fail':
        if not existing:
            arrear = ArrearHistory(
                student_id=student_id,
                subject_id=subject_id,
                semester=semester,
                academic_year=academic_year,
                grade_obtained=mark.grade,
                cleared=False
            )
            db.session.add(arrear)
        else:
            existing.grade_obtained = mark.grade
            existing.cleared = False
    elif existing and not existing.cleared:
        # Subject previously failed, now passed - mark as cleared
        existing.cleared = True
        existing.cleared_grade = mark.grade
        existing.cleared_in_year = academic_year

    db.session.commit()


def _check_badges(student_id: int):
    """Internal: award badges based on academic achievements."""
    student = Student.query.get(student_id)
    if not student or not student.cgpa_record:
        return

    cgpa = float(student.cgpa_record.overall_cgpa)
    arrears = student.cgpa_record.standing_arrears
    sem_gpas = student.semester_gpas

    def award(code):
        badge = Badge.query.filter_by(code=code).first()
        if badge:
            existing = StudentBadge.query.filter_by(
                student_id=student_id, badge_id=badge.id
            ).first()
            if not existing:
                db.session.add(StudentBadge(student_id=student_id, badge_id=badge.id))

    # First semester done
    if len(sem_gpas) >= 1:
        award('first_semester')

    # Perfect GPA
    if any(float(s.gpa) == 10.0 for s in sem_gpas):
        award('perfect_gpa')

    # Scholars
    if cgpa >= 8.5 and arrears == 0:
        award('scholars_entry')

    # CGPA milestones
    if cgpa >= 8.0:
        award('cgpa_8')
    if cgpa >= 9.0:
        award('cgpa_9')

    # No arrears in latest semester
    if sem_gpas:
        latest = max(sem_gpas, key=lambda s: s.semester)
        if latest.subjects_failed == 0 and latest.non_credit_failed == 0:
            award('all_pass')

    # Improvement (GPA up by 1.0+)
    if len(sem_gpas) >= 2:
        sorted_gpas = sorted(sem_gpas, key=lambda s: s.semester)
        if float(sorted_gpas[-1].gpa) - float(sorted_gpas[-2].gpa) >= 1.0:
            award('improvement')

    db.session.commit()
