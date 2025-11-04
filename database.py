import sqlite3
from contextlib import contextmanager

DB_NAME = "todo.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        yield conn
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def create_table():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        table_exists = cur.fetchone()
        
        if not table_exists:
            cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            task TEXT NOT NULL,
                            reminder_time TEXT NOT NULL,
                            status TEXT NOT NULL DEFAULT 'Pending',
                            priority TEXT NOT NULL DEFAULT 'Medium',
                            created_date TEXT NOT NULL,
                            notes TEXT,
                            category TEXT DEFAULT 'General'
                        )""")
        else:
            cur.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cur.fetchall()]
            
            if 'notes' not in columns:
                cur.execute("ALTER TABLE tasks ADD COLUMN notes TEXT")
            if 'category' not in columns:
                cur.execute("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'General'")
            if 'created_date' not in columns:
                cur.execute("ALTER TABLE tasks ADD COLUMN created_date TEXT")
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reminder_time ON tasks(reminder_time)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)")

# ... (rest of the functions - use the full code from the file above}

def add_task(task, reminder_time, priority="Medium", notes="", category="General"):
    from datetime import datetime
    created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""INSERT INTO tasks (task, reminder_time, status, priority, created_date, notes, category) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (task, reminder_time, "Pending", priority, created_date, notes, category))
        return cur.lastrowid

def get_tasks(status_filter=None, priority_filter=None, category_filter=None):
    with get_db_connection() as conn:
        cur = conn.cursor()
        query = "SELECT id, task, reminder_time, status, priority, notes, category FROM tasks WHERE 1=1"
        params = []

        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        if priority_filter:
            query += " AND priority = ?"
            params.append(priority_filter)
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)

        query += " ORDER BY reminder_time ASC"
        cur.execute(query, params)
        return cur.fetchall()

def mark_done(task_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET status='Done' WHERE id=?", (task_id,))
        return cur.rowcount > 0

def delete_task(task_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        return cur.rowcount > 0

def update_task(task_id, task, reminder_time, priority, notes="", category="General"):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""UPDATE tasks SET task=?, reminder_time=?, priority=?, notes=?, category=?
                       WHERE id=?""", (task, reminder_time, priority, notes, category, task_id))
        return cur.rowcount > 0

def get_task_by_id(task_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT task, reminder_time, priority, notes, category FROM tasks WHERE id=?", (task_id,))
        return cur.fetchone()

def get_statistics():
    with get_db_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM tasks")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
        pending = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks WHERE status='Done'")
        done = cur.fetchone()[0]

        cur.execute("SELECT priority, COUNT(*) FROM tasks WHERE status='Pending' GROUP BY priority")
        by_priority = dict(cur.fetchall())

        cur.execute("SELECT category, COUNT(*) FROM tasks GROUP BY category")
        by_category = dict(cur.fetchall())

        return {
            'total': total,
            'pending': pending,
            'done': done,
            'by_priority': by_priority,
            'by_category': by_category
        }

def export_to_csv(csv_path):
    import csv
    tasks = get_tasks()

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Task', 'Reminder Time', 'Status', 'Priority', 'Notes', 'Category'])
        writer.writerows(tasks)
    return True
