import sqlite3
conn = sqlite3.connect("/app/data/channels.db")
c = conn.cursor()
print("PER CHANNEL STATUS")
for r in c.execute("SELECT channel_id, status, COUNT(*) as cnt FROM videos GROUP BY channel_id, status ORDER BY channel_id, status"):
    print(f"  channel {r[0]}: {r[1]} = {r[2]}")
print()
print("CHANNELS")
for r in c.execute("SELECT id, name FROM channels"):
    print(f"  id={r[0]} name={r[1]}")
