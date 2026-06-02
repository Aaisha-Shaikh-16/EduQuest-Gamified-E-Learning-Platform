from app import app, db, Course, Lesson, Quiz

with app.app_context():
    courses = Course.query.all()
    for course in courses:
        lessons = Lesson.query.filter_by(course_id=course.course_id).order_by(Lesson.lesson_order).all()
        quizzes = Quiz.query.filter_by(course_id=course.course_id, lesson_id=None).all()
        
        for idx, quiz in enumerate(quizzes):
            if idx < len(lessons):
                quiz.lesson_id = lessons[idx].lesson_id
                print(f"Linked quiz {quiz.quiz_id} to lesson {lessons[idx].lesson_id}")
        
        db.session.commit()
    print('✅ All quizzes linked to lessons!')