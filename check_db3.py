import sqlite3
conn = sqlite3.connect("/app/data/channels.db")
c = conn.cursor()
print("ORPHANED VIDEOS (channel deleted but videos remain):")
for r in c.execute("""
    SELECT v.channel_id, v.status, COUNT(*) as cnt, 
           GROUP_CONCAT(DISTINCT v.title) as sample_titles
    FROM videos v 
    LEFT JOIN channels c ON v.channel_id = c.id 
    WHERE c.id IS NULL 
    GROUP BY v.channel_id, v.status
"""):
    print(f"  channel_id={r[0]}: {r[1]} = {r[2]}")
    titles = r[3].split(",")[:3]
    for t in titles:
        print(f"    - {t}")
