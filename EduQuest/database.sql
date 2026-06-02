
-- EduQuest Database Schema

CREATE DATABASE IF NOT EXISTS eduquest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eduquest;

-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin') DEFAULT 'student',
    total_xp INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Courses Table
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    description TEXT,
    content TEXT,
    difficulty ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
    is_paid BOOLEAN DEFAULT FALSE,
    required_xp INT DEFAULT 0,
    xp_reward INT DEFAULT 100,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_difficulty (difficulty),
    INDEX idx_required_xp (required_xp)
);

-- Enrollments Table
CREATE TABLE enrollments (
    enroll_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    progress DECIMAL(5,2) DEFAULT 0.00,
    status ENUM('active', 'completed') DEFAULT 'active',
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (user_id, course_id),
    INDEX idx_user_status (user_id, status)
);

-- Lessons Table
CREATE TABLE lessons (
    lesson_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    lesson_order INT DEFAULT 0,
    lesson_type ENUM('text', 'video', 'exercise') DEFAULT 'text',
    xp_reward INT DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    INDEX idx_course_order (course_id, lesson_order)
);

-- Quizzes Table
CREATE TABLE quizzes (
    quiz_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    lesson_id INT NULL,
    question TEXT NOT NULL,
    opt_a VARCHAR(255) NOT NULL,
    opt_b VARCHAR(255) NOT NULL,
    opt_c VARCHAR(255) NOT NULL,
    opt_d VARCHAR(255) NOT NULL,
    correct_opt ENUM('A', 'B', 'C', 'D') NOT NULL,
    -- xp_reward INT DEFAULT 10,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    INDEX idx_course (course_id),
    INDEX idx_lesson (lesson_id)
);

-- Lesson Progress Table
CREATE TABLE lesson_progress (
    progress_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    lesson_id INT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_lesson (user_id, lesson_id),
    INDEX idx_user (user_id)
);

-- Badges Table
CREATE TABLE badges (
    badge_id INT AUTO_INCREMENT PRIMARY KEY,
    badge_name VARCHAR(50) NOT NULL,
    description TEXT,
    required_xp INT NOT NULL,
    icon VARCHAR(100) DEFAULT '🏆',
    INDEX idx_required_xp (required_xp)
);

-- User Badges Table
CREATE TABLE user_badges (
    user_badge_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    badge_id INT NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_badge (user_id, badge_id),
    INDEX idx_user (user_id)
);

-- XP System Table
CREATE TABLE xp_system (
    xp_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT,
    xp_earned INT NOT NULL,
    activity_type VARCHAR(50),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_earned_at (earned_at)
);

-- Leaderboard Table
CREATE TABLE leaderboard (
    leaderboard_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_xp INT NOT NULL,
    `rank` INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user (user_id),
    INDEX idx_rank (`rank`),
    INDEX idx_total_xp (total_xp DESC)
);

-- Insert Default Badges
INSERT INTO badges (badge_name, description, required_xp, icon) VALUES
('Getting Started', 'New Adventurer', 0, '🌱'),
('Beginner', 'Complete you First Course', 165, '🚀'),
('Knowledge Seeker', 'Reach 250 XP', 250, '📝'),
('Learner', 'Reach 500 XP', 500, '📚'),
('Sharp Mind','Reach 750 XP',750,'💡'),
('Expert', 'Reach 1000 XP', 1000, '🎓'),
('Master', 'Reach 1500 XP', 1500, '👑'),
('Master Mind', 'Reach 2000 XP', 2000, '🏅'),
('Legend', 'Reach 3500 XP', 3500, '⭐'),
('Learning Warrior', 'Reach 5000 XP', 5000, '⚔️');

-- Insert Sample Courses
INSERT INTO courses (course_name, description, content, difficulty, is_paid, required_xp, xp_reward) VALUES
('Python Basics', 'Learn the fundamentals of Python programming', 'Introduction to Python, variables, data types, and control structures.', 'beginner', FALSE, 0, 100);

-- Insert Sample Quizzes
INSERT INTO quizzes (course_id, lesson_id, question, opt_a, opt_b, opt_c, opt_d, correct_opt) VALUES
(1, NULL, 'What is the correct file extension for Python files?', '.py', '.python', '.pt', '.pyt', 'A');

-- Insert Sample Lessons
INSERT INTO lessons (course_id, title, content, lesson_order, lesson_type, xp_reward) VALUES
(1, 'Introduction to Python', 
'<h3>Welcome to Python!</h3><p>Python is a versatile programming language used for web development, data science, automation, and more.</p><h4>Exercise:</h4><p>Write your first Python program:</p><pre>print("Hello, World!")</pre><p>Try running this in your Python environment!</p>', 1, 'exercise', 20),
(1, 'Variables and Data Types', '<h3>Python Variables</h3><p>Variables store data values. Python has no command for declaring a variable - you just assign a value!</p><pre>x = 5\nname = "John"\nis_student = True</pre><h4>Data Types:</h4><ul><li>int - Integer numbers</li><li>float - Decimal numbers</li><li>str - Text strings</li><li>bool - True/False</li></ul><h4>Exercise:</h4><p>Create variables for your name, age, and favorite color. Print them all!</p>', 2, 'exercise', 20),
(1, 'Control Flow', '<h3>If Statements and Loops</h3><p>Control the flow of your program with conditions and loops.</p><h4>If Statement:</h4><pre>age = 18\nif age >= 18:\n    print("Adult")\nelse:\n    print("Minor")</pre><h4>For Loop:</h4><pre>for i in range(1, 11):\n    print(i)</pre><h4>Exercise:</h4><p>Write a program that prints numbers 1-10, but prints "Fizz" for multiples of 3 and "Buzz" for multiples of 5.</p>', 3, 'exercise', 25);