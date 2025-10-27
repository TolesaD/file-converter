import sqlite3
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE,
                preferences TEXT DEFAULT '{}',
                total_conversions INTEGER DEFAULT 0
            )
        ''')
        
        # Conversion jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversion_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                input_file_path TEXT,
                output_format TEXT,
                status TEXT DEFAULT 'queued',
                progress INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                priority INTEGER DEFAULT 0,
                error_message TEXT,
                file_size INTEGER,
                input_type TEXT,
                output_file_path TEXT,
                queue_position INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                input_type TEXT,
                output_type TEXT,
                input_size INTEGER,
                output_size INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conversion_time INTEGER,
                success BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def add_user(self, user_id, username, first_name, last_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    def update_conversion_job(self, job_id, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if 'progress' in kwargs or 'status' in kwargs:
            kwargs['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(job_id)
        
        cursor.execute(f'''
            UPDATE conversion_jobs SET {set_clause} WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def add_conversion_job(self, user_id, input_file_path, output_format, input_type, file_size, queue_position=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversion_jobs 
            (user_id, input_file_path, output_format, input_type, file_size, queue_position)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, input_file_path, output_format, input_type, file_size, queue_position))
        
        job_id = cursor.lastrowid
        
        # Update user's total conversions
        cursor.execute('''
            UPDATE users SET total_conversions = total_conversions + 1 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return job_id
    
    def get_queued_jobs_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM conversion_jobs 
            WHERE status IN ('queued', 'processing')
        ''')
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_user_queued_jobs(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, input_file_path, output_format, status, progress, queue_position
            FROM conversion_jobs 
            WHERE user_id = ? AND status IN ('queued', 'processing')
            ORDER BY created_at ASC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'input_file': row[1],
            'output_format': row[2],
            'status': row[3],
            'progress': row[4],
            'queue_position': row[5]
        } for row in results]

# Global database instance
db = Database()