import sys
import os

# Append the current directory so app and models can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from models import User

    app = create_app()
    with app.app_context():
        # Make sure tables exist
        db.create_all()

        admin = User.query.filter_by(email='admin@rec.edu').first()
        if not admin:
            print("Creating admin user...")
            admin = User(email='admin@rec.edu', role='Admin')
            db.session.add(admin)
        admin.set_password('Admin@123')

        mentor = User.query.filter_by(email='mentor1@rec.edu').first()
        if not mentor:
            print("Creating mentor user...")
            mentor = User(email='mentor1@rec.edu', role='Mentor')
            db.session.add(mentor)
        mentor.set_password('Mentor@123')

        student = User.query.filter_by(email='student1@rec.edu').first()
        if not student:
            print("Creating student user...")
            student = User(email='student1@rec.edu', role='Student')
            db.session.add(student)
        student.set_password('Student@123')

        db.session.commit()
        print("Passwords successfully set for Admin, Mentor, and Student roles as mentioned in README.md!")
except Exception as e:
    print(f"An error occurred: {e}")
