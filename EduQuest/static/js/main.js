// EduQuest JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Progress circles animation
    const progressCircles = document.querySelectorAll('.progress-circle');
    progressCircles.forEach(circle => {
        const progress = circle.getAttribute('data-progress');
        circle.style.background = `conic-gradient(#4f46e5 ${progress * 3.6}deg, #f3f4f6 0deg)`;
    });
    
    // Course enrollment confirmation
    const enrollButtons = document.querySelectorAll('.enroll-btn');
    enrollButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const courseName = this.getAttribute('data-course-name');
            if (!confirm(`Enroll in ${courseName}?`)) {
                e.preventDefault();
            }
        });
    });
    
    // Quiz timer (optional)
    const quizForm = document.querySelector('.quiz-form');
    if (quizForm) {
        let timeLeft = 300; // 5 minutes
        const timerDisplay = document.getElementById('quiz-timer');
        
        if (timerDisplay) {
            const timer = setInterval(() => {
                timeLeft--;
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 0) {
                    clearInterval(timer);
                    alert('Time is up!');
                    quizForm.submit();
                }
            }, 1000);
        }
    }
    
    // Smooth scroll to sections
    const scrollLinks = document.querySelectorAll('a[href^="#"]');
    scrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// XP Animation
function animateXP(element, targetValue) {
    let currentValue = 0;
    const increment = targetValue / 50;
    const timer = setInterval(() => {
        currentValue += increment;
        if (currentValue >= targetValue) {
            currentValue = targetValue;
            clearInterval(timer);
        }
        element.textContent = Math.floor(currentValue);
    }, 20);
}

// Badge unlock animation
function unlockBadge(badgeElement) {
    badgeElement.classList.add('earned');
    badgeElement.style.animation = 'bounceIn 1s';
}

// Leaderboard live updates (if using WebSocket)
function updateLeaderboard(data) {
    const leaderboardBody = document.querySelector('#leaderboard-body');
    if (leaderboardBody) {
        leaderboardBody.innerHTML = data.map((user, index) => `
            <tr class="leaderboard-row">
                <td class="leaderboard-rank">${index + 1}</td>
                <td>${user.username}</td>
                <td><span class="xp-badge">${user.total_xp} XP</span></td>
            </tr>
        `).join('');
    }
}

// Theme toggle functionality
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const html = document.documentElement;

// Load saved theme or default to light
const currentTheme = localStorage.getItem('theme') || 'light';
html.setAttribute('data-theme', currentTheme);
updateThemeIcon(currentTheme);

themeToggle?.addEventListener('click', () => {
    const theme = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
});

function updateThemeIcon(theme) {
    if (themeIcon) {
        themeIcon.className = theme === 'light' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
    }
}
