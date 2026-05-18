"""
Authentication Routes
JWT-based login for Admin, Mentor, Student roles
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from models import db, User, Student, Mentor, CGPARecord
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email, is_active=True).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Extra info for token
    additional_claims = {'role': user.role, 'name': user.name}

    # Attach profile-specific ID
    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            additional_claims['student_id'] = student.id
            additional_claims['reg_no'] = student.reg_no
            additional_claims['current_semester'] = student.current_semester
    elif user.role == 'mentor':
        mentor = Mentor.query.filter_by(user_id=user.id).first()
        if mentor:
            additional_claims['mentor_user_id'] = user.id

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
        'role': user.role
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    additional_claims = {'role': user.role, 'name': user.name}
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = user.to_dict()

    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            data['profile'] = student.to_dict()
            if student.cgpa_record:
                data['cgpa'] = student.cgpa_record.to_dict()
    elif user.role == 'mentor':
        mentor = Mentor.query.filter_by(user_id=user.id).first()
        if mentor:
            data['profile'] = mentor.to_dict()

    return jsonify(data), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()

    if not user.check_password(data.get('old_password', '')):
        return jsonify({'error': 'Current password is incorrect'}), 400

    new_password = data.get('new_password', '')
    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200


def require_role(*roles):
    """Decorator factory to restrict endpoint to specific roles."""
    from functools import wraps
    from flask_jwt_extended import verify_jwt_in_request

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
