import datetime
import glob
import os
import random
import shutil
import sqlite3

SOURCE_DB = "database/main.db"
BACKUPS_DIR = "database/backup"


def init_source_db():
    """Initializes the mock source database with some dummy data."""
    os.makedirs(os.path.dirname(SOURCE_DB), exist_ok=True)
    if os.path.exists(SOURCE_DB):
        os.remove(SOURCE_DB)

    conn = sqlite3.connect(SOURCE_DB)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Insert dummy data
    for i in range(1, 101):
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (f"user{i}", f"user{i}@example.com"),
        )

    for i in range(1, 501):
        user_id = random.randint(1, 100)
        amount = round(random.uniform(10.0, 500.0), 2)
        cursor.execute(
            "INSERT INTO transactions (user_id, amount) VALUES (?, ?)",
            (user_id, amount),
        )

    conn.commit()
    conn.close()
    print(f"Initialized source database '{SOURCE_DB}'.")


def create_backup():
    """Creates a backup of the source database. Sometimes corrupts it on purpose."""
    if not os.path.exists(SOURCE_DB):
        init_source_db()

    if not os.path.exists(BACKUPS_DIR):
        os.makedirs(BACKUPS_DIR)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUPS_DIR, backup_filename)

    # Copy the database
    shutil.copy2(SOURCE_DB, backup_path)
    print(f"Created backup '{backup_filename}'.")

    # 60% chance to corrupt the backup to simulate a failure
    rand_val = random.random()
    if rand_val < 0.6:
        corrupt_backup(backup_path, rand_val)


def corrupt_backup(backup_path, rand_val=None):
    """Simulates a backup failure by deleting data or tables."""
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()

    if rand_val is None:
        rand_val = random.random()

    try:
        if rand_val < 0.15:
            # Drop a table
            cursor.execute("DROP TABLE users")
            print(f"CORRUPTION: Dropped the 'users' table in '{backup_path}'.")
        elif rand_val < 0.30:
            # Empty a table
            cursor.execute("DELETE FROM transactions")
            print(f"CORRUPTION: Emptied the 'transactions' table in '{backup_path}'.")
        elif rand_val < 0.45:
            # Delete rows
            cursor.execute("DELETE FROM transactions WHERE id % 2 = 0")
            print(f"CORRUPTION: Deleted half the rows from transactions in '{backup_path}'.")
        elif rand_val < 0.55:
            # Nullify data / Negative data
            cursor.execute("UPDATE transactions SET amount = -500 WHERE id % 3 = 0")
            print(f"CORRUPTION: Set negative transaction amounts in '{backup_path}'.")
        else:
            # Duplicate rows
            cursor.execute("INSERT INTO users (username, email) SELECT username, email FROM users LIMIT 10")
            print(f"CORRUPTION: Duplicated 10 users in '{backup_path}'.")

        conn.commit()
    except Exception as e:
        print(f"Error corrupting backup: {e}")
    finally:
        conn.close()


def cleanup_old_backups(keep=7):
    """Deletes old backups keeping only the most recent 'keep' files. Also deletes sandbox."""
    backups = sorted(glob.glob(os.path.join(BACKUPS_DIR, "*.db")), key=os.path.getmtime, reverse=True)
    
    # Delete older backups
    for old_backup in backups[keep:]:
        try:
            os.remove(old_backup)
            print(f"Deleted old backup: {old_backup}")
        except Exception as e:
            print(f"Failed to delete {old_backup}: {e}")
            
    # Clean sandbox database
    sandbox_db = "database/sandbox/sandbox_database.db"
    if os.path.exists(sandbox_db):
        try:
            os.remove(sandbox_db)
            print(f"Cleaned up sandbox database.")
        except Exception as e:
            pass



if __name__ == "__main__":
    init_source_db()
    # Create 3 backups for testing
    for _ in range(3):
        create_backup()
