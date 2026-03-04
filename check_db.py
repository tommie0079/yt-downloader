import sqlite3
db = sqlite3.connect('/app/data/channels.db')
c = db.execute('SELECT status, COUNT(1) FROM videos GROUP BY status')
for row in c.fetchall():
    print(row)
c2 = db.execute('SELECT title, status FROM videos')
for row in c2.fetchall():
    print(row)
