import sqlite3
db = sqlite3.connect('/app/data/channels.db')
# Reset stuck 'downloading' to 'pending' so they get retried
db.execute("UPDATE videos SET status = 'pending' WHERE status = 'downloading'")
# Reset 'failed' to 'pending' so they get retried on next scan
db.execute("UPDATE videos SET status = 'pending', error_message = NULL WHERE status = 'failed'")
db.commit()
c = db.execute('SELECT status, COUNT(1) FROM videos GROUP BY status')
for row in c.fetchall():
    print(row)
print('Done - all stuck/failed videos reset to pending')
