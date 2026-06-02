import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',          # your MySQL username
    password='Aaisha',    # your MySQL password
    db='eduquest',        # your database name
    charset='utf8mb4'
)

cursor = conn.cursor()

# Clear corrupted data
cursor.execute("DELETE FROM badges")

# Re-insert with correct emojis
badges = [
    ('Beginner', 'Complete your first course', 100, '🎖️'),
    ('Learner', 'Reach 500 XP', 500, '📚'),
    ('Expert', 'Reach 1000 XP', 1000, '🎓'),
    ('Master', 'Reach 2000 XP', 2000, '👑'),
    ('Legend', 'Reach 5000 XP', 5000, '⭐'),
]

cursor.executemany(
    "INSERT INTO badges (badge_name, description, required_xp, icon) VALUES (%s, %s, %s, %s)",
    badges
)

conn.commit()
cursor.close()
conn.close()
print("Done! Badges inserted successfully.")

import pymysql
conn = pymysql.connect(host='localhost', user='root', password='Aaisha', db='eduquest', charset='utf8mb4')
cursor = conn.cursor()
cursor.execute("SELECT badge_name, icon FROM badges")
for row in cursor.fetchall():
    print(row)