"""
Grade Calculation Engine
Implements REC's exact marking scheme for all subject types.
"""


# ── Grade Boundaries (Anna University Pattern) ──────────────────────
GRADE_SCALE = [
    (91, 100, 'O',  10),
    (81,  90, 'A+',  9),
    (71,  80, 'A',   8),
    (61,  70, 'B+',  7),
    (51,  60, 'B',   6),
    (45,  50, 'C+',  5),
    (40,  44, 'C',   4),
    (0,   39, 'F',   0),
]


def get_grade(total_marks: float) -> tuple[str, float]:
    """Return (grade_letter, grade_point) for a given total out of 100."""
    for low, high, grade, point in GRADE_SCALE:
        if low <= total_marks <= high:
            return grade, point
    return 'F', 0


def calculate_theory(cat1: float, cat2: float, quiz: float, end_sem: float) -> dict:
    """
    Pure Theory Subject Calculation
    Internal = (CAT1 + CAT2 + Quiz) / 200 * 40
    External = EndSem / 100 * 60
    Total    = Internal + External
    """
    internal = round((cat1 + cat2 + quiz) / 200 * 40, 2)
    external = round(end_sem / 100 * 60, 2)
    total = round(internal + external, 2)
    grade, grade_point = get_grade(total)
    return {
        'internal': internal,
        'external': external,
        'total': total,
        'grade': grade,
        'grade_point': grade_point,
        'breakdown': {
            'theory_internal_raw': cat1 + cat2 + quiz,
            'theory_internal_converted': internal,
            'theory_external_converted': external
        }
    }


def calculate_lot(cat1: float, cat2: float, quiz: float,
                  end_sem_theory: float,
                  model_lab: float, model_max: int,
                  end_sem_practical: float) -> dict:
    """
    Lab Oriented Theory (LOT) Subject Calculation
    Theory Internal  = (CAT1+CAT2+Quiz) / 200 * 25
    Theory External  = EndSemTheory / 100 * 35
    Prac Internal    = ModelLab / model_max * 15  (model_max is 25 or 50)
    Prac External    = EndSemPractical / 100 * 25
    Total = all four (out of 100)
    """
    theory_internal = round((cat1 + cat2 + quiz) / 200 * 25, 2)
    theory_external = round(end_sem_theory / 100 * 35, 2)
    prac_internal = round(model_lab / model_max * 15, 2)
    prac_external = round(end_sem_practical / 100 * 25, 2)
    total = round(theory_internal + theory_external + prac_internal + prac_external, 2)
    grade, grade_point = get_grade(total)
    return {
        'internal': round(theory_internal + prac_internal, 2),
        'external': round(theory_external + prac_external, 2),
        'total': total,
        'grade': grade,
        'grade_point': grade_point,
        'breakdown': {
            'theory_internal': theory_internal,
            'theory_external': theory_external,
            'prac_internal': prac_internal,
            'prac_external': prac_external,
            'model_max_used': model_max
        }
    }


def calculate_lab(model_lab: float, end_sem_practical: float) -> dict:
    """
    Pure Lab Course
    Model    = out of 25 (direct)
    Semester = out of 75 (direct)
    Total    = Model + Semester (out of 100, no scaling)
    """
    total = round(model_lab + end_sem_practical, 2)
    grade, grade_point = get_grade(total)
    return {
        'internal': model_lab,
        'external': end_sem_practical,
        'total': total,
        'grade': grade,
        'grade_point': grade_point,
        'breakdown': {
            'model_25': model_lab,
            'semester_75': end_sem_practical
        }
    }


def calculate_soft_skills(ss_cat1: float, ss_cat2: float, ss_cat3: float) -> dict:
    """
    Soft Skills Subject
    Total = (CAT1 + CAT2 + CAT3) / 300 * 100
    """
    total = round((ss_cat1 + ss_cat2 + ss_cat3) / 300 * 100, 2)
    grade, grade_point = get_grade(total)
    return {
        'internal': total,
        'external': 0,
        'total': total,
        'grade': grade,
        'grade_point': grade_point,
        'breakdown': {
            'ss_cat1': ss_cat1,
            'ss_cat2': ss_cat2,
            'ss_cat3': ss_cat3,
            'raw_total': ss_cat1 + ss_cat2 + ss_cat3,
            'converted_to_100': total
        }
    }


def calculate_project(model_lab: float, end_sem_practical: float) -> dict:
    """Project Phase treated like Lab (Model 25 + Sem 75)."""
    return calculate_lab(model_lab, end_sem_practical)


def calculate_marks_for_subject(subject_type: str, data: dict) -> dict:
    """
    Master dispatcher. Call with subject_type and a data dict.
    Returns calculation result with total, grade, grade_point.
    """
    try:
        if subject_type == 'theory':
            return calculate_theory(
                float(data.get('cat1', 0) or 0),
                float(data.get('cat2', 0) or 0),
                float(data.get('quiz', 0) or 0),
                float(data.get('end_sem_theory', 0) or 0)
            )
        elif subject_type == 'lot':
            return calculate_lot(
                float(data.get('cat1', 0) or 0),
                float(data.get('cat2', 0) or 0),
                float(data.get('quiz', 0) or 0),
                float(data.get('end_sem_theory', 0) or 0),
                float(data.get('model_lab', 0) or 0),
                int(data.get('model_max', 25) or 25),
                float(data.get('end_sem_practical', 0) or 0)
            )
        elif subject_type in ('lab', 'project'):
            return calculate_lab(
                float(data.get('model_lab', 0) or 0),
                float(data.get('end_sem_practical', 0) or 0)
            )
        elif subject_type == 'soft_skills':
            return calculate_soft_skills(
                float(data.get('ss_cat1', 0) or 0),
                float(data.get('ss_cat2', 0) or 0),
                float(data.get('ss_cat3', 0) or 0)
            )
        elif subject_type in ('internship', 'non_credit'):
            return {
                'internal': 0, 'external': 0, 'total': 0,
                'grade': None, 'grade_point': 0,
                'pass_fail': data.get('pass_fail', 'pending'),
                'breakdown': {}
            }
        else:
            raise ValueError(f"Unknown subject type: {subject_type}")
    except Exception as e:
        return {'error': str(e), 'total': 0, 'grade': 'F', 'grade_point': 0}


def calculate_gpa(subjects_data: list) -> dict:
    """
    Calculate GPA for a semester.
    subjects_data: list of dicts with 'grade_point', 'credits', 'subject_type', 'grade'
    Non-credit subjects excluded from GPA calculation.
    """
    total_credit_points = 0
    total_credits = 0
    passed = 0
    failed = 0
    non_credit_failed = 0

    for s in subjects_data:
        stype = s.get('subject_type', '')
        credits = s.get('credits', 0)
        grade_point = float(s.get('grade_point', 0) or 0)
        grade = s.get('grade', 'F')

        if stype in ('non_credit', 'internship'):
            if s.get('pass_fail') == 'fail':
                non_credit_failed += 1
            continue  # Skip from GPA

        total_credit_points += grade_point * credits
        total_credits += credits

        if grade == 'F' or grade_point == 0:
            failed += 1
        else:
            passed += 1

    gpa = round(total_credit_points / total_credits, 2) if total_credits > 0 else 0.0

    return {
        'gpa': gpa,
        'total_credits': total_credits,
        'earned_credits': sum(
            s['credits'] for s in subjects_data
            if s.get('subject_type') not in ('non_credit', 'internship')
            and s.get('grade', 'F') != 'F'
            and float(s.get('grade_point', 0) or 0) > 0
        ),
        'subjects_passed': passed,
        'subjects_failed': failed,
        'non_credit_failed': non_credit_failed
    }


def calculate_cgpa(semester_gpas: list) -> float:
    """
    Calculate CGPA from list of semester GPA records.
    semester_gpas: list of dicts with 'gpa' and 'total_credits'
    CGPA = Σ(GPA × Credits) / Σ Credits
    """
    total_credit_points = sum(s['gpa'] * s['total_credits'] for s in semester_gpas)
    total_credits = sum(s['total_credits'] for s in semester_gpas)
    return round(total_credit_points / total_credits, 2) if total_credits > 0 else 0.0


# ── Scholars & Recommendation Engine ────────────────────────────────

def scholars_status(cgpa: float, standing_arrears: int) -> dict:
    """Determine Scholars Program eligibility and motivational state."""
    if cgpa >= 8.5 and standing_arrears == 0:
        return {
            'eligible': True,
            'state': 'scholars',
            'message': '🏆 You are a Scholars Program member!',
            'sub_message': 'Keep maintaining this standard to retain your privileges.',
            'color': '#10b981',
            'gap': 0
        }
    elif cgpa >= 7.5:
        gap = round(8.5 - cgpa, 2)
        return {
            'eligible': False,
            'state': 'within_reach',
            'message': f'🎯 Scholars Program is within reach!',
            'sub_message': f'You are only {gap} CGPA points away from the Scholars Program.',
            'color': '#f59e0b',
            'gap': gap
        }
    else:
        gap = round(8.5 - cgpa, 2)
        return {
            'eligible': False,
            'state': 'keep_working',
            'message': '💪 Work towards Scholars Program',
            'sub_message': f'You need {gap} more CGPA points. Consistent effort over upcoming semesters will get you there.',
            'color': '#6366f1',
            'gap': gap
        }


def generate_recommendations(student_marks: list, current_cgpa: float,
                              scholars_target: float = 8.5) -> list:
    """
    Generate per-subject recommendations for end sem strategy.
    student_marks: list of dicts with subject info + internal marks entered so far
    """
    recommendations = []

    for mark in student_marks:
        stype = mark.get('subject_type')
        if stype not in ('theory', 'lot'):
            continue

        subject_name = mark.get('subject_name', 'Subject')
        rec = {'subject': subject_name, 'alerts': [], 'targets': []}

        if stype == 'theory':
            cat1 = float(mark.get('cat1', 0) or 0)
            cat2 = float(mark.get('cat2', 0) or 0)
            quiz = float(mark.get('quiz', 0) or 0)
            internal = round((cat1 + cat2 + quiz) / 200 * 40, 2)
            rec['internal_earned'] = internal

            # Calculate end sem needed for each grade
            for target_grade, _, grade_letter, _ in [
                (40, 100, 'C (Pass)', 4),
                (51, 100, 'B', 6),
                (61, 100, 'B+', 7),
                (71, 100, 'A', 8),
                (81, 100, 'A+', 9),
                (91, 100, 'O', 10)
            ]:
                needed_external = round((target_grade - internal) / 0.6, 1)
                if 0 <= needed_external <= 100:
                    rec['targets'].append({
                        'grade': grade_letter,
                        'end_sem_needed': needed_external
                    })

            # Alert if at risk of failing
            min_pass_end_sem = round((40 - internal) / 0.6, 1)
            if min_pass_end_sem > 60:
                rec['alerts'].append(f'⚠️ High risk! You need {min_pass_end_sem}/100 in end sem just to pass.')
            elif min_pass_end_sem > 40:
                rec['alerts'].append(f'ℹ️ You need {min_pass_end_sem}/100 in end sem to pass.')

        recommendations.append(rec)

    return recommendations


def evaluate_academic_status(cgpa: float, standing_arrears: int,
                              criteria: list) -> dict:
    """
    Determine academic standing based on admin-configured criteria.
    criteria: list of EvaluationCriteria dicts
    """
    for c in sorted(criteria, key=lambda x: x['min_cgpa'], reverse=True):
        if (float(c['min_cgpa']) <= cgpa <= float(c['max_cgpa'])
                and standing_arrears <= c['max_arrears']):
            return {
                'status': c['status_label'],
                'color': c['color_code'],
                'action': c['action_required']
            }
    return {
        'status': 'Under Review',
        'color': '#6b7280',
        'action': 'Please contact admin for status.'
    }


def cgpa_needed_for_scholars(current_cgpa: float, semesters_done: int,
                               total_semesters: int = 8) -> dict:
    """
    Calculate what average GPA is needed in remaining semesters
    to reach 8.5 CGPA for Scholars Program.
    Simplified: uses equal credits assumption.
    """
    remaining = total_semesters - semesters_done
    if remaining <= 0:
        return {'achievable': cgpa >= 8.5, 'needed_avg': None, 'remaining_semesters': 0}

    needed_total = 8.5 * total_semesters
    current_total = current_cgpa * semesters_done
    needed_remaining = needed_total - current_total
    needed_avg_per_sem = round(needed_remaining / remaining, 2)

    return {
        'achievable': needed_avg_per_sem <= 10.0,
        'needed_avg_gpa': needed_avg_per_sem,
        'remaining_semesters': remaining,
        'message': (
            f'Score an average GPA of {needed_avg_per_sem} in your next {remaining} semester(s) to reach Scholars CGPA.'
            if needed_avg_per_sem <= 10
            else 'Scholars CGPA of 8.5 is not achievable from current standing.'
        )
    }
