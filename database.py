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
                queue_position INTEGER DEFAULT 0,
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
                conversion_time INTEGER DEFAULT 0,
                success BOOLEAN DEFAULT TRUE,
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
    
    def get_user_history(self, user_id, limit=50):
        """Get user conversion history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT input_type, output_type, input_size, output_size, timestamp, success
            FROM history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'input_type': row[0],
            'output_type': row[1],
            'input_size': row[2],
            'output_size': row[3],
            'timestamp': row[4],
            'success': row[5]
        } for row in results]
    
    def get_system_stats(self):
        """Get system statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Total conversions
        cursor.execute('SELECT COUNT(*) FROM conversion_jobs')
        total_conversions = cursor.fetchone()[0]
        
        # Successful conversions
        cursor.execute('SELECT COUNT(*) FROM history WHERE success = 1')
        successful_conversions = cursor.fetchone()[0]
        
        # Popular conversions
        cursor.execute('''
            SELECT input_type, output_type, COUNT(*) as count
            FROM history 
            WHERE success = 1
            GROUP BY input_type, output_type 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        popular_conversions = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_conversions': total_conversions,
            'successful_conversions': successful_conversions,
            'popular_conversions': popular_conversions
        }
    
    def get_queued_jobs_count(self):
        """Get count of queued jobs"""
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
        """Get user's queued jobs"""
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
    
    def get_all_users(self):
        """Get all users for broadcast and management"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, registration_date, is_banned, total_conversions 
            FROM users 
            ORDER BY registration_date DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [{
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'registration_date': row[4],
            'is_banned': bool(row[5]),
            'total_conversions': row[6]
        } for row in users]
    
    def get_banned_users(self):
        """Get all banned users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_name 
            FROM users 
            WHERE is_banned = 1
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [{
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3]
        } for row in users]
    
    def ban_user(self, user_id):
        """Ban a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    
    def unban_user(self, user_id):
        """Unban a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, is_banned, total_conversions
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'is_banned': bool(user[4]),
                'total_conversions': user[5]
            }
        return None
    
    def get_conversion_stats(self):
        """Get detailed conversion statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total conversions per day (last 7 days)
        cursor.execute('''
            SELECT DATE(created_at), COUNT(*) 
            FROM conversion_jobs 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at) 
            ORDER BY DATE(created_at) DESC
        ''')
        daily_conversions = cursor.fetchall()
        
        # Format distribution
        cursor.execute('''
            SELECT input_type, COUNT(*) 
            FROM conversion_jobs 
            GROUP BY input_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''')
        format_distribution = cursor.fetchall()
        
        # User activity
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) 
            FROM conversion_jobs 
            WHERE created_at >= datetime('now', '-1 day')
        ''')
        daily_active_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) 
            FROM conversion_jobs 
            WHERE created_at >= datetime('now', '-7 days')
        ''')
        weekly_active_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'daily_conversions': daily_conversions,
            'format_distribution': format_distribution,
            'daily_active_users': daily_active_users,
            'weekly_active_users': weekly_active_users
        }

# Global database instance
db = Database()