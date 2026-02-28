import sqlite3

db = sqlite3.connect("/app/data/channels.db")
# Reset all videos so they get re-downloaded properly
count = db.execute("UPDATE videos SET status = 'pending', error_message = NULL WHERE status IN ('downloaded', 'failed', 'downloading')").rowcount
# Also clear the archive file so yt-dlp doesn't skip them
db.commit()
print(f"Reset {count} videos to pending")
db.close()

import os
# Remove archive files so yt-dlp retries
for root, dirs, files in os.walk("/downloads"):
    for f in files:
        if f == ".yt-dlp-archive.txt":
            path = os.path.join(root, f)
            os.remove(path)
            print(f"Removed archive: {path}")
