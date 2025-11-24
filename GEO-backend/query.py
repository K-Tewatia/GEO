import sqlite3

DB_PATH = "brand_visibility.db"   # your database file

def clear_all_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for (table_name,) in tables:
        # Skip SQLite internal metadata tables
        if table_name.startswith("sqlite_"):
            continue
        
        try:
            cursor.execute(f"DELETE FROM {table_name};")
            print(f"Cleared table: {table_name}")
        except Exception as e:
            print(f"Error clearing table {table_name}: {e}")

    conn.commit()
    conn.close()
    print("\nAll tables cleared successfully.")


if __name__ == "__main__":
    clear_all_tables(DB_PATH)
