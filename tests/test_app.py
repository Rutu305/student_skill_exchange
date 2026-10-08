import pytest
import os
from app import app, db
from models import User, Skill, UserSkill, UserWantsToLearn, ConnectionRequest, seed_database
from gemini_service import get_predefined_questions
from validators import (
    validate_name, validate_class, validate_gender, validate_email,
    validate_phone, validate_password_strength
)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            seed_database()
        yield client


def test_seed_skills(client):
    """Test that default catalog skills are seeded correctly."""
    with app.app_context():
        skills = Skill.query.all()
        assert len(skills) >= 13
        skill_names = [s.skill_name for s in skills]
        assert 'Python' in skill_names
        assert 'Java' in skill_names
        assert 'React' in skill_names


def test_strong_validations_unit():
    """Unit test individual validation rules."""
    # 1. Name validation
    assert validate_name('Rutuja Patil')[0] is True
    assert validate_name('A')[0] is False  # too short
    assert validate_name('User123')[0] is False  # contains numbers
    assert validate_name('User<script>')[0] is False  # XSS attempt

    # 2. Class validation
    assert validate_class('B.Tech 3rd Year')[0] is True
    assert validate_class('')[0] is False
    assert validate_class('x' * 60)[0] is False  # too long

    # 3. Gender validation
    assert validate_gender('Female')[0] is True
    assert validate_gender('InvalidGender')[0] is False

    # 4. Email validation
    assert validate_email('student@university.edu')[0] is True
    assert validate_email('bad-email')[0] is False
    assert validate_email('test@')[0] is False

    # 5. Phone validation
    assert validate_phone('9876543210')[0] is True
    assert validate_phone('12345')[0] is False  # short
    assert validate_phone('0000000000')[0] is False  # trivial repeated numbers
    assert validate_phone('abcdefghij')[0] is False

    # 6. Password strength validation
    assert validate_password_strength('StrongPass@123')[0] is True
    assert validate_password_strength('short')[0] is False  # < 8
    assert validate_password_strength('nouppercase@123')[0] is False  # no upper
    assert validate_password_strength('NOLOWERCASE@123')[0] is False  # no lower
    assert validate_password_strength('NoSpecialChar123')[0] is False  # no special
    assert validate_password_strength('NoNumbersHere!')[0] is False  # no number


def test_user_registration_and_login(client):
    """Test registration with strong validation, duplicate email check, and login verification."""
    # 1. Weak password rejected
    res_weak = client.post('/register', data={
        'name': 'Alice Test',
        'class': 'B.Tech 3rd Year',
        'gender': 'Female',
        'email': 'alice@example.com',
        'password': 'weak',
        'confirm_password': 'weak',
        'phone': '9876543210'
    })
    assert b'Password must include' in res_weak.data

    # 2. Mismatched passwords rejected
    res_mismatch = client.post('/register', data={
        'name': 'Alice Test',
        'class': 'B.Tech 3rd Year',
        'gender': 'Female',
        'email': 'alice@example.com',
        'password': 'StrongPass@123',
        'confirm_password': 'DifferentPass@123',
        'phone': '9876543210'
    })
    assert b'Passwords do not match' in res_mismatch.data

    # 3. Invalid phone rejected
    res_bad_phone = client.post('/register', data={
        'name': 'Alice Test',
        'class': 'B.Tech 3rd Year',
        'gender': 'Female',
        'email': 'alice@example.com',
        'password': 'StrongPass@123',
        'confirm_password': 'StrongPass@123',
        'phone': '0000000000'
    })
    assert b'non-trivial 10-digit mobile number' in res_bad_phone.data

    # 4. Successful Registration
    res = client.post('/register', data={
        'name': 'Alice Test',
        'class': 'B.Tech 3rd Year',
        'gender': 'Female',
        'email': 'alice@example.com',
        'password': 'StrongPass@123',
        'confirm_password': 'StrongPass@123',
        'phone': '9876543210'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Account created successfully' in res.data or b'Login' in res.data

    # 5. Duplicate Email Registration Failure
    res_dup = client.post('/register', data={
        'name': 'Alice Two',
        'class': '12th',
        'gender': 'Female',
        'email': 'alice@example.com',
        'password': 'StrongPass@123',
        'confirm_password': 'StrongPass@123',
        'phone': '9876543211'
    })
    assert b'Email is already registered' in res_dup.data

    # 6. Incorrect Password Login
    res_wrong_pw = client.post('/login', data={
        'email': 'alice@example.com',
        'password': 'WrongPassword@999'
    })
    assert b'Incorrect password' in res_wrong_pw.data

    # 7. Incorrect Email Login
    res_wrong_email = client.post('/login', data={
        'email': 'nobody@example.com',
        'password': 'StrongPass@123'
    })
    assert b'Incorrect email' in res_wrong_email.data

    # 8. Correct Login
    res_login = client.post('/login', data={
        'email': 'alice@example.com',
        'password': 'StrongPass@123'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b'Alice Test' in res_login.data
    assert b'Dashboard' in res_login.data


def test_forgot_and_reset_password(client):
    """Test forgot password verification and resetting password with strong password policy."""
    # Register user
    client.post('/register', data={
        'name': 'Bob Reset',
        'class': 'BCA 1st Year',
        'gender': 'Male',
        'email': 'bob@example.com',
        'password': 'InitialPass@123',
        'confirm_password': 'InitialPass@123',
        'phone': '9123456789'
    })

    # Verify account
    res_verify = client.post('/forgot-password', data={
        'email': 'bob@example.com',
        'phone': '9123456789'
    }, follow_redirects=True)
    assert res_verify.status_code == 200
    assert b'Set New Password' in res_verify.data

    # Weak password reset attempt rejected
    res_weak_reset = client.post('/reset-password', data={
        'password': 'short',
        'confirm_password': 'short'
    })
    assert b'Password must include' in res_weak_reset.data

    # Valid strong reset password
    res_reset = client.post('/reset-password', data={
        'password': 'BrandNewPass@456',
        'confirm_password': 'BrandNewPass@456'
    }, follow_redirects=True)
    assert res_reset.status_code == 200
    assert b'Password reset successfully' in res_reset.data

    # Log in with new password
    res_new_login = client.post('/login', data={
        'email': 'bob@example.com',
        'password': 'BrandNewPass@456'
    }, follow_redirects=True)
    assert b'Bob Reset' in res_new_login.data


def test_skill_test_flow(client):
    """Test taking a skill test, passing it, and verifying it gets added to user profile."""
    # Register and login
    client.post('/register', data={
        'name': 'Charlie Quiz',
        'class': 'B.Tech CS',
        'gender': 'Male',
        'email': 'charlie@example.com',
        'password': 'CharliePass@123',
        'confirm_password': 'CharliePass@123',
        'phone': '9988776655'
    })
    client.post('/login', data={
        'email': 'charlie@example.com',
        'password': 'CharliePass@123'
    })

    # Submit have_skills to trigger test
    res_save = client.post('/dashboard', data={
        'save_skills': '1',
        'have_skills[]': ['Python'],
        'want_skills[]': ['Java']
    }, follow_redirects=True)
    assert b'Python' in res_save.data
    assert b'Quiz' in res_save.data or b'Test' in res_save.data

    # Submit answers for Python test
    res_submit_test = client.post('/take-test', data={
        'q0': '2',
        'q1': '2',
        'q2': '0',
        'q3': '0',
        'q4': '2'
    }, follow_redirects=True)
    assert b'Test Results' in res_submit_test.data

    # Return to dashboard
    res_dash = client.post('/test-result', data={'action': 'dashboard'}, follow_redirects=True)
    assert b'Your Verified Skills' in res_dash.data
    assert b'Python' in res_dash.data


def test_mutual_matching_and_connection_requests(client):
    """Test mutual peer matching and connection request flow between two students."""
    # User 1: Student A (has Python verified, wants Java)
    client.post('/register', data={
        'name': 'Student A',
        'class': 'B.Tech Year 2',
        'gender': 'Male',
        'email': 'studenta@example.com',
        'password': 'StudentPass@123',
        'confirm_password': 'StudentPass@123',
        'phone': '9000000001'
    })
    client.post('/login', data={'email': 'studenta@example.com', 'password': 'StudentPass@123'})
    with app.app_context():
        u1 = User.query.filter_by(email='studenta@example.com').first()
        u1_id = u1.id
        db.session.add(UserSkill(user_id=u1_id, skill_name='Python', rating=5))
        db.session.add(UserWantsToLearn(user_id=u1_id, skill_name='Java'))
        db.session.commit()
    client.get('/logout')

    # User 2: Student B (has Java verified, wants Python)
    client.post('/register', data={
        'name': 'Student B',
        'class': 'B.Tech Year 3',
        'gender': 'Female',
        'email': 'studentb@example.com',
        'password': 'StudentPass@456',
        'confirm_password': 'StudentPass@456',
        'phone': '9000000002'
    })
    client.post('/login', data={'email': 'studentb@example.com', 'password': 'StudentPass@456'})
    with app.app_context():
        u2 = User.query.filter_by(email='studentb@example.com').first()
        u2_id = u2.id
        db.session.add(UserSkill(user_id=u2_id, skill_name='Java', rating=4))
        db.session.add(UserWantsToLearn(user_id=u2_id, skill_name='Python'))
        db.session.commit()

    # View dashboard for Student B: Should see Student A as a mutual match!
    res_b_dash = client.get('/dashboard')
    assert b'Student A' in res_b_dash.data
    assert b'Send Request' in res_b_dash.data

    # Student B sends connection request to Student A
    res_send = client.get(f'/request/send/{u1_id}', follow_redirects=True)
    assert b'Connection request sent!' in res_send.data
    assert b'Request Sent' in res_send.data
    client.get('/logout')

    # Student A logs in: Should see pending request from Student B
    client.post('/login', data={'email': 'studenta@example.com', 'password': 'StudentPass@123'})
    res_a_dash = client.get('/dashboard')
    assert b'Connection Requests Received' in res_a_dash.data
    assert b'Student B' in res_a_dash.data

    with app.app_context():
        req = ConnectionRequest.query.filter_by(from_user_id=u2_id, to_user_id=u1_id).first()
        req_id = req.id

    # Student A accepts the request
    res_accept = client.get(f'/request/accept/{req_id}', follow_redirects=True)
    assert b'Connection request accepted!' in res_accept.data

    # Contact info should now be unlocked and visible!
    assert b'Your Connections (Contact Details Unlocked)' in res_accept.data
    assert b'studentb@example.com' in res_accept.data
    assert b'9000000002' in res_accept.data


def test_question_banks_coverage():
    """Verify that offline question bank provides 5 questions with 4 options each."""
    test_skills = ['Java', 'Python', 'JavaScript', 'React', 'Node.js', 'PHP', 'HTML/CSS', 'MySQL', 'UI/UX Design', 'English Speaking', 'Spanish', 'French', 'Machine Learning']
    for skill in test_skills:
        questions = get_predefined_questions(skill)
        assert len(questions) == 5, f"Failed length for {skill}"
        for q in questions:
            assert 'question' in q
            assert len(q['options']) == 4
            assert 0 <= q['correct'] <= 3
