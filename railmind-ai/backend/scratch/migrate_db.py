import sqlite3

def migrate():
    db_path = "railmind.db"
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(block_plans)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'safety_report_data' not in columns:
            cursor.execute("ALTER TABLE block_plans ADD COLUMN safety_report_data JSON;")
            print("Successfully added safety_report_data column to block_plans.")
        else:
            print("Column safety_report_data already exists.")
        
        conn.commit()
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
