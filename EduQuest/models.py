from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'admin'), default='student')
    total_xp = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    enrollments = db.relationship('Enrollment', backref='user', lazy=True, cascade='all, delete-orphan')
    xp_transactions = db.relationship('XPSystem', backref='user', lazy=True, cascade='all, delete-orphan')
    user_badges = db.relationship('UserBadge', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def get_id(self):
        return str(self.user_id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    __tablename__ = 'courses'
    
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    difficulty = db.Column(db.Enum('beginner', 'intermediate', 'advanced'), default='beginner')
    is_paid = db.Column(db.Boolean, default=False)
    required_xp = db.Column(db.Integer, default=0)
    xp_reward = db.Column(db.Integer, default=100)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy=True, cascade='all, delete-orphan')
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade='all, delete-orphan')
    
class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    lesson_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_order = db.Column(db.Integer, default=0)
    lesson_type = db.Column(db.Enum('text', 'video', 'exercise'), default='text')
    xp_reward = db.Column(db.Integer, default=20)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    progress = db.relationship('LessonProgress', backref='lesson', lazy=True, cascade='all, delete-orphan')

class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'
    
    progress_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='lesson_progress')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    enroll_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    progress = db.Column(db.Numeric(5, 2), default=0.00)
    status = db.Column(db.Enum('active', 'completed'), default='active')
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    quiz_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    opt_a = db.Column(db.String(255), nullable=False)
    opt_b = db.Column(db.String(255), nullable=False)
    opt_c = db.Column(db.String(255), nullable=False)
    opt_d = db.Column(db.String(255), nullable=False)
    correct_opt = db.Column(db.Enum('A', 'B', 'C', 'D'), nullable=False)
    # xp_reward = db.Column(db.Integer, default=10)
    
    lesson = db.relationship('Lesson', backref='quizzes')

class Badge(db.Model):
    __tablename__ = 'badges'
    
    badge_id = db.Column(db.Integer, primary_key=True)
    badge_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    required_xp = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(100), default='🏆')
    
    user_badges = db.relationship('UserBadge', backref='badge', lazy=True, cascade='all, delete-orphan')

class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    
    user_badge_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.badge_id'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

class XPSystem(db.Model):
    __tablename__ = 'xp_system'
    
    xp_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    xp_earned = db.Column(db.Integer, nullable=False)
    activity_type = db.Column(db.String(50))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    
    leaderboard_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_xp = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='leaderboard_entry')

