import sqlite3
conn = sqlite3.connect("/app/data/channels.db")
c = conn.cursor()
print("STATUS COUNTS")
for r in c.execute("SELECT status, COUNT(*) FROM videos GROUP BY status"):
    print(r)
print("LAST 20 DOWNLOADED")
for r in c.execute("SELECT title, status FROM videos WHERE status='downloaded' ORDER BY rowid DESC LIMIT 20"):
    print(r)
print("STUCK DOWNLOADING")
for r in c.execute("SELECT title, status FROM videos WHERE status='downloading'"):
    print(r)
