import sqlite3

db = sqlite3.connect("/app/data/channels.db")
count = db.execute("UPDATE videos SET status = 'pending', error_message = NULL WHERE status = 'failed'").rowcount
db.commit()
print(f"Reset {count} failed videos to pending")
db.close()
