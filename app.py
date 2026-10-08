import os
import re
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from config import Config
from models import (
    db, User, Skill, UserSkill, UserWantsToLearn, ConnectionRequest, seed_database
)
from gemini_service import generate_mcqs_with_gemini
from matcher import (
    find_mutual_matches, get_accepted_connections, get_pending_received_requests
)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    seed_database()


def login_required(func):
    """Decorator to require login for protected routes."""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


from validators import (
    validate_name, validate_class, validate_gender, validate_email,
    validate_phone, validate_password_strength
)

# -------------------------------------------------------------
# LANDING & AUTH ROUTES
# -------------------------------------------------------------

@app.route('/')
def index():
    is_logged_in = 'user_id' in session
    user_name = session.get('user_name', '')
    return render_template('index.html', is_logged_in=is_logged_in, user_name=user_name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_name = request.form.get('class', '').strip()
        gender = request.form.get('gender', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()

        errors = []
        
        # 1. Name Validation
        ok, msg = validate_name(name)
        if not ok:
            errors.append(msg)

        # 2. Class Validation
        ok, msg = validate_class(class_name)
        if not ok:
            errors.append(msg)

        # 3. Gender Validation
        ok, msg = validate_gender(gender)
        if not ok:
            errors.append(msg)

        # 4. Email Validation
        ok, msg = validate_email(email)
        if not ok:
            errors.append(msg)
        else:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('Email is already registered. Please login.')

        # 5. Phone Validation
        ok, msg = validate_phone(phone)
        if not ok:
            errors.append(msg)

        # 6. Strong Password Validation
        ok, issues = validate_password_strength(password)
        if not ok:
            errors.extend(issues)
        elif password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            error = ' • '.join(errors)
        else:
            new_user = User(
                name=name,
                class_name=class_name,
                gender=gender,
                email=email,
                phone=phone
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            error = 'Please fill in all fields'
        else:
            ok, msg = validate_email(email)
            if not ok:
                error = 'Please enter a valid email format'
            else:
                user = User.query.filter_by(email=email).first()
                if not user:
                    error = 'Incorrect email'
                elif not user.check_password(password):
                    error = 'Incorrect password'
                else:
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_email'] = user.email
                    flash(f'Welcome back, {user.name}!', 'success')
                    return redirect(url_for('dashboard'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()

        if not email or not phone:
            error = 'Please fill in both fields'
        else:
            ok_email, _ = validate_email(email)
            ok_phone, _ = validate_phone(phone)
            if not ok_email or not ok_phone:
                error = 'Invalid email or phone number format'
            else:
                user = User.query.filter_by(email=email, phone=phone).first()
                if user:
                    session['reset_email'] = email
                    return redirect(url_for('reset_password'))
                else:
                    error = 'Invalid email or phone number'

    return render_template('forgot_password.html', error=error)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    reset_email = session.get('reset_email')
    if not reset_email:
        flash('Session expired or invalid reset request. Please try again.', 'warning')
        return redirect(url_for('forgot_password'))

    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        ok, issues = validate_password_strength(password)
        if not ok:
            errors.extend(issues)
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            error = ' • '.join(errors)
        else:
            user = User.query.filter_by(email=reset_email).first()
            if user:
                user.set_password(password)
                db.session.commit()
                session.pop('reset_email', None)
                flash('Password reset successfully! Please log in with your new password.', 'success')
                return redirect(url_for('login'))
            else:
                error = 'User not found. Please try again.'

    return render_template('reset_password.html', error=error)


# -------------------------------------------------------------
# DASHBOARD & SKILL MANAGEMENT
# -------------------------------------------------------------

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_id = session['user_id']
    user = db.get_or_404(User, user_id)

    # Fetch all catalog skills
    all_skills = [s.skill_name for s in Skill.query.order_by(Skill.skill_name).all()]

    # Fetch user verified skills
    user_skills = UserSkill.query.filter_by(user_id=user_id).all()
    verified_skill_names = [us.skill_name for us in user_skills]

    # Fetch user want to learn skills
    wants_to_learn = UserWantsToLearn.query.filter_by(user_id=user_id).all()
    wants_skill_names = [wl.skill_name for wl in wants_to_learn]

    if request.method == 'POST':
        if 'save_skills' in request.form:
            have_raw = request.form.getlist('have_skills[]') or request.form.getlist('have_skills')
            want_raw = request.form.getlist('want_skills[]') or request.form.getlist('want_skills')

            # Validate against database catalog
            have_skills = [s.strip() for s in have_raw if s.strip() in all_skills]
            want_skills = [s.strip() for s in want_raw if s.strip() in all_skills]

            # Conflict validation: Cannot want to learn a skill you already have verified!
            conflicts = [s for s in want_skills if s in verified_skill_names]
            if conflicts:
                want_skills = [s for s in want_skills if s not in verified_skill_names]
                flash(f"Note: {', '.join(conflicts)} is already verified in your profile, so it was removed from 'want to learn'.", 'info')

            # 1. Update wants to learn
            UserWantsToLearn.query.filter_by(user_id=user_id).delete()
            for s in set(want_skills):
                db.session.add(UserWantsToLearn(user_id=user_id, skill_name=s))
            db.session.commit()

            # 2. Identify new unverified skills from 'have_skills'
            new_skills = [s for s in set(have_skills) if s not in verified_skill_names]

            if new_skills:
                session['pending_skills'] = new_skills
                session['pending_skills_index'] = 0
                return redirect(url_for('take_test'))
            else:
                flash('Skills updated successfully! No new skills to test.', 'success')
                return redirect(url_for('dashboard'))

        if 'refresh_matches' in request.form:
            return redirect(url_for('dashboard'))

    # Load matches, pending requests, and accepted connections
    matches = find_mutual_matches(user_id)
    pending_requests = get_pending_received_requests(user_id)
    accepted_connections = get_accepted_connections(user_id)

    return render_template(
        'dashboard.html',
        user=user,
        all_skills=all_skills,
        user_skills=user_skills,
        verified_skill_names=verified_skill_names,
        wants_skill_names=wants_skill_names,
        matches=matches,
        pending_requests=pending_requests,
        accepted_connections=accepted_connections
    )


# -------------------------------------------------------------
# CONNECTION REQUESTS
# -------------------------------------------------------------

@app.route('/request/send/<int:to_user_id>')
@login_required
def send_request(to_user_id):
    user_id = session['user_id']
    if to_user_id == user_id:
        flash('You cannot send a connection request to yourself.', 'warning')
        return redirect(url_for('dashboard'))

    # Check if request already exists
    existing = ConnectionRequest.query.filter_by(
        from_user_id=user_id,
        to_user_id=to_user_id
    ).first()

    if not existing:
        req = ConnectionRequest(
            from_user_id=user_id,
            to_user_id=to_user_id,
            status='pending'
        )
        db.session.add(req)
        db.session.commit()
        flash('Connection request sent!', 'success')
    else:
        flash('Connection request already exists.', 'info')

    return redirect(url_for('dashboard'))


@app.route('/request/accept/<int:request_id>')
@login_required
def accept_request(request_id):
    user_id = session['user_id']
    req = ConnectionRequest.query.filter_by(
        id=request_id,
        to_user_id=user_id,
        status='pending'
    ).first()

    if req:
        req.status = 'accepted'
        db.session.commit()
        flash('Connection request accepted! Contact details are now unlocked.', 'success')
    else:
        flash('Request not found or already processed.', 'warning')

    return redirect(url_for('dashboard'))


# -------------------------------------------------------------
# SKILL VERIFICATION TEST (GEMINI + OFFLINE FALLBACK)
# -------------------------------------------------------------

@app.route('/take-test', methods=['GET', 'POST'])
@login_required
def take_test():
    pending_skills = session.get('pending_skills', [])
    current_index = session.get('pending_skills_index', 0)

    if not pending_skills or current_index >= len(pending_skills):
        session.pop('pending_skills', None)
        session.pop('pending_skills_index', None)
        session.pop('current_questions', None)
        return redirect(url_for('dashboard'))

    current_skill = pending_skills[current_index]

    if request.method == 'GET':
        # Generate 5 MCQs using Gemini or fallback
        questions = generate_mcqs_with_gemini(current_skill)
        session['current_questions'] = questions

    questions = session.get('current_questions', [])

    if request.method == 'POST':
        score = 0
        results = []

        for i in range(len(questions)):
            user_ans_str = request.form.get(f'q{i}')
            user_ans = int(user_ans_str) if user_ans_str is not None and user_ans_str.isdigit() else -1
            correct_ans = questions[i].get('correct', 0)
            is_correct = (user_ans == correct_ans)
            if is_correct:
                score += 1

            results.append({
                'question': questions[i].get('question', ''),
                'user_answer': user_ans,
                'correct_answer': correct_ans,
                'is_correct': is_correct,
                'options': questions[i].get('options', [])
            })

        session['test_results'] = {
            'skill': current_skill,
            'score': score,
            'total': len(questions),
            'rating': score,  # Rating 1-5 equal to score
            'passed': score >= 3,
            'results': results
        }
        return redirect(url_for('test_result'))

    return render_template(
        'take_test.html',
        current_skill=current_skill,
        current_index=current_index,
        total_skills=len(pending_skills),
        questions=questions
    )


@app.route('/test-result', methods=['GET', 'POST'])
@login_required
def test_result():
    results_data = session.get('test_results')
    if not results_data:
        return redirect(url_for('dashboard'))

    user_id = session['user_id']
    skill = results_data['skill']
    score = results_data['score']
    rating = results_data['rating']
    passed = results_data['passed']

    # Auto-save verified skill if passed
    if passed:
        existing = UserSkill.query.filter_by(user_id=user_id, skill_name=skill).first()
        if not existing:
            new_us = UserSkill(user_id=user_id, skill_name=skill, rating=rating)
            db.session.add(new_us)
        else:
            existing.rating = max(existing.rating, rating)
        
        # Update user's aggregate skill rating
        user = db.session.get(User, user_id)
        if user:
            all_ratings = [s.rating for s in UserSkill.query.filter_by(user_id=user_id).all()]
            if all_ratings:
                user.skill_rating = round(sum(all_ratings) / len(all_ratings), 1)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')
        pending_skills = session.get('pending_skills', [])
        current_index = session.get('pending_skills_index', 0)

        session.pop('test_results', None)
        session.pop('current_questions', None)

        if action == 'next' or (action == 'dashboard' and current_index + 1 < len(pending_skills)):
            session['pending_skills_index'] = current_index + 1
            if session['pending_skills_index'] < len(pending_skills):
                return redirect(url_for('take_test'))

        # Finished all tests or user chose to go to dashboard
        session.pop('pending_skills', None)
        session.pop('pending_skills_index', None)
        return redirect(url_for('dashboard'))

    has_more_skills = False
    pending_skills = session.get('pending_skills', [])
    current_index = session.get('pending_skills_index', 0)
    if current_index + 1 < len(pending_skills):
        has_more_skills = True

    return render_template(
        'test_result.html',
        skill=skill,
        score=score,
        total=results_data.get('total', 5),
        rating=rating,
        passed=passed,
        has_more_skills=has_more_skills,
        results=results_data.get('results', [])
    )


# -------------------------------------------------------------
# API HELPERS
# -------------------------------------------------------------

@app.route('/api/skills')
def api_skills():
    skills = [s.skill_name for s in Skill.query.order_by(Skill.skill_name).all()]
    return jsonify({'skills': skills})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1']
    app.run(host='0.0.0.0', port=port, debug=debug)
