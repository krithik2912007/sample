"""
Admin Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models import (db, User, Student, Mentor, Department, Subject,
                    Evaluation, EvaluationCriteria, CGPARecord, SemesterGPA)
from routes.auth import require_role
from werkzeug.security import generate_password_hash
import csv, io

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_role('admin')
def dashboard():
    total_students = Student.query.count()
    total_mentors = Mentor.query.count()

    # Status breakdown from latest evaluations
    cgpa_records = CGPARecord.query.all()
    scholars = sum(1 for r in cgpa_records if r.scholars_eligible)
    good = sum(1 for r in cgpa_records if float(r.overall_cgpa) >= 7.0 and not r.scholars_eligible)
    warning = sum(1 for r in cgpa_records if 5.0 <= float(r.overall_cgpa) < 7.0)
    probation = sum(1 for r in cgpa_records if float(r.overall_cgpa) < 5.0)

    # CGPA distribution buckets
    buckets = {'0-4': 0, '4-5': 0, '5-6': 0, '6-7': 0, '7-8': 0, '8-9': 0, '9-10': 0}
    for r in cgpa_records:
        c = float(r.overall_cgpa)
        if c < 4: buckets['0-4'] += 1
        elif c < 5: buckets['4-5'] += 1
        elif c < 6: buckets['5-6'] += 1
        elif c < 7: buckets['6-7'] += 1
        elif c < 8: buckets['7-8'] += 1
        elif c < 9: buckets['8-9'] += 1
        else: buckets['9-10'] += 1

    return jsonify({
        'total_students': total_students,
        'total_mentors': total_mentors,
        'scholars_count': scholars,
        'good_standing': good,
        'academic_warning': warning,
        'probation': probation,
        'cgpa_distribution': buckets
    }), 200


@admin_bp.route('/students', methods=['GET'])
@jwt_required()
@require_role('admin')
def list_students():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    semester = request.args.get('semester', type=int)

    query = Student.query.join(User, Student.user_id == User.id)
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (Student.reg_no.ilike(f'%{search}%'))
        )
    if semester:
        query = query.filter(Student.current_semester == semester)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'students': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200


@admin_bp.route('/students', methods=['POST'])
@jwt_required()
@require_role('admin')
def create_student():
    data = request.get_json()
    # Create user
    user = User(
        name=data['name'],
        email=data['email'],
        role='student'
    )
    user.set_password(data.get('password', 'REC@12345'))
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        reg_no=data['reg_no'],
        department_id=data['department_id'],
        batch_year=data['batch_year'],
        current_semester=data.get('current_semester', 1),
        mentor_id=data.get('mentor_id')
    )
    db.session.add(student)
    db.session.flush()

    cgpa_rec = CGPARecord(student_id=student.id)
    db.session.add(cgpa_rec)
    db.session.commit()

    return jsonify({'message': 'Student created', 'student': student.to_dict()}), 201


@admin_bp.route('/students/<int:sid>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_student(sid):
    student = Student.query.get_or_404(sid)
    data = request.get_json()
    student.current_semester = data.get('current_semester', student.current_semester)
    student.mentor_id = data.get('mentor_id', student.mentor_id)
    student.user.name = data.get('name', student.user.name)
    student.user.email = data.get('email', student.user.email)
    db.session.commit()
    return jsonify({'message': 'Updated', 'student': student.to_dict()}), 200


@admin_bp.route('/students/<int:sid>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_student(sid):
    student = Student.query.get_or_404(sid)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student deleted'}), 200


@admin_bp.route('/students/bulk-upload', methods=['POST'])
@jwt_required()
@require_role('admin')
def bulk_upload():
    """CSV upload: name,email,reg_no,department_id,batch_year,mentor_id"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'CSV file required'}), 400

    stream = io.StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(stream)
    created, errors = [], []

    for row in reader:
        try:
            user = User(name=row['name'], email=row['email'], role='student')
            user.set_password('REC@12345')
            db.session.add(user)
            db.session.flush()
            student = Student(
                user_id=user.id,
                reg_no=row['reg_no'],
                department_id=int(row['department_id']),
                batch_year=int(row['batch_year']),
                mentor_id=int(row['mentor_id']) if row.get('mentor_id') else None
            )
            db.session.add(student)
            db.session.flush()
            db.session.add(CGPARecord(student_id=student.id))
            created.append(row['reg_no'])
        except Exception as e:
            errors.append({'row': row.get('reg_no', '?'), 'error': str(e)})
            db.session.rollback()

    db.session.commit()
    return jsonify({'created': len(created), 'errors': errors}), 200


@admin_bp.route('/criteria', methods=['GET'])
@jwt_required()
@require_role('admin')
def get_criteria():
    criteria = EvaluationCriteria.query.all()
    return jsonify([c.to_dict() for c in criteria]), 200


@admin_bp.route('/criteria/<int:cid>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_criteria(cid):
    c = EvaluationCriteria.query.get_or_404(cid)
    data = request.get_json()
    c.min_cgpa = data.get('min_cgpa', c.min_cgpa)
    c.max_cgpa = data.get('max_cgpa', c.max_cgpa)
    c.max_arrears = data.get('max_arrears', c.max_arrears)
    c.color_code = data.get('color_code', c.color_code)
    c.action_required = data.get('action_required', c.action_required)
    db.session.commit()
    return jsonify(c.to_dict()), 200


# ─────────────────────────────────────────────────────────────
"""Mentor Routes"""
from models import MentorNote, ParentShareLink
from utils.calculator import scholars_status
import secrets
from datetime import datetime, timedelta

mentor_bp = Blueprint('mentor', __name__)


@mentor_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_role('mentor', 'admin')
def mentor_dashboard():
    user_id = int(get_jwt_identity() if hasattr(get_jwt_identity, '__call__') else 0)
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())

    students = Student.query.filter_by(mentor_id=user_id).all()
    data = []
    for s in students:
        cgpa = float(s.cgpa_record.overall_cgpa) if s.cgpa_record else 0
        arrears = s.cgpa_record.standing_arrears if s.cgpa_record else 0
        status = scholars_status(cgpa, arrears)
        data.append({
            **s.to_dict(),
            'scholars_info': status,
            'badges_count': len(s.badges)
        })

    # Summary stats
    cgpas = [float(s.cgpa_record.overall_cgpa) for s in students if s.cgpa_record]
    return jsonify({
        'students': data,
        'total': len(students),
        'avg_cgpa': round(sum(cgpas) / len(cgpas), 2) if cgpas else 0,
        'scholars_count': sum(1 for s in students if s.cgpa_record and s.cgpa_record.scholars_eligible),
        'at_risk': sum(1 for c in cgpas if c < 5.0),
        'warning': sum(1 for c in cgpas if 5.0 <= c < 7.0)
    }), 200


@mentor_bp.route('/students/<int:sid>/notes', methods=['GET'])
@jwt_required()
@require_role('mentor', 'admin')
def get_notes(sid):
    from flask_jwt_extended import get_jwt_identity
    notes = MentorNote.query.filter_by(student_id=sid).all()
    return jsonify([n.to_dict() for n in notes]), 200


@mentor_bp.route('/students/<int:sid>/notes', methods=['POST'])
@jwt_required()
@require_role('mentor', 'admin')
def add_note(sid):
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    data = request.get_json()
    note = MentorNote(
        mentor_id=user_id,
        student_id=sid,
        note=data['note'],
        is_private=data.get('is_private', True)
    )
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@mentor_bp.route('/students/<int:sid>/share-link', methods=['POST'])
@jwt_required()
@require_role('mentor', 'admin')
def generate_share_link(sid):
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    token = secrets.token_urlsafe(32)
    link = ParentShareLink(
        student_id=sid,
        mentor_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(link)
    db.session.commit()
    return jsonify({'token': token, 'link': f'/parent-view/{token}'}), 201


# ─────────────────────────────────────────────────────────────
"""Student Routes"""
student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_role('student')
def student_dashboard():
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({'error': 'Profile not found'}), 404

    cgpa_data = student.cgpa_record.to_dict() if student.cgpa_record else {}
    cgpa_val = float(student.cgpa_record.overall_cgpa) if student.cgpa_record else 0
    arrears = student.cgpa_record.standing_arrears if student.cgpa_record else 0

    sem_gpas = sorted(student.semester_gpas, key=lambda s: s.semester)
    scholars_info = scholars_status(cgpa_val, arrears)

    from utils.calculator import cgpa_needed_for_scholars
    scholars_plan = cgpa_needed_for_scholars(
        cgpa_val,
        len(sem_gpas),
        8
    )

    # Personal best
    best_gpa = max((float(s.gpa) for s in sem_gpas), default=0)
    best_semester = next((s.semester for s in sem_gpas if float(s.gpa) == best_gpa), None)

    badges = [sb.to_dict() for sb in student.badges]
    arrear_history = [a.to_dict() for a in student.arrears]

    return jsonify({
        'student': student.to_dict(),
        'cgpa': cgpa_data,
        'semester_gpas': [s.to_dict() for s in sem_gpas],
        'scholars_info': scholars_info,
        'scholars_plan': scholars_plan,
        'personal_best': {'gpa': best_gpa, 'semester': best_semester},
        'badges': badges,
        'arrear_history': arrear_history,
        'total_arrears': len(arrear_history),
        'standing_arrears': arrears
    }), 200


# ─────────────────────────────────────────────────────────────
"""Evaluation Routes"""
evaluation_bp = Blueprint('evaluation', __name__)


@evaluation_bp.route('/run-annual', methods=['POST'])
@jwt_required()
@require_role('admin')
def run_annual_evaluation():
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    data = request.get_json()
    academic_year = data.get('academic_year', '2024-25')

    criteria = EvaluationCriteria.query.all()
    criteria_list = [c.to_dict() for c in criteria]

    from utils.calculator import evaluate_academic_status
    students = Student.query.all()
    results = []

    for student in students:
        if not student.cgpa_record:
            continue
        cgpa = float(student.cgpa_record.overall_cgpa)
        arrears = student.cgpa_record.standing_arrears
        status_info = evaluate_academic_status(cgpa, arrears, criteria_list)

        # Map status label to enum value
        status_map = {
            'Good Standing': 'good_standing',
            'Academic Warning': 'academic_warning',
            'Probation': 'probation',
            'Dismissed from Program': 'dismissed'
        }
        status_enum = status_map.get(status_info['status'], 'academic_warning')

        ev = Evaluation(
            student_id=student.id,
            academic_year=academic_year,
            cgpa_at_evaluation=cgpa,
            standing_arrears=arrears,
            status=status_enum,
            scholars_status=student.cgpa_record.scholars_eligible,
            evaluated_by=user_id
        )
        db.session.add(ev)
        results.append({
            'student': student.to_dict(),
            'status': status_info,
            'cgpa': cgpa
        })

    db.session.commit()
    return jsonify({'evaluated': len(results), 'results': results}), 200


@evaluation_bp.route('/history', methods=['GET'])
@jwt_required()
def evaluation_history():
    from flask_jwt_extended import get_jwt_identity, get_jwt
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims['role'] == 'student':
        student = Student.query.filter_by(user_id=user_id).first()
        evals = Evaluation.query.filter_by(student_id=student.id).all()
    else:
        evals = Evaluation.query.order_by(Evaluation.evaluated_at.desc()).limit(200).all()

    return jsonify([e.to_dict() for e in evals]), 200


# ─────────────────────────────────────────────────────────────
"""Subjects Routes"""
subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('/<int:semester>', methods=['GET'])
@jwt_required()
def get_subjects(semester):
    dept_id = request.args.get('dept_id', 1, type=int)
    subjects = Subject.query.filter_by(
        department_id=dept_id,
        semester=semester,
        is_active=True
    ).all()
    return jsonify([s.to_dict() for s in subjects]), 200


@subjects_bp.route('/', methods=['POST'])
@jwt_required()
@require_role('admin')
def create_subject():
    data = request.get_json()
    s = Subject(
        code=data['code'],
        name=data['name'],
        department_id=data['department_id'],
        semester=data['semester'],
        subject_type=data['subject_type'],
        credits=data['credits'],
        l_hours=data.get('l_hours', 0),
        t_hours=data.get('t_hours', 0),
        p_hours=data.get('p_hours', 0),
        is_elective=data.get('is_elective', False),
        elective_group=data.get('elective_group'),
        lot_model_max=data.get('lot_model_max', 25)
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@subjects_bp.route('/<int:sid>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_subject(sid):
    s = Subject.query.get_or_404(sid)
    data = request.get_json()
    for field in ['code', 'name', 'subject_type', 'credits', 'semester',
                  'l_hours', 't_hours', 'p_hours', 'is_elective',
                  'elective_group', 'lot_model_max']:
        if field in data:
            setattr(s, field, data[field])
    db.session.commit()
    return jsonify(s.to_dict()), 200


# ─────────────────────────────────────────────────────────────
"""Reports Routes"""
reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/transcript/<int:student_id>', methods=['GET'])
@jwt_required()
def get_transcript(student_id):
    from flask_jwt_extended import get_jwt_identity, get_jwt
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    student = Student.query.get_or_404(student_id)

    # Students can only get their own transcript
    if claims['role'] == 'student':
        own = Student.query.filter_by(user_id=user_id).first()
        if not own or own.id != student_id:
            return jsonify({'error': 'Access denied'}), 403

    sem_gpas = sorted(student.semester_gpas, key=lambda s: s.semester)
    transcript = []

    for sem_gpa in sem_gpas:
        marks = Mark.query.filter_by(
            student_id=student_id,
            semester=sem_gpa.semester,
            academic_year=sem_gpa.academic_year,
            entry_mode='academic'
        ).all()
        transcript.append({
            'semester': sem_gpa.semester,
            'academic_year': sem_gpa.academic_year,
            'gpa': float(sem_gpa.gpa),
            'subjects': [m.to_dict() for m in marks]
        })

    return jsonify({
        'student': student.to_dict(),
        'cgpa': student.cgpa_record.to_dict() if student.cgpa_record else {},
        'transcript': transcript,
        'arrears': [a.to_dict() for a in student.arrears]
    }), 200


@reports_bp.route('/parent-view/<token>', methods=['GET'])
def parent_view(token):
    """Public read-only parent view (no auth)."""
    from models import ParentShareLink
    link = ParentShareLink.query.filter_by(token=token).first()
    if not link or link.expires_at < datetime.utcnow():
        return jsonify({'error': 'Link expired or invalid'}), 404

    student = link.student
    return jsonify({
        'student_name': student.user.name,
        'reg_no': student.reg_no,
        'department': student.department.name if student.department else '',
        'cgpa': float(student.cgpa_record.overall_cgpa) if student.cgpa_record else 0,
        'semester_gpas': [s.to_dict() for s in sorted(student.semester_gpas, key=lambda x: x.semester)],
        'scholars_eligible': student.cgpa_record.scholars_eligible if student.cgpa_record else False,
        'standing_arrears': student.cgpa_record.standing_arrears if student.cgpa_record else 0
    }), 200


# ─────────────────────────────────────────────────────────────
"""Pages Routes — serve HTML templates"""
from flask import render_template
pages_bp = Blueprint('pages', __name__)

from flask_jwt_extended import get_jwt_identity


@pages_bp.route('/')
def index():
    return render_template('auth/login.html')


@pages_bp.route('/login')
def login_page():
    return render_template('auth/login.html')


@pages_bp.route('/admin/dashboard')
def admin_dashboard_page():
    return render_template('admin/dashboard.html')


@pages_bp.route('/mentor/dashboard')
def mentor_dashboard_page():
    return render_template('mentor/dashboard.html')


@pages_bp.route('/student/dashboard')
def student_dashboard_page():
    return render_template('student/dashboard.html')


@pages_bp.route('/student/semester/<int:sem>')
def semester_page(sem):
    return render_template('student/semester.html', semester=sem)


@pages_bp.route('/student/simulator')
def simulator_page():
    return render_template('student/simulator.html')


@pages_bp.route('/parent-view/<token>')
def parent_view_page(token):
    return render_template('shared/parent_view.html', token=token)
