
from models import db, User, Course, Enrollment, Quiz, Badge, UserBadge, XPSystem, Leaderboard, Lesson, LessonProgress
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config.from_object(Config)
app.config['JSON_AS_ASCII'] = False
# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ============ AUTHENTICATION ROUTES ============

@app.route('/')
def index():
    courses = Course.query.all()  # Fetch all courses
    return render_template('index.html', courses=courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        check_badge_unlock(user.user_id)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page or url_for('admin_dashboard'))
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# ============ USER ROUTES ============

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    enrollments = Enrollment.query.filter_by(user_id=current_user.user_id).all()
    badges = UserBadge.query.filter_by(user_id=current_user.user_id).all()
    leaderboard_entry = Leaderboard.query.filter_by(user_id=current_user.user_id).first()
    recent_xp = XPSystem.query.filter_by(user_id=current_user.user_id).order_by(XPSystem.earned_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         enrollments=enrollments, 
                         badges=badges,
                         rank=leaderboard_entry.rank if leaderboard_entry else None,
                         recent_xp=recent_xp)

@app.route('/courses')
# @login_required
def courses():
    all_courses = Course.query.all()
    enrolled_course_ids = []
    if current_user.is_authenticated:
        enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(user_id=current_user.user_id).all()]
    return render_template('courses.html', courses=all_courses, enrolled_course_ids=enrolled_course_ids)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Check if user is enrolled
    enrollment = Enrollment.query.filter_by(user_id=current_user.user_id, course_id=course.course_id).first()
    if not enrollment:
        flash('You must be enrolled in this course to view lessons', 'error')
        return redirect(url_for('course_detail', course_id=course.course_id))
    
    # Get all lessons for navigation
    all_lessons = Lesson.query.filter_by(course_id=course.course_id).order_by(Lesson.lesson_order).all()
    
    # Check if lesson is completed
    progress = LessonProgress.query.filter_by(user_id=current_user.user_id, lesson_id=lesson_id).first()
    
    return render_template('lesson.html', 
                         lesson=lesson, 
                         course=course,
                         all_lessons=all_lessons,
                         progress=progress)

@app.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if already completed
    progress = LessonProgress.query.filter_by(user_id=current_user.user_id, lesson_id=lesson_id).first()
    
    if not progress:
        progress = LessonProgress(user_id=current_user.user_id, lesson_id=lesson_id)
    
    if not progress.completed:
        progress.completed = True
        progress.completed_at = datetime.utcnow()
        db.session.add(progress)
        
        # Award XP for lesson
        xp = XPSystem(
            user_id=current_user.user_id,
            course_id=lesson.course_id,
            xp_earned=lesson.xp_reward,
            activity_type='lesson_completion'
        )
        db.session.add(xp)
        
        current_user.total_xp += lesson.xp_reward
        
        # Update course progress
        enrollment = Enrollment.query.filter_by(user_id=current_user.user_id, course_id=lesson.course_id).first()
        if enrollment:
            total_lessons = Lesson.query.filter_by(course_id=lesson.course_id).count()
            completed_lessons = LessonProgress.query.filter_by(
                user_id=current_user.user_id,
                completed=True
            ).join(Lesson).filter(Lesson.course_id == lesson.course_id).count()
            
            enrollment.progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            
            # Auto-complete course and award course XP when 100% complete
            if enrollment.progress >= 100 and enrollment.status != 'completed':
                enrollment.status = 'completed'
                enrollment.completed_at = datetime.utcnow()
                
                course = Course.query.get(lesson.course_id)
                course_xp = XPSystem(
                    user_id=current_user.user_id,
                    course_id=lesson.course_id,
                    xp_earned=course.xp_reward,
                    activity_type='course_completion'
                )
                db.session.add(course_xp)
                current_user.total_xp += course.xp_reward
                
                flash(f'🎉 Course completed! +{course.xp_reward} XP earned for course completion!', 'success')
        
        db.session.commit()
        
        check_badge_unlock(current_user.user_id)
        update_leaderboard(current_user.user_id)
        
        flash(f'Lesson completed! +{lesson.xp_reward} XP earned', 'success')
    
    return redirect(url_for('view_lesson', lesson_id=lesson_id))


# Add admin routes for managing lessons

@app.route('/admin/course/<int:course_id>/lessons')
@login_required
@admin_required
def admin_course_lessons(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
    return render_template('admin/lessons.html', course=course, lessons=lessons)

@app.route('/admin/course/<int:course_id>/lesson/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        lesson = Lesson(
            course_id=course_id,
            title=request.form.get('title'),
            content=request.form.get('content'),
            lesson_order=int(request.form.get('lesson_order', 0)),
            lesson_type=request.form.get('lesson_type'),
            xp_reward=int(request.form.get('xp_reward', 20))
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash('Lesson added successfully', 'success')
        return redirect(url_for('admin_course_lessons', course_id=course_id))
    
    # Get next order number
    max_order = db.session.query(db.func.max(Lesson.lesson_order)).filter_by(course_id=course_id).scalar() or 0
    next_order = max_order + 1
    
    return render_template('admin/add_lesson.html', course=course, next_order=next_order)

@app.route('/admin/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)
    
    if request.method == 'POST':
        lesson.title = request.form.get('title')
        lesson.content = request.form.get('content')
        lesson.lesson_order = int(request.form.get('lesson_order'))
        lesson.lesson_type = request.form.get('lesson_type')
        lesson.xp_reward = int(request.form.get('xp_reward'))
        
        db.session.commit()
        
        flash('Lesson updated successfully', 'success')
        return redirect(url_for('admin_course_lessons', course_id=course.course_id))
    
    return render_template('admin/edit_lesson.html', lesson=lesson, course=course)

@app.route('/admin/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    
    db.session.delete(lesson)
    db.session.commit()
    
    flash('Lesson deleted successfully', 'success')
    return redirect(url_for('admin_course_lessons', course_id=course_id))


@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def quiz(quiz_id):
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        selected = request.form.get('answer')
        
        if selected == quiz_obj.correct_opt:
            if quiz_obj.lesson_id:
                # Check if lesson progress exists
                progress = LessonProgress.query.filter_by(
                    user_id=current_user.user_id, 
                    lesson_id=quiz_obj.lesson_id
                ).first()
                
                # Create progress if it doesn't exist
                if not progress:
                    progress = LessonProgress(
                        user_id=current_user.user_id, 
                        lesson_id=quiz_obj.lesson_id,
                        completed=False
                    )
                    db.session.add(progress)
                
                # Only award XP if not already completed
                if not progress.completed:
                    # Mark lesson as completed
                    progress.completed = True
                    progress.completed_at = datetime.utcnow()
                    
                    # Get lesson and award XP
                    lesson = Lesson.query.get(quiz_obj.lesson_id)
                    
                    # Add lesson XP
                    lesson_xp = XPSystem(
                        user_id=current_user.user_id,
                        course_id=lesson.course_id,
                        xp_earned=lesson.xp_reward,
                        activity_type='lesson_completion'
                    )
                    db.session.add(lesson_xp)
                    
                    # Update user total XP
                    current_user.total_xp += lesson.xp_reward
                    
                    # CRITICAL: Calculate and update course progress
                    enrollment = Enrollment.query.filter_by(
                        user_id=current_user.user_id, 
                        course_id=lesson.course_id
                    ).first()
                    
                    if enrollment:
                        # Count total lessons in course
                        total_lessons = Lesson.query.filter_by(
                            course_id=lesson.course_id
                        ).count()
                        
                        # Count completed lessons by this user in this course
                        completed_count = db.session.query(LessonProgress).join(
                            Lesson, LessonProgress.lesson_id == Lesson.lesson_id
                        ).filter(
                            LessonProgress.user_id == current_user.user_id,
                            LessonProgress.completed == True,
                            Lesson.course_id == lesson.course_id
                        ).count()
                        
                        # Calculate percentage
                        if total_lessons > 0:
                            enrollment.progress = round((completed_count / total_lessons) * 100, 2)
                        else:
                            enrollment.progress = 0
                        
                        # Check if course is now complete
                        if enrollment.progress >= 100 and enrollment.status != 'completed':
                            enrollment.status = 'completed'
                            enrollment.completed_at = datetime.utcnow()
                            
                            # Award course completion XP
                            course = Course.query.get(lesson.course_id)
                            course_xp = XPSystem(
                                user_id=current_user.user_id,
                                course_id=lesson.course_id,
                                xp_earned=course.xp_reward,
                                activity_type='course_completion'
                            )
                            db.session.add(course_xp)
                            current_user.total_xp += course.xp_reward
                            
                            flash(f'🎉 Course completed! +{course.xp_reward} XP bonus!', 'success')
                    
                    # Commit all changes to database
                    db.session.commit()
                    
                    # Update badges and leaderboard
                    check_badge_unlock(current_user.user_id)
                    update_leaderboard(current_user.user_id)
                    
                    flash(f'✅ Correct! Lesson completed! +{lesson.xp_reward} XP earned', 'success')
                else:
                    # Already completed
                    flash('✅ Correct! (Lesson already completed)', 'info')
                
                return redirect(url_for('view_lesson', lesson_id=quiz_obj.lesson_id))
            else:
                # Standalone quiz (no lesson)
                xp = XPSystem(
                    user_id=current_user.user_id,
                    course_id=quiz_obj.course_id,
                    xp_earned=quiz_obj.xp_reward,
                    activity_type='quiz_completion'
                )
                db.session.add(xp)
                current_user.total_xp += quiz_obj.xp_reward
                db.session.commit()
                
                check_badge_unlock(current_user.user_id)
                update_leaderboard(current_user.user_id)
                
                flash(f'✅ Correct! +{quiz_obj.xp_reward} XP earned', 'success')
                return redirect(url_for('course_detail', course_id=quiz_obj.course_id))
        else:
            flash('❌ Incorrect answer. Try again!', 'error')
    
    return render_template('quiz.html', quiz=quiz_obj)

@app.route('/admin/course/<int:course_id>/quizzes')
@login_required
@admin_required
def admin_course_quizzes(course_id):
    course = Course.query.get_or_404(course_id)
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    return render_template('admin/quizzes.html', course=course, quizzes=quizzes)

@app.route('/admin/course/<int:course_id>/quiz/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_quiz(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        lesson_id_value = request.form.get('lesson_id')
        
        quiz = Quiz(
            course_id=course_id,
            lesson_id=int(lesson_id_value) if lesson_id_value and lesson_id_value != '' else None,
            question=request.form.get('question'),
            opt_a=request.form.get('opt_a'),
            opt_b=request.form.get('opt_b'),
            opt_c=request.form.get('opt_c'),
            opt_d=request.form.get('opt_d'),
            correct_opt=request.form.get('correct_opt'),
            # xp_reward=int(request.form.get('xp_reward', 10))
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz added successfully and linked to lesson', 'success')
        return redirect(url_for('admin_course_quizzes', course_id=course_id))
    
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
    return render_template('admin/add_quiz.html', course=course, lessons=lessons)


@app.route('/admin/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get(quiz.course_id)
    
    if request.method == 'POST':
        quiz.lesson_id = int(request.form.get('lesson_id')) if request.form.get('lesson_id') else None
        quiz.question = request.form.get('question')
        quiz.opt_a = request.form.get('opt_a')
        quiz.opt_b = request.form.get('opt_b')
        quiz.opt_c = request.form.get('opt_c')
        quiz.opt_d = request.form.get('opt_d')
        quiz.correct_opt = request.form.get('correct_opt')
        # quiz.xp_reward = int(request.form.get('xp_reward'))
        
        db.session.commit()
        
        flash('Quiz updated successfully', 'success')
        return redirect(url_for('admin_course_quizzes', course_id=course.course_id))
    
    lessons = Lesson.query.filter_by(course_id=course.course_id).order_by(Lesson.lesson_order).all()
    return render_template('admin/edit_quiz.html', quiz=quiz, course=course, lessons=lessons)

@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course_id = quiz.course_id
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('admin_course_quizzes', course_id=course_id))


@app.route('/leaderboard')
@login_required
def leaderboard():
    top_users = Leaderboard.query.order_by(Leaderboard.rank.asc()).limit(100).all()
    return render_template('leaderboard.html', leaderboard=top_users)

@app.route('/profile')
@login_required
def profile():
    badges = UserBadge.query.filter_by(user_id=current_user.user_id).all()
    enrollments = Enrollment.query.filter_by(user_id=current_user.user_id).all()
    xp_history = XPSystem.query.filter_by(user_id=current_user.user_id).order_by(XPSystem.earned_at.desc()).limit(20).all()
    leaderboard_entry = Leaderboard.query.filter_by(user_id=current_user.user_id).first()
    
    return render_template('profile.html',
                         badges=badges,
                         enrollments=enrollments,
                         xp_history=xp_history,
                         rank=leaderboard_entry.rank if leaderboard_entry else None)

# ============ ADMIN ROUTES ============

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_courses=total_courses,
                         total_enrollments=total_enrollments,
                         recent_users=recent_users)

@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/course/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    if request.method == 'POST':
        course = Course(
            course_name=request.form.get('course_name'),
            description=request.form.get('description'),
            content=request.form.get('content'),
            difficulty=request.form.get('difficulty'),
            is_paid=bool(request.form.get('is_paid')),
            required_xp=int(request.form.get('required_xp', 0)),
            xp_reward=int(request.form.get('xp_reward', 100))
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course added successfully', 'success')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/add_course.html')

@app.route('/admin/course/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.course_name = request.form.get('course_name')
        course.description = request.form.get('description')
        course.content = request.form.get('content')
        course.difficulty = request.form.get('difficulty')
        course.is_paid = bool(request.form.get('is_paid'))
        course.required_xp = int(request.form.get('required_xp', 0))
        course.xp_reward = int(request.form.get('xp_reward', 100))
        
        db.session.commit()
        
        flash('Course updated successfully', 'success')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/course/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully', 'success')
    return redirect(url_for('admin_courses'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.user_id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    # Delete related leaderboard entry first to avoid FK constraint error
    Leaderboard.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin_users'))
@app.route('/course/<int:course_id>')
# @login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    enrollment = None
    can_access = True
    
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(user_id=current_user.user_id, course_id=course_id).first()
        
        # Recalculate progress if enrolled
        if enrollment:
            total_lessons = Lesson.query.filter_by(course_id=course_id).count()
            if total_lessons > 0:
                completed_count = db.session.query(LessonProgress).join(
                    Lesson, LessonProgress.lesson_id == Lesson.lesson_id
                ).filter(
                    LessonProgress.user_id == current_user.user_id,
                    LessonProgress.completed == True,
                    Lesson.course_id == course_id
                ).count()
                
                enrollment.progress = round((completed_count / total_lessons) * 100, 2)
                db.session.commit()
        
        can_access = current_user.total_xp >= course.required_xp
    
    # Get lessons to show titles
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
    quizzes = Quiz.query.filter_by(course_id=course_id, lesson_id=None).all()
    
    return render_template('course_detail.html', 
                         course=course, 
                         enrollment=enrollment, 
                         quizzes=quizzes,
                         lessons=lessons,
                         can_access=can_access)


@app.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if current_user.total_xp < course.required_xp:
        flash('You do not have enough XP to enroll in this course.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    existing = Enrollment.query.filter_by(user_id=current_user.user_id, course_id=course_id).first()
    if existing:
        flash('You are already enrolled in this course.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
    
    enrollment = Enrollment(user_id=current_user.user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    
    flash(f'Successfully enrolled in {course.course_name}!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))
@app.route('/toggle-student-view')
@login_required
def toggle_student_view():
    if current_user.role != 'admin':
        abort(403)
    session['preview_as_student'] = not session.get('preview_as_student', False)
    if session['preview_as_student']:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('admin_dashboard'))
@app.route('/course/<int:course_id>/complete', methods=['POST'])
@login_required
def complete_course(course_id):
    enrollment = Enrollment.query.filter_by(user_id=current_user.user_id, course_id=course_id).first_or_404()
    course = Course.query.get_or_404(course_id)
    
    if enrollment.status == 'completed':
        flash('You have already completed this course.', 'info')
        return redirect(url_for('course_detail', course_id=course_id))
    
    enrollment.status = 'completed'
    enrollment.progress = 100
    enrollment.completed_at = datetime.utcnow()
    
    xp = XPSystem(
        user_id=current_user.user_id,
        course_id=course_id,
        xp_earned=course.xp_reward,
        activity_type='course_completion'
    )
    db.session.add(xp)
    
    current_user.total_xp += course.xp_reward
    
    db.session.commit()
    
    check_badge_unlock(current_user.user_id)
    update_leaderboard(current_user.user_id)
    
    flash(f'Congratulations! Course completed. +{course.xp_reward} XP earned!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))
# ============ HELPER FUNCTIONS ============

def check_badge_unlock(user_id):
    user = User.query.get(user_id)
    badges = Badge.query.filter(Badge.required_xp <= user.total_xp).all()
    
    for badge in badges:
        existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.badge_id).first()
        if not existing:
            user_badge = UserBadge(user_id=user_id, badge_id=badge.badge_id)
            db.session.add(user_badge)
    
    db.session.commit()

def update_leaderboard(user_id):
    user = User.query.get(user_id)
    
    leaderboard_entry = Leaderboard.query.filter_by(user_id=user_id).first()
    if leaderboard_entry:
        leaderboard_entry.total_xp = user.total_xp
    else:
        leaderboard_entry = Leaderboard(user_id=user_id, total_xp=user.total_xp)
        db.session.add(leaderboard_entry)
    
    db.session.commit()
    
    # Update ranks
    all_entries = Leaderboard.query.order_by(Leaderboard.total_xp.desc()).all()
    for idx, entry in enumerate(all_entries, 1):
        entry.rank = idx
    
    db.session.commit()

# ====== Backfill badges for existing users ======
@app.route('/admin/backfill-badges')
@login_required
@admin_required
def backfill_badges():
    users = User.query.all()
    for user in users:
        check_badge_unlock(user.user_id)
    flash(f'Badges backfilled for {len(users)} users!', 'success')
    return redirect(url_for('admin_dashboard'))

# ============ DATABASE INITIALIZATION ============

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('✅ Database initialized!')
    
    # Create default admin if not exists
    admin = User.query.filter_by(email='admin@eduquest.com').first()
    if not admin:
        admin = User(username='admin', email='admin@eduquest.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Default admin created: admin@eduquest.com / admin123')
    
    # Create default badges if not exists
    if Badge.query.count() == 0:
        badges_data = [
            {'badge_name': 'Getting Started', 'description': 'New Adventurer', 'required_xp': 0, 'icon': '🌱'},
            {'badge_name': 'Beginner', 'description': 'Complete your First Course', 'required_xp': 165, 'icon': '🚀'},
            {'badge_name': 'Knowledge Seeker', 'description': 'Reach 250 XP', 'required_xp': 250, 'icon': '📋'},
            {'badge_name': 'Learner', 'description': 'Reach 500 XP', 'required_xp': 500, 'icon': '📊'},
            {'badge_name': 'Sharp Mind', 'description': 'Reach 750 XP', 'required_xp': 750, 'icon': '💡'},
            {'badge_name': 'Expert', 'description': 'Reach 1000 XP', 'required_xp': 1000, 'icon': '🎓'},
            {'badge_name': 'Master', 'description': 'Reach 1500 XP', 'required_xp': 1500, 'icon': '👑'},
            {'badge_name': 'Master Mind', 'description': 'Reach 2000 XP', 'required_xp': 2000, 'icon': '🥇'},
            {'badge_name': 'Legend', 'description': 'Reach 3500 XP', 'required_xp': 3500, 'icon': '⭐'},
            {'badge_name': 'Learning Warrior', 'description': 'Reach 5000 XP', 'required_xp': 5000, 'icon': '⚔️'},
        ]
        
        for badge_data in badges_data:
            badge = Badge(**badge_data)
            db.session.add(badge)
        
        db.session.commit()
        print('✅ Default badges created!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
