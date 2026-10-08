# SkillSwap — Student Skill Exchange Platform (Flask Edition)

A modern, full-featured Python Flask application converted from the legacy PHP implementation with enhanced security, robust validations, responsive UI, and AI-assisted skill verification quizzes.

---

## 🌟 Key Features

1. **Robust Dual-Layer Validations (Client & Server-Side)**
   - **Full Name**: 2–60 characters, alphabetic letters, spaces, hyphens, apostrophes only.
   - **Academic Class**: 2–50 characters, alphanumeric with standard formatting.
   - **Strict Whitelist Gender**: Male, Female, Other.
   - **Email**: RFC-compliant regex, unique check against database.
   - **Phone**: Exactly 10 digits, blocks non-numeric inputs and trivial repeating numbers (`0000000000`, `1111111111`).
   - **Strong Password Policy**:
     - Minimum 8 characters (up to 128)
     - At least 1 uppercase letter (`A-Z`)
     - At least 1 lowercase letter (`a-z`)
     - At least 1 number (`0-9`)
     - At least 1 special character (`@$!%*?&#^()_+-=...`)
     - Visual real-time password strength meter (Red: Weak → Orange: Medium → Green: Strong)
     - Live checklist and password confirmation matching verification.

2. **Skill Management & Verification Tests**
   - **Catalog of Skills**: Java, Python, JavaScript, PHP, HTML/CSS, React, Node.js, MySQL, UI/UX Design, Graphic Design, English Speaking, Spanish, French.
   - **AI-Powered Quizzes**: 5 MCQs generated via Google Gemini 2.5 Flash API with intelligent automatic fallback to rich offline question banks.
   - **Pass/Fail Threshold**: Scoring 3/5 or higher unlocks the verified skill badge and updates aggregate student rating (1.0–5.0).
   - **Conflict Prevention**: Students cannot mark already-verified skills as "want to learn".

3. **Intelligent Peer Matching & Safe Connections**
   - **Mutual Skill Exchange Algorithm**: User A has skills User B wants, and User B has skills User A wants.
   - **Affinity Match Score**: Visual percentage match indicator (e.g., 94% Match 🔥).
   - **Privacy First**: Contact details (email and mobile phone) are kept hidden until a mutual connection request is accepted.

4. **Zero-Configuration Execution**
   - Defaults to SQLite (`skillswap.db`) out-of-the-box so you can clone and run immediately without needing XAMPP or MySQL running.
   - Seamlessly supports MySQL via `.env` or `DATABASE_URL` if MySQL/phpMyAdmin is preferred.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.13)
- pip

### 2. Setup Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
*(Optionally provide your own Google Gemini API key in `.env` if desired)*

### 5. Run the Application
```bash
python app.py
```
Open your browser at: **`http://127.0.0.1:5000/`**

---

## 🧪 Running Automated Tests
Run the test suite with pytest:
```bash
python -m pytest tests/test_app.py -v
```

---

## 📁 Project Structure

```
student_skill_exchange/
├── app.py                 # Core Flask routes & application logic
├── models.py              # SQLAlchemy database models & auto-seeder
├── validators.py          # Centralized strong validation helpers
├── matcher.py             # Mutual skill matching & connection logic
├── gemini_service.py      # Gemini API & offline MCQ question banks
├── config.py              # App, DB, and API configurations
├── requirements.txt       # Python package dependencies
├── .env.example           # Environment variables template
├── static/
│   └── css/
│       └── style.css      # Modern responsive design system
├── templates/
│   ├── base.html          # Layout shell with navigation & flashes
│   ├── index.html         # Landing hero & features
│   ├── login.html         # Secure login page
│   ├── register.html      # Registration with live validation & strength meter
│   ├── forgot_password.html # Account verification
│   ├── reset_password.html  # Secure password reset
│   ├── dashboard.html     # Skills management, peer matches, connections
│   ├── take_test.html     # Interactive MCQ quiz interface
│   └── test_result.html   # Score circle, rating stars, breakdown
└── tests/
    └── test_app.py        # Automated test suite (100% pass)
```
