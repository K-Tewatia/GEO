import sqlite3

db_path = "brand_visibility.db"  # Your DB file path

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute()
conn.commit()
conn.close()

print("Backfill update of llmname for old analyses completed.")
