# src/database.py
import sqlite3
from datetime import datetime
import os
import threading
from contextlib import contextmanager

# Create a thread-local storage for database connections
_local = threading.local()

@contextmanager
def get_db_connection():
    """Get a database connection with proper handling."""
    db_path = os.path.join("data", "attendance.db")
    
    # Get or create connection for this thread
    if not hasattr(_local, 'conn'):
        _local.conn = sqlite3.connect(db_path, timeout=20.0)  # 20 second timeout
        _local.conn.execute("PRAGMA journal_mode=WAL")  # Use Write-Ahead Logging
        _local.conn.execute("PRAGMA busy_timeout=5000")  # 5 second busy timeout
    
    try:
        yield _local.conn
    except Exception as e:
        _local.conn.rollback()
        raise e

def init_db():
    """Initialize the database and create tables if they don't exist."""
    db_path = os.path.join("data", "attendance.db")
    print(f"Initializing database at: {db_path}")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    with get_db_connection() as conn:
        c = conn.cursor()

        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS attendance
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      date TEXT NOT NULL,
                      hour INTEGER NOT NULL,
                      UNIQUE(name, date, hour))''')
        print("Created attendance table")

        c.execute('''CREATE TABLE IF NOT EXISTS contacts
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        parent_phone TEXT,
                        email TEXT)''')
        print("Created contacts table")
        
        conn.commit()
    print("Database initialization complete")


def verify_database():
    """Verify database structure and contents."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Check tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print("\n=== Database Tables ===")
        for table in tables:
            print(f"- {table[0]}")
            
        # Check attendance records
        c.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = c.fetchone()[0]
        print(f"\n=== Attendance Records ===")
        print(f"Total records: {attendance_count}")
        
        if attendance_count > 0:
            c.execute("SELECT name, date, hour FROM attendance ORDER BY date DESC, hour DESC LIMIT 5")
            recent_records = c.fetchall()
            print("\nMost recent records:")
            for record in recent_records:
                print(f"- {record[0]}: {record[1]} at {record[2]}:00")
        
        # Check contacts
        c.execute("SELECT COUNT(*) FROM contacts")
        contacts_count = c.fetchone()[0]
        print(f"\n=== Contact Records ===")
        print(f"Total contacts: {contacts_count}")
        
        if contacts_count > 0:
            c.execute("SELECT name, parent_phone, email FROM contacts")
            contacts = c.fetchall()
            print("\nContact details:")
            for contact in contacts:
                print(f"- {contact[0]}: {contact[1]}, {contact[2]}")
        
        return True


def mark_attendance(name):
    """Mark attendance for current hour"""
    # Validate name
    if not name or len(name) < 2 or len(name) > 50:
        print(f"❌ Invalid name: {name}")
        return "invalid_name"
        
    # Check if student exists in contacts
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM contacts WHERE name = ?", (name,))
        if not c.fetchone():
            print(f"❌ Student not found in contacts: {name}")
            return "student_not_found"

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_hour = now.hour

        try:
            c.execute('''INSERT INTO attendance (name, date, hour)
                         VALUES (?, ?, ?)''',
                      (name, current_date, current_hour))
            conn.commit()
            print(f"✅ Marked attendance for {name} on {current_date} at {current_hour}:00")
            return "marked"
        except sqlite3.IntegrityError:
            print(f"ℹ️ Attendance already marked for {name} on {current_date} at {current_hour}:00")
            return "already_marked"


def get_attendance_records():
    """Get all attendance records with hour information"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT name, date, hour 
                     FROM attendance 
                     ORDER BY date DESC, hour DESC''')
        return c.fetchall()

def add_contact(name, parent_phone=None, email=None):
    """Add or update contact information"""
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT OR REPLACE INTO contacts (name, parent_phone, email) VALUES (?, ?, ?)",
                      (name, parent_phone, email))
            conn.commit()
            print(f"✅ Contact information updated for {name}")
        except sqlite3.Error as e:
            print(f"❌ Error updating contact: {str(e)}")
            raise

def get_contact_info(name):
    """Get contact information for a student"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT parent_phone, email FROM contacts WHERE name = ?", (name,))
        return c.fetchone()

def delete_contact(name):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM contacts WHERE name = ?", (name,))
        conn.commit()
        print(f"Contact information deleted for {name}.")

def delete_records(name=None, date=None):
    with get_db_connection() as conn:
        c = conn.cursor()
        if name and date:
            c.execute("DELETE FROM attendance WHERE name = ? AND date = ?", (name, date))
        elif name:
            c.execute("DELETE FROM attendance WHERE name = ?", (name,))
        elif date:
            c.execute("DELETE FROM attendance WHERE date = ?", (date,))
        else:
            print("No records deleted. Specify a name or date.")
        conn.commit()
        print(f"Deleted records for name={name}, date={date}.")


def get_daily_absences(date, hours):
    """Get absences for specific date and hours"""
    with get_db_connection() as conn:
        c = conn.cursor()
        absences = []
        for hour in hours:
            # Get all valid students from contacts
            c.execute("SELECT name FROM contacts WHERE name NOT LIKE '%/%' AND name NOT LIKE '%\\%'")
            all_students = [row[0] for row in c.fetchall()]

            # Get present students for the hour
            c.execute('''SELECT name FROM attendance 
                         WHERE date = ? AND hour = ?''', (date, hour))
            present = [row[0] for row in c.fetchall()]

            # Calculate absences
            absent = list(set(all_students) - set(present))
            absences.extend([(hour, student) for student in absent])

        return absences

def delete_all_attendance():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM attendance")
        conn.commit()
        print("All attendance records deleted.")

def delete_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS attendance")
        conn.commit()
        print("Attendance table deleted.")


def get_attendance_stats():
    """Fetch attendance data for visualization"""
    with get_db_connection() as conn:
        c = conn.cursor()

        # Get total classes held
        c.execute("""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT date || '-' || hour 
                FROM attendance
            )
        """)
        total_classes = c.fetchone()[0] or 1  # Avoid division by zero

        # Get attendance count per student
        c.execute('''
            SELECT name, COUNT(*) as present_count 
            FROM attendance 
            GROUP BY name
        ''')
        attendance_data = c.fetchall()

        # Calculate percentages
        stats = []
        for name, present in attendance_data:
            percentage = (present / total_classes) * 100
            stats.append((name, present, round(percentage, 2)))

        return stats, total_classes

def show_database_contents():
    """Display all records from both contacts and attendance tables."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        print("\n=== Contacts Table ===")
        c.execute("SELECT * FROM contacts")
        contacts = c.fetchall()
        if contacts:
            for contact in contacts:
                print(f"ID: {contact[0]}, Name: {contact[1]}, Phone: {contact[2]}, Email: {contact[3]}")
        else:
            print("No contacts found")
            
        print("\n=== Attendance Records ===")
        c.execute("SELECT * FROM attendance ORDER BY date DESC, hour DESC")
        records = c.fetchall()
        if records:
            for record in records:
                print(f"ID: {record[0]}, Name: {record[1]}, Date: {record[2]}, Hour: {record[3]}")
        else:
            print("No attendance records found")

if __name__ == "__main__":
    # When run directly, verify database
    print("Verifying database...")
    verify_database()