# Academic Performance Evaluation System
## REC — CSE Department | Regulation 2023

---

## 📁 Project Structure

```
academic_eval/
├── app.py                    # Flask app factory & entry point
├── models.py                 # All SQLAlchemy models
├── requirements.txt
├── schema.sql                # Full DB schema + CSE subject seed data
├── .env                      # (create this — see below)
│
├── routes/
│   └── __init__.py           # All routes: auth, admin, mentor, student,
│                             #   marks, subjects, evaluation, reports, pages
│
├── utils/
│   └── calculator.py         # Grade calculation engine (Theory/LOT/Lab/Soft Skills)
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── templates/
    ├── auth/
    │   └── login.html        # Login page (3-role)
    ├── admin/
    │   └── dashboard.html    # Admin dashboard
    ├── mentor/
    │   └── dashboard.html    # Mentor dashboard
    ├── student/
    │   ├── dashboard.html    # Student main dashboard
    │   ├── semester.html     # Semester marks entry (CORE UX)
    │   └── simulator.html    # Grade simulator
    └── shared/
        ├── base.html         # Shared CSS + JS utilities
        └── parent_view.html  # Parent share link view
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### 2. Clone & Install

```bash
cd academic_eval
pip install -r requirements.txt
```

### 3. Create `.env` File

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost/academic_eval
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=youremail@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@rec.edu
```

### 4. Set Up Database

```bash
# Login to MySQL
mysql -u root -p

# Run schema
source /path/to/academic_eval/schema.sql
```

Or via Flask shell:
```bash
flask shell
>>> from app import db
>>> db.create_all()
```

### 5. Seed Default Passwords

After running schema.sql, update passwords via Flask shell:
```python
from app import create_app, db
from models import User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(email='admin@rec.edu').first()
    admin.set_password('Admin@123')
    mentor = User.query.filter_by(email='mentor1@rec.edu').first()
    mentor.set_password('Mentor@123')
    student = User.query.filter_by(email='student1@rec.edu').first()
    student.set_password('Student@123')
    db.session.commit()
    print("Passwords set!")
```

### 6. Run the App

```bash
python app.py
# → http://localhost:5000
```

---

## 🔐 Default Login Credentials

| Role    | Email              | Password    |
|---------|--------------------|-------------|
| Admin   | admin@rec.edu      | Admin@123   |
| Mentor  | mentor1@rec.edu    | Mentor@123  |
| Student | student1@rec.edu   | Student@123 |

---

## 📐 Grade Calculation Logic

### Theory Subject
```
Internal = (CAT1 + CAT2 + Quiz) / 200 × 40
External = End Sem / 100 × 60
Total    = Internal + External  (out of 100)
```

### LOT (Lab Oriented Theory)
```
Theory Internal  = (CAT1 + CAT2 + Quiz) / 200 × 25
Theory External  = End Sem Theory / 100 × 35
Prac Internal    = Model Lab / (25 or 50) × 15
Prac External    = End Sem Practical / 100 × 25
Total            = All four  (out of 100)
```

### Lab Course
```
Model Exam  = / 25 (direct)
Semester    = / 75 (direct)
Total       = Model + Semester  (out of 100)
```

### Soft Skills
```
Total = (CAT1 + CAT2 + CAT3) / 300 × 100
```

### Grade Scale (Anna University)
| Marks   | Grade | Points |
|---------|-------|--------|
| 91–100  | O     | 10     |
| 81–90   | A+    | 9      |
| 71–80   | A     | 8      |
| 61–70   | B+    | 7      |
| 51–60   | B     | 6      |
| 45–50   | C+    | 5      |
| 40–44   | C     | 4      |
| < 40    | F     | 0      |

---

## 🚀 API Reference

### Auth
```
POST /api/auth/login          → {access_token, refresh_token, user, role}
POST /api/auth/refresh        → {access_token}
GET  /api/auth/me             → current user profile
POST /api/auth/change-password
```

### Marks
```
POST /api/marks/calculate     → preview grade (no save, no auth)
POST /api/marks/save          → save academic mark (auth required)
GET  /api/marks/semester/:n   → get all marks for a semester
POST /api/marks/simulate      → simulate GPA from multiple subjects
```

### Admin
```
GET  /api/admin/dashboard
GET  /api/admin/students
POST /api/admin/students
PUT  /api/admin/students/:id
DEL  /api/admin/students/:id
POST /api/admin/students/bulk-upload  → CSV upload
GET  /api/admin/criteria
PUT  /api/admin/criteria/:id
```

### Mentor
```
GET  /api/mentor/dashboard
GET  /api/mentor/students/:id/notes
POST /api/mentor/students/:id/notes
POST /api/mentor/students/:id/share-link
```

### Student
```
GET  /api/student/dashboard
```

### Subjects
```
GET  /api/subjects/:semester
POST /api/subjects/            → admin only
PUT  /api/subjects/:id         → admin only
```

### Evaluation
```
POST /api/evaluation/run-annual  → admin only
GET  /api/evaluation/history
```

### Reports
```
GET  /api/reports/transcript/:student_id
GET  /api/reports/parent-view/:token    → public, no auth
```

---

## 🏗️ What's Built (V1)

✅ Complete database schema (14 tables)
✅ Grade calculation engine (Theory / LOT / Lab / Soft Skills / Non-Credit)
✅ JWT authentication (3 roles)
✅ All backend API routes
✅ Login page (professional, role-selector)
✅ Semester marks entry page (live calculation, subject-type forms)
✅ Shared design system (sidebar, cards, charts, modals, toasts)
✅ Scholars Program logic
✅ Arrear tracking
✅ Badge system
✅ CGPA calculation
✅ CSE Semesters 1–6 pre-seeded subjects

## 📋 To Complete (Next Sessions)

- [ ] Admin dashboard HTML (charts, student table, evaluation runner)
- [ ] Mentor dashboard HTML (30-student grid, notes, share link)
- [ ] Student dashboard HTML (CGPA ring, GPA trend chart, badges)
- [ ] Grade Simulator page
- [ ] PDF transcript generation (xhtml2pdf)
- [ ] Parent share view page
- [ ] Email notifications (Flask-Mail)
- [ ] Bulk CSV upload UI
- [ ] Leaderboard page
- [ ] Sem 7–8 admin subject posting UI
