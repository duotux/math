from datetime import datetime, timezone
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10))  # student/teacher
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    answers = db.relationship('AnswerRecord', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expression = db.Column(db.String(200))
    answer = db.Column(db.Float)
    records = db.relationship('AnswerRecord', backref='problem_ref', lazy='dynamic')

class AnswerRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'))
    user_answer = db.Column(db.Float)
    is_correct = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))