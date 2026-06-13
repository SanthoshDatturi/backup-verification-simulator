import sqlite3
import os
import shutil
import random
import datetime

SOURCE_DB = "main.db"
BACKUPS_DIR = "backups"

def init_source_db():
    """Initializes the mock source database with some dummy data."""
    if os.path.exists(SOURCE_DB):
        os.remove(SOURCE_DB)
        
    conn = sqlite3.connect(SOURCE_DB)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Insert dummy data
    for i in range(1, 101):
        cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)", (f"user{i}", f"user{i}@example.com"))
        
    for i in range(1, 501):
        user_id = random.randint(1, 100)
        amount = round(random.uniform(10.0, 500.0), 2)
        cursor.execute("INSERT INTO transactions (user_id, amount) VALUES (?, ?)", (user_id, amount))
        
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
    
    # 30% chance to corrupt the backup to simulate a failure
    if random.random() < 0.3:
        corrupt_backup(backup_path)

def corrupt_backup(backup_path):
    """Simulates a backup failure by deleting data or tables."""
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()
    
    corruption_type = random.choice(['delete_rows', 'drop_table', 'empty_table'])
    
    try:
        if corruption_type == 'delete_rows':
            # Delete half the transactions
            cursor.execute("DELETE FROM transactions WHERE id % 2 = 0")
            print(f"CORRUPTION: Deleted half the rows from transactions in '{backup_path}'.")
        elif corruption_type == 'drop_table':
            cursor.execute("DROP TABLE users")
            print(f"CORRUPTION: Dropped the 'users' table in '{backup_path}'.")
        elif corruption_type == 'empty_table':
            cursor.execute("DELETE FROM transactions")
            print(f"CORRUPTION: Emptied the 'transactions' table in '{backup_path}'.")
        
        conn.commit()
    except Exception as e:
        print(f"Error corrupting backup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_source_db()
    # Create 3 backups for testing
    for _ in range(3):
        create_backup()
