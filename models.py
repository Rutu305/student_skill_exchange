from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

DEFAULT_SKILLS = [
    'Java', 'Python', 'JavaScript', 'PHP', 'HTML/CSS', 
    'React', 'Node.js', 'MySQL', 'UI/UX Design', 
    'Graphic Design', 'English Speaking', 'Spanish', 'French'
]

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    # Using 'class' as column name in the database for full parity with the PHP schema
    class_name = db.Column('class', db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    skill_rating = db.Column(db.Numeric(3, 1), default=0.0)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    verified_skills = db.relationship('UserSkill', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    wants_to_learn = db.relationship('UserWantsToLearn', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        # Support both Werkzeug hashes and PHP's native bcrypt $2y$ hashes
        if self.password.startswith('$2y$') or self.password.startswith('$2a$') or self.password.startswith('$2b$'):
            try:
                # Convert $2y$ prefix to $2b$ for python-bcrypt compatibility if needed
                hash_bytes = self.password.replace('$2y$', '$2b$').encode('utf-8')
                return bcrypt.checkpw(raw_password.encode('utf-8'), hash_bytes)
            except Exception:
                pass
        return check_password_hash(self.password, raw_password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'class': self.class_name,
            'gender': self.gender,
            'email': self.email,
            'phone': self.phone,
            'skill_rating': float(self.skill_rating or 0.0)
        }


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_name = db.Column(db.String(100), unique=True, nullable=False)


class UserSkill(db.Model):
    __tablename__ = 'user_skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating from 1 to 5


class UserWantsToLearn(db.Model):
    __tablename__ = 'user_wants_to_learn'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)


class ConnectionRequest(db.Model):
    __tablename__ = 'connection_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted'
    created_at = db.Column(db.DateTime, default=utc_now)

    # User references
    sender = db.relationship('User', foreign_keys=[from_user_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[to_user_id], backref='received_requests')


def seed_database():
    """Initializes tables and seeds default skills if not present."""
    db.create_all()
    for skill_name in DEFAULT_SKILLS:
        existing = Skill.query.filter_by(skill_name=skill_name).first()
        if not existing:
            db.session.add(Skill(skill_name=skill_name))
    db.session.commit()
