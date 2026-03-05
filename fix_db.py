import sqlite3
conn = sqlite3.connect("/app/data/channels.db")
c = conn.cursor()

# Delete orphaned videos (belong to deleted channels)
orphaned = c.execute("DELETE FROM videos WHERE channel_id NOT IN (SELECT id FROM channels)").rowcount
print(f"Deleted {orphaned} orphaned videos")

# Fix stuck downloading -> pending
stuck = c.execute("UPDATE videos SET status = 'pending' WHERE status = 'downloading'").rowcount
print(f"Reset {stuck} stuck downloading videos to pending")

conn.commit()

# Show final state
print("\nFINAL STATE:")
for r in c.execute("SELECT status, COUNT(*) FROM videos GROUP BY status"):
    print(f"  {r[0]} = {r[1]}")

conn.close()
