from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import csv
import time
import re
import hashlib
import secrets
import sqlite3
import threading
import sys
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Tuple
import logging
import os
from dotenv import load_dotenv
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-admin-key-change-in-production')

# Load environment variables
load_dotenv()

def filter_medication_recommendations(report: str, language: str = 'en') -> str:
    """Filter out medication recommendations from clinical reports for safety"""
    
    # Comprehensive medication-related patterns
    medication_patterns = [
        # English patterns - broader but still targeted
        r'.*\b(recommend|suggest|consider|prescribe|start|begin|initiate|try)\s+.*?\b(medication|medicine|drug|antidepressant|antianxiety|SSRI|SNRI|benzodiazepine|antipsychotic)\b.*',
        r'.*\b(sertraline|fluoxetine|escitalopram|paroxetine|citalopram|venlafaxine|duloxetine|bupropion|mirtazapine|trazodone|lorazepam|alprazolam|clonazepam|diazepam|buspirone|quetiapine|aripiprazole|risperidone|olanzapine|lamotrigine|valproate|carbamazepine)\b.*',
        r'.*\b(mg|milligrams|dose|dosage|daily|twice|morning|evening)\s+.*\b(medication|medicine|drug)\b.*',
        r'.*\bmedicinal\s+treatment\b.*',
        r'.*\bpharmacological\s+(intervention|treatment)\b.*',
        
        # Chinese patterns - broader coverage
        r'.*\b(建議|推薦|考慮|處方|開始|嘗試)\s+.*?\b(藥物|藥品|處方|抗憂鬱劑|抗焦慮劑|苯二氮平類|抗精神病藥)\b.*',
        r'.*\b(舍曲林|氟西汀|艾司西酞普蘭|帕羅西汀|西酞普蘭|文拉法辛|度洛西汀|安非他酮|米氮平|勞拉西泮|阿普唑侖|氯硝西泮|地西泮|丁螺環酮)\b.*',
        r'.*\b(毫克|劑量|每日|每天|早上|晚上)\s+.*?\b(藥物|藥品)\b.*',
        r'.*\b藥物治療\b.*',
        r'.*\b藥理學.*?(干預|治療)\b.*'
    ]
    
    # Split report into sentences and paragraphs
    sentences = []
    for paragraph in report.split('\n'):
        sentences.extend(paragraph.split('.'))
    
    filtered_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if sentence contains medication-related content
        contains_medication = False
        
        for pattern in medication_patterns:
            if re.search(pattern, sentence, re.IGNORECASE | re.DOTALL):
                contains_medication = True
                break
        
        if contains_medication:
            # Replace with redacted message
            if language == 'zh':
                redacted_msg = "[藥物相關建議已隱藏 - 請諮詢合格醫師獲得藥物治療建議]"
            else:
                redacted_msg = "[Medication-related recommendations redacted - Please consult a qualified physician for medication advice]"
            filtered_sentences.append(redacted_msg)
        else:
            filtered_sentences.append(sentence)
    
    # Rejoin sentences, handling newlines properly
    result = '. '.join(filtered_sentences)
    
    # Clean up multiple consecutive redaction messages
    if language == 'zh':
        result = re.sub(r'(\[藥物相關建議已隱藏[^\]]+\]\.\s*){2,}', '[藥物相關建議已隱藏 - 請諮詢合格醫師獲得藥物治療建議]. ', result)
    else:
        result = re.sub(r'(\[Medication-related recommendations redacted[^\]]+\]\.\s*){2,}', '[Medication-related recommendations redacted - Please consult a qualified physician for medication advice]. ', result)
    
    return result

class DatabaseManager:
    """SQLite database manager for PsyFind"""
    
    def __init__(self, db_path: str = 'psyfind.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.lock:
            conn = self.get_connection()
            try:
                # User sessions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        language TEXT DEFAULT 'en',
                        message_count INTEGER DEFAULT 0,
                        conversation_stage TEXT DEFAULT 'initial',
                        user_info TEXT DEFAULT '{}',
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Chat messages table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
                    )
                ''')
                
                # Assessment results table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        assessment_type TEXT NOT NULL,
                        responses TEXT NOT NULL,
                        score INTEGER,
                        severity TEXT,
                        interpretation TEXT,
                        dsm_analysis TEXT,
                        clinical_report TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
                    )
                ''')
                
                # Admin sessions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS admin_sessions (
                        session_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        permissions TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # System analytics table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        total_sessions INTEGER DEFAULT 0,
                        total_assessments INTEGER DEFAULT 0,
                        assessment_types TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                ''')
                
                # System events table for logging
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        session_id TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Doctors/Psychiatrists table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS doctors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        specialty TEXT NOT NULL,
                        subspecialty TEXT,
                        approach TEXT,
                        phone TEXT,
                        email TEXT,
                        location TEXT,
                        languages TEXT NOT NULL,
                        experience TEXT,
                        education TEXT,
                        certifications TEXT,
                        availability TEXT,
                        consultation_fee TEXT,
                        notes TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
            except Exception as e:
                logger.error(f"Database initialization error: {str(e)}")
                conn.rollback()
            finally:
                conn.close()
    
    # User Session Management
    def create_user_session(self, session_id: str, language: str = 'en') -> bool:
        """Create a new user session"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO user_sessions 
                    (session_id, language, created_at, last_activity) 
                    VALUES (?, ?, ?, ?)
                ''', (session_id, language, datetime.now(), datetime.now()))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating user session: {str(e)}")
                return False
            finally:
                conn.close()
    
    def get_user_session(self, session_id: str) -> Optional[Dict]:
        """Get user session data"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM user_sessions WHERE session_id = ? AND is_active = 1
            ''', (session_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def update_session_activity(self, session_id: str, message_count: int = None, 
                              conversation_stage: str = None) -> bool:
        """Update session activity"""
        with self.lock:
            conn = self.get_connection()
            try:
                updates = ['last_activity = ?']
                params = [datetime.now()]
                
                if message_count is not None:
                    updates.append('message_count = ?')
                    params.append(message_count)
                
                if conversation_stage is not None:
                    updates.append('conversation_stage = ?')
                    params.append(conversation_stage)
                
                params.append(session_id)
                
                conn.execute(f'''
                    UPDATE user_sessions SET {', '.join(updates)} WHERE session_id = ?
                ''', params)
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error updating session activity: {str(e)}")
                return False
            finally:
                conn.close()
    
    def get_active_sessions(self, limit: int = 100) -> List[Dict]:
        """Get active user sessions"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT session_id, created_at, last_activity, language, 
                       message_count, conversation_stage
                FROM user_sessions 
                WHERE is_active = 1 
                ORDER BY last_activity DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def cleanup_expired_sessions(self, timeout_hours: int = 1) -> int:
        """Cleanup expired sessions"""
        with self.lock:
            conn = self.get_connection()
            try:
                cutoff_time = datetime.now() - timedelta(hours=timeout_hours)
                cursor = conn.execute('''
                    UPDATE user_sessions 
                    SET is_active = 0 
                    WHERE last_activity < ? AND is_active = 1
                ''', (cutoff_time,))
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Error cleaning up sessions: {str(e)}")
                return 0
            finally:
                conn.close()
    
    # Chat Message Management
    def add_chat_message(self, session_id: str, role: str, content: str, 
                        metadata: Dict = None) -> bool:
        """Add chat message to database"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    INSERT INTO chat_messages (session_id, role, content, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, role, content, json.dumps(metadata or {})))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding chat message: {str(e)}")
                return False
            finally:
                conn.close()
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for a session"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT role, content, timestamp, metadata
                FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, limit))
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                msg['metadata'] = json.loads(msg['metadata'])
                messages.append(msg)
            return list(reversed(messages))  # Return in chronological order
        finally:
            conn.close()
    
    # Assessment Management
    def save_assessment_result(self, session_id: str, assessment_type: str, 
                             responses: Dict, score: int, severity: str,
                             interpretation: str, dsm_analysis: List[Dict],
                             clinical_report: str) -> bool:
        """Save assessment results"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    INSERT INTO assessment_results 
                    (session_id, assessment_type, responses, score, severity, 
                     interpretation, dsm_analysis, clinical_report)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, assessment_type, json.dumps(responses), score,
                      severity, interpretation, json.dumps(dsm_analysis), clinical_report))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error saving assessment result: {str(e)}")
                return False
            finally:
                conn.close()
    
    def get_assessment_stats(self) -> Dict:
        """Get assessment statistics"""
        conn = self.get_connection()
        try:
            # Total assessments
            cursor = conn.execute('SELECT COUNT(*) as total FROM assessment_results')
            total = cursor.fetchone()['total']
            
            # Assessment types
            cursor = conn.execute('''
                SELECT assessment_type, COUNT(*) as count 
                FROM assessment_results 
                GROUP BY assessment_type
            ''')
            types = {row['assessment_type']: row['count'] for row in cursor.fetchall()}
            
            # Daily stats (last 30 days)
            cursor = conn.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM assessment_results 
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            ''')
            daily = {row['date']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_assessments': total,
                'assessment_types': types,
                'daily_stats': daily
            }
        finally:
            conn.close()
    
    # Admin Session Management
    def create_admin_session(self, session_id: str, username: str, permissions: List[str]) -> bool:
        """Create admin session"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO admin_sessions 
                    (session_id, username, permissions, created_at, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, username, json.dumps(permissions), datetime.now(), datetime.now()))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating admin session: {str(e)}")
                return False
            finally:
                conn.close()
    
    def get_admin_session(self, session_id: str) -> Optional[Dict]:
        """Get admin session"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM admin_sessions 
                WHERE session_id = ? AND is_active = 1
            ''', (session_id,))
            row = cursor.fetchone()
            if row:
                session_data = dict(row)
                session_data['permissions'] = json.loads(session_data['permissions'])
                return session_data
            return None
        finally:
            conn.close()
    
    def update_admin_activity(self, session_id: str) -> bool:
        """Update admin session activity"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    UPDATE admin_sessions 
                    SET last_activity = ? 
                    WHERE session_id = ?
                ''', (datetime.now(), session_id))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error updating admin activity: {str(e)}")
                return False
            finally:
                conn.close()
    
    def terminate_admin_session(self, session_id: str) -> bool:
        """Terminate admin session"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    UPDATE admin_sessions 
                    SET is_active = 0 
                    WHERE session_id = ?
                ''', (session_id,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error terminating admin session: {str(e)}")
                return False
            finally:
                conn.close()
    
    # Analytics and Events
    def log_system_event(self, event_type: str, event_data: Dict = None, session_id: str = None):
        """Log system event"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    INSERT INTO system_events (event_type, event_data, session_id)
                    VALUES (?, ?, ?)
                ''', (event_type, json.dumps(event_data or {}), session_id))
                conn.commit()
            except Exception as e:
                logger.error(f"Error logging system event: {str(e)}")
            finally:
                conn.close()
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        conn = self.get_connection()
        try:
            # Active sessions
            cursor = conn.execute('SELECT COUNT(*) as count FROM user_sessions WHERE is_active = 1')
            active_sessions = cursor.fetchone()['count']
            
            # Total sessions
            cursor = conn.execute('SELECT COUNT(*) as count FROM user_sessions')
            total_sessions = cursor.fetchone()['count']
            
            # Assessment stats
            assessment_stats = self.get_assessment_stats()
            
            return {
                'active_sessions': active_sessions,
                'total_sessions': total_sessions,
                **assessment_stats
            }
        finally:
            conn.close()
    
    # Doctor Management
    def create_doctor(self, doctor_data: Dict) -> int:
        """Create a new doctor record"""
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.execute('''
                    INSERT INTO doctors (
                        name, specialty, subspecialty, approach, phone, email, 
                        location, languages, experience, education, certifications,
                        availability, consultation_fee, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doctor_data.get('name'),
                    doctor_data.get('specialty'),
                    doctor_data.get('subspecialty', ''),
                    doctor_data.get('approach', ''),
                    doctor_data.get('phone', ''),
                    doctor_data.get('email', ''),
                    doctor_data.get('location', ''),
                    json.dumps(doctor_data.get('languages', [])),
                    doctor_data.get('experience', ''),
                    doctor_data.get('education', ''),
                    doctor_data.get('certifications', ''),
                    doctor_data.get('availability', ''),
                    doctor_data.get('consultation_fee', ''),
                    doctor_data.get('notes', '')
                ))
                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()
    
    def get_doctors(self, active_only: bool = True, limit: int = None) -> List[Dict]:
        """Get all doctors"""
        conn = self.get_connection()
        try:
            query = 'SELECT * FROM doctors'
            params = []
            
            if active_only:
                query += ' WHERE is_active = 1'
            
            query += ' ORDER BY name'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor = conn.execute(query, params)
            doctors = []
            
            for row in cursor.fetchall():
                doctor = dict(row)
                doctor['languages'] = json.loads(doctor['languages'])
                doctors.append(doctor)
            
            return doctors
        finally:
            conn.close()
    
    def get_doctor(self, doctor_id: int) -> Dict:
        """Get a specific doctor by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,))
            row = cursor.fetchone()
            
            if row:
                doctor = dict(row)
                doctor['languages'] = json.loads(doctor['languages'])
                return doctor
            return None
        finally:
            conn.close()
    
    def update_doctor(self, doctor_id: int, doctor_data: Dict) -> bool:
        """Update a doctor record"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    UPDATE doctors SET
                        name = ?, specialty = ?, subspecialty = ?, approach = ?,
                        phone = ?, email = ?, location = ?, languages = ?,
                        experience = ?, education = ?, certifications = ?,
                        availability = ?, consultation_fee = ?, notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    doctor_data.get('name'),
                    doctor_data.get('specialty'),
                    doctor_data.get('subspecialty', ''),
                    doctor_data.get('approach', ''),
                    doctor_data.get('phone', ''),
                    doctor_data.get('email', ''),
                    doctor_data.get('location', ''),
                    json.dumps(doctor_data.get('languages', [])),
                    doctor_data.get('experience', ''),
                    doctor_data.get('education', ''),
                    doctor_data.get('certifications', ''),
                    doctor_data.get('availability', ''),
                    doctor_data.get('consultation_fee', ''),
                    doctor_data.get('notes', ''),
                    doctor_id
                ))
                conn.commit()
                return conn.total_changes > 0
            finally:
                conn.close()
    
    def delete_doctor(self, doctor_id: int) -> bool:
        """Soft delete a doctor (set is_active to False)"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    UPDATE doctors SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (doctor_id,))
                conn.commit()
                return conn.total_changes > 0
            finally:
                conn.close()
    
    def search_doctors(self, query: str, specialty: str = None) -> List[Dict]:
        """Search doctors by name, specialty, or location"""
        conn = self.get_connection()
        try:
            sql = '''
                SELECT * FROM doctors 
                WHERE is_active = 1 AND (
                    name LIKE ? OR 
                    specialty LIKE ? OR 
                    subspecialty LIKE ? OR 
                    location LIKE ?
                )
            '''
            params = [f'%{query}%'] * 4
            
            if specialty:
                sql += ' AND specialty = ?'
                params.append(specialty)
            
            sql += ' ORDER BY name'
            
            cursor = conn.execute(sql, params)
            doctors = []
            
            for row in cursor.fetchall():
                doctor = dict(row)
                doctor['languages'] = json.loads(doctor['languages'])
                doctors.append(doctor)
            
            return doctors
        finally:
            conn.close()
    
    def _import_doctors_from_csv(self):
        """Import doctors from CSV file if database is empty"""
        try:
            logger.info("Checking if doctors need to be imported from CSV...")
            
            # Check if doctors table is empty
            conn = self.get_connection()
            try:
                cursor = conn.execute('SELECT COUNT(*) FROM doctors')
                count = cursor.fetchone()[0]
            finally:
                conn.close()
            
            if count > 0:
                logger.info(f"Found {count} doctors in database, skipping CSV import")
                return
            
            # Import from CSV
            import csv
            import os
            
            csv_path = 'assets/psychiatrists.csv'
            if not os.path.exists(csv_path):
                logger.warning("Psychiatrists CSV file not found, skipping import")
                return
            
            logger.info("Starting CSV import...")
            imported_count = 0
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        if not row.get('name') or not row.get('name').strip():  # Skip empty rows
                            continue
                        
                        # Parse languages
                        languages_str = row.get('languages', '').strip()
                        if not languages_str:
                            continue  # Skip if no languages
                        
                        languages = [lang.strip() for lang in languages_str.split(',') if lang.strip()]
                        if not languages:
                            continue
                        
                        # Create doctor data
                        doctor_data = {
                            'name': row.get('name', '').strip(),
                            'specialty': row.get('specialty', '').strip(),
                            'subspecialty': row.get('subspecialty', '').strip(),
                            'approach': row.get('approach', '').strip(),
                            'phone': row.get('phone', '').strip(),
                            'email': '',  # Not in CSV
                            'location': row.get('location', '').strip(),
                            'languages': languages,
                            'experience': row.get('experience', '').strip(),
                            'education': '',  # Not in CSV
                            'certifications': '',  # Not in CSV
                            'availability': '',  # Not in CSV
                            'consultation_fee': '',  # Not in CSV
                            'notes': ''  # Not in CSV
                        }
                        
                        # Only import if we have required fields
                        if doctor_data['name'] and doctor_data['specialty'] and languages:
                            self.create_doctor(doctor_data)
                            imported_count += 1
                            logger.info(f"Imported doctor: {doctor_data['name']}")
                    
                    except Exception as row_error:
                        logger.error(f"Error importing row {row}: {str(row_error)}")
                        continue
            
            logger.info(f"Successfully imported {imported_count} doctors from CSV")
            
        except Exception as e:
            logger.error(f"Error importing doctors from CSV: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

class LLMService:
    def __init__(self):
        self.preferred_provider = os.getenv('LLM_PROVIDER', 'auto').lower()
        
        # API keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        # Use database for session management
        self.session_timeout = 3600  # 1 hour timeout
        
    def _cleanup_expired_sessions(self):
        """Remove expired sessions to prevent memory leaks"""
        return db_manager.cleanup_expired_sessions(timeout_hours=1)
    
    def _validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format and prevent injection attacks"""
        if not session_id or not isinstance(session_id, str):
            return False
        
        # Session ID should be alphanumeric with underscores and dashes
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            return False
        
        # Reasonable length limits
        if len(session_id) < 10 or len(session_id) > 100:
            return False
        
        return True
    
    def _get_session(self, session_id: str, language: str = 'en') -> Dict:
        """Get or create a chat session with proper validation"""
        if not self._validate_session_id(session_id):
            raise ValueError(f"Invalid session ID format: {session_id}")
        
        # Try to get existing session from database
        session_data = db_manager.get_user_session(session_id)
        
        if session_data:
            # Update activity and return existing session
            db_manager.update_session_activity(session_id)
            # Convert database format to expected format
            return {
                'messages': db_manager.get_chat_history(session_id),
                'context': {
                    'language': session_data['language'],
                    'user_info': json.loads(session_data.get('user_info', '{}')),
                    'assessment_recommendations': [],
                    'conversation_stage': session_data['conversation_stage']
                },
                'created_at': session_data['created_at'],
                'last_activity': session_data['last_activity'],
                'message_count': session_data['message_count']
            }
        else:
            # Create new session in database
            db_manager.create_user_session(session_id, language)
            logger.info(f"Created new session: {session_id}")
            return {
                'messages': [],
                'context': {
                    'language': language,
                    'user_info': {},
                    'assessment_recommendations': [],
                    'conversation_stage': 'initial'
                },
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'message_count': 0
            }
        
    def generate_analysis_report(self, symptoms: str, age: int, duration: str, dsm_matches: List[Dict], language: str = 'en') -> str:
        """Generate comprehensive analysis report using LLM"""
        
        # Create detailed prompt for psychiatric analysis
        prompt = self._create_analysis_prompt(symptoms, age, duration, dsm_matches, language)
        
        # Use specified provider or auto-fallback
        try:
            if self.preferred_provider == 'ollama':
                return self._query_ollama(prompt)
            elif self.preferred_provider == 'openai':
                return self._query_openai(prompt)
            elif self.preferred_provider == 'openrouter':
                return self._query_openrouter(prompt)
            elif self.preferred_provider == 'fallback':
                return self._generate_fallback_report(dsm_matches, language)
            else:  # auto mode - try in priority order
                if self._is_ollama_available():
                    return self._query_ollama(prompt)
                elif self.openai_api_key:
                    return self._query_openai(prompt)
                elif self.openrouter_api_key:
                    return self._query_openrouter(prompt)
                else:
                    return self._generate_fallback_report(dsm_matches, language)
        except Exception as e:
            logger.error(f"LLM analysis failed with {self.preferred_provider}: {str(e)}")
            # If specific provider fails and not in auto mode, still try fallback
            if self.preferred_provider != 'auto':
                logger.info("Falling back to basic report due to provider failure")
            return self._generate_fallback_report(dsm_matches, language)
    
    def _create_analysis_prompt(self, symptoms: str, age: int, duration: str, dsm_matches: List[Dict], language: str) -> str:
        """Create detailed prompt for LLM analysis"""
        
        lang_instruction = ""
        if language == 'zh':
            lang_instruction = "Please respond in Traditional Chinese (繁體中文)."
        
        dsm_context = ""
        if dsm_matches:
            dsm_context = "DSM-5-TR Analysis Results:\n"
            for match in dsm_matches[:3]:
                dsm_context += f"- {match['disorder']} (Code: {match['code']}) - {match['confidence']:.1f}% match\n"
                dsm_context += f"  Matched keywords: {', '.join(match['matched_keywords'])}\n"
        
        prompt = f"""You are a clinical psychiatrist providing a comprehensive mental health assessment report. {lang_instruction}

PATIENT INFORMATION:
- Age: {age} years old
- Symptom Duration: {duration}
- Reported Symptoms: {symptoms}

{dsm_context}

Please provide a detailed psychiatric analysis report including:

1. **Clinical Impression**: Professional assessment of the presented symptoms
2. **Differential Diagnosis**: Possible conditions to consider based on DSM-5-TR criteria
3. **Risk Assessment**: Evaluate any immediate safety concerns
4. **Recommended Interventions**: 
   - Immediate steps to take
   - Therapeutic approaches to consider
   - Lifestyle modifications
5. **Follow-up Care**: Timeline and type of professional care needed
6. **Psychoeducation**: Brief explanation for patient understanding

IMPORTANT GUIDELINES:
- Base analysis on evidence-based psychiatric principles
- Reference DSM-5-TR criteria when appropriate
- Emphasize the need for professional evaluation
- Be empathetic and non-judgmental
- Include safety considerations
- Avoid definitive diagnoses - use terms like "suggests," "consistent with," "warrants evaluation for"

Format the response as a professional clinical report that could be shared with healthcare providers."""

        return prompt
    
    def chat_conversation(self, session_id: str, user_message: str, language: str = 'en') -> Dict:
        """Handle chat conversation with LLM-powered responses"""
        
        try:
            # Get or create session with proper validation
            session = self._get_session(session_id, language)
            
            # Increment message count and update activity
            session['message_count'] += 1
            session['last_activity'] = time.time()
            
            # Check for message limits per session (prevent abuse)
            if session['message_count'] > 100:
                logger.warning(f"Session {session_id} exceeded message limit")
                return {
                    "message": "Session limit reached. Please start a new conversation.",
                    "assessment_recommendation": "none",
                    "conversation_stage": "limit_reached"
                }
                
        except ValueError as e:
            logger.error(f"Session validation error: {e}")
            return {
                "message": "Invalid session. Please refresh the page.",
                "assessment_recommendation": "none",
                "conversation_stage": "error"
            }
        
        # Add user message to database
        db_manager.add_chat_message(session_id, 'user', user_message)
        
        # Update session message count
        new_message_count = session['message_count'] + 1
        db_manager.update_session_activity(session_id, message_count=new_message_count)
        
        # Generate LLM response
        try:
            response_data = self._generate_chat_response(session, user_message, language, session_id)
            
            # Add assistant response to database
            db_manager.add_chat_message(session_id, 'assistant', response_data['message'], 
                                      response_data.get('metadata', {}))
            
            # Update session with conversation stage
            if response_data.get('conversation_stage'):
                db_manager.update_session_activity(session_id, 
                                                 message_count=new_message_count + 1,
                                                 conversation_stage=response_data['conversation_stage'])
            
            return response_data
            
        except Exception as e:
            logger.error(f"Chat conversation error: {str(e)}")
            return self._generate_fallback_chat_response(language, session)
    
    def _generate_chat_response(self, session: Dict, user_message: str, language: str, session_id: str) -> Dict:
        """Generate intelligent chat response using LLM"""
        
        # Create conversation prompt
        prompt = self._create_chat_prompt(session, user_message, language, session_id)
        
        # Get LLM response
        try:
            if self.preferred_provider == 'ollama':
                llm_response = self._query_ollama(prompt)
            elif self.preferred_provider == 'openai' and self.openai_api_key:
                llm_response = self._query_openai(prompt)
            elif self.preferred_provider == 'openrouter' and self.openrouter_api_key:
                llm_response = self._query_openrouter(prompt)
            else:
                # Auto-select available provider
                if self._is_ollama_available():
                    llm_response = self._query_ollama(prompt)
                elif self.openai_api_key:
                    llm_response = self._query_openai(prompt)
                elif self.openrouter_api_key:
                    llm_response = self._query_openrouter(prompt)
                else:
                    return self._generate_fallback_chat_response(language, session)
            
            # Parse LLM response for structured data
            return self._parse_chat_response(llm_response, session, language)
            
        except Exception as e:
            logger.error(f"LLM chat response error: {str(e)}")
            return self._generate_fallback_chat_response(language, session)
    
    def _create_chat_prompt(self, session: Dict, user_message: str, language: str, session_id: str = None) -> str:
        """Create chat prompt for LLM"""
        
        lang_instruction = ""
        if language == 'zh':
            lang_instruction = "請用繁體中文回應。"
        
        # Build conversation history
        conversation_history = ""
        for msg in session['messages'][-6:]:  # Last 6 messages for context
            role = "用戶" if language == 'zh' and msg['role'] == 'user' else msg['role'].title()
            conversation_history += f"{role}: {msg['content']}\n"
        
        conversation_stage = session['context'].get('conversation_stage', 'initial')
        
        # Handle special conversation start
        if user_message in ["START_CONVERSATION", "FRESH_START_CONVERSATION"]:
            # For fresh starts, ensure completely clean session
            if user_message == "FRESH_START_CONVERSATION":
                session['messages'] = []  # Clear any existing messages
                session['context']['conversation_stage'] = 'initial'
                session['context']['assessment_recommendations'] = []
                logger.info(f"Fresh start for session {session_id}")
            
            if language == 'zh':
                user_message = "請以友善和專業的方式介紹自己，並詢問今天如何幫助我。這是一個全新的對話。"
            else:
                user_message = "Please introduce yourself in a friendly and professional way, and ask how you can help me today. This is a completely fresh conversation."
        
        prompt = f"""You are a professional clinical psychologist assistant providing mental health screening and support. {lang_instruction}

ROLE: You are empathetic, professional, and knowledgeable about mental health. Your goal is to:
1. Conduct a supportive conversation to understand the user's concerns
2. Recommend appropriate standardized assessments when suitable
3. Provide psychoeducation and coping strategies
4. Always emphasize the importance of professional help when needed

CONVERSATION CONTEXT:
Stage: {conversation_stage}
Language: {language}

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE: {user_message}

RESPONSE GUIDELINES:
- Be warm, empathetic, and non-judgmental
- Build rapport through 2-3 exchanges, then move toward assessment when appropriate
- Ask open-ended questions to explore their experiences naturally
- After understanding their main concerns, suggest relevant assessments:
  * Depression symptoms (sadness, hopelessness, loss of interest, fatigue) → PHQ-9 assessment
  * Anxiety symptoms (worry, panic, restlessness, nervousness) → GAD-7 assessment  
  * Sleep issues (insomnia, sleep disturbances, fatigue) → Insomnia Severity Index
  * Health anxiety (excessive worry about physical health, somatic symptoms) → Whiteley-7 assessment
- Balance conversation with clinical progress - don't avoid assessments indefinitely
- If someone shares clear symptoms, acknowledge them and suggest appropriate screening
- Provide brief psychoeducation when appropriate
- Always remind users this is not a substitute for professional care
- Keep responses conversational and supportive (2-3 sentences max)

RESPONSE FORMAT:
You MUST respond with ONLY a valid JSON object. No additional text before or after. Use this exact structure:

{{
    "message": "Your empathetic response here (2-3 sentences max)",
    "assessment_recommendation": "phq9|gad7|isi|whiteley|none",
    "conversation_stage": "initial|assessment|support|referral",
    "follow_up_questions": ["Optional follow-up question"],
    "psychoeducation": "Brief educational note if relevant"
}}

IMPORTANT: Return ONLY the JSON object, nothing else. No explanations, no additional text.

JSON Response:"""

        return prompt
    
    def _parse_chat_response(self, llm_response: str, session: Dict, language: str) -> Dict:
        """Parse LLM response and extract structured data"""
        
        try:
            import json
            import re
            
            # Clean the response first
            cleaned_response = llm_response.strip()
            
            # Try multiple JSON extraction patterns
            json_patterns = [
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested JSON pattern
                r'\{.*?\}(?=\s*$)',  # JSON at end of string
                r'\{.*?\}(?=\s*\n)',  # JSON followed by newline
                r'\{.*\}',  # Simple JSON pattern (fallback)
            ]
            
            response_data = None
            
            for pattern in json_patterns:
                json_matches = re.findall(pattern, cleaned_response, re.DOTALL)
                for match in json_matches:
                    try:
                        # Try to parse this JSON candidate
                        candidate_data = json.loads(match.strip())
                        
                        # Validate it has expected fields
                        if isinstance(candidate_data, dict) and 'message' in candidate_data:
                            response_data = candidate_data
                            break
                    except json.JSONDecodeError:
                        continue
                
                if response_data:
                    break
            
            # If no valid JSON found, try to extract just the message content
            if not response_data:
                # Look for message content between quotes
                message_match = re.search(r'"message":\s*"([^"]*)"', cleaned_response)
                if message_match:
                    message_content = message_match.group(1)
                else:
                    # Try to clean up the response and use it as message
                    # Remove any JSON-like artifacts
                    message_content = re.sub(r'[{}"]', '', cleaned_response)
                    message_content = re.sub(r'message:\s*', '', message_content)
                    message_content = re.sub(r'assessment_recommendation:.*', '', message_content)
                    message_content = message_content.strip()
                    
                    # If still too messy, use simple fallback
                    if len(message_content) < 10 or 'assessment_recommendation' in message_content:
                        if language == 'zh':
                            message_content = "我理解您的感受。請告訴我更多關於您的情況。"
                        else:
                            message_content = "I understand how you're feeling. Please tell me more about your situation."
                
                response_data = {
                    "message": message_content,
                    "assessment_recommendation": "none",
                    "conversation_stage": "support"
                }
            
            # Ensure required fields exist
            response_data.setdefault("message", "I understand. Let me help you with that.")
            response_data.setdefault("assessment_recommendation", "none")
            response_data.setdefault("conversation_stage", "support")
            
            # Update session context
            session['context']['conversation_stage'] = response_data.get('conversation_stage', 'support')
            
            # Add assessment recommendation if provided
            if response_data.get('assessment_recommendation') != 'none':
                session['context']['assessment_recommendations'].append(
                    response_data['assessment_recommendation']
                )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error parsing chat response: {str(e)}")
            logger.error(f"Raw LLM response: {llm_response[:200]}...")
            
            # Extract any readable message from the response
            message = llm_response.strip()
            if len(message) > 500:
                message = message[:500] + "..."
            
            fallback_msg = "I'm here to help. Could you tell me more about what's on your mind?"
            if language == 'zh':
                fallback_msg = "我在這裡幫助您。能告訴我更多您心中的想法嗎？"
            
            return {
                "message": message if message else fallback_msg,
                "assessment_recommendation": "none",
                "conversation_stage": "support"
            }
    
    def _generate_fallback_chat_response(self, language: str, session: Dict = None) -> Dict:
        """Generate simple fallback response when LLM is unavailable"""
        
        # Simple supportive message - let LLM handle the complexity when available
        if language == 'zh':
            message = "我在這裡支持您。請告訴我更多關於您的感受，這樣我可以更好地幫助您。"
        else:
            message = "I'm here to support you. Please tell me more about how you're feeling so I can better help you."
        
        # Only hardcode the assessment recommendation logic based on keywords
        assessment_rec = "none"
        conversation_stage = "support"
        
        # Simple keyword-based assessment recommendation when LLM is unavailable
        if session and session.get('messages'):
            recent_messages = [msg['content'].lower() for msg in session['messages'][-3:] if msg['role'] == 'user']
            combined_text = ' '.join(recent_messages)
            
            # Hardcoded assessment logic - this is the only part that should be static
            if any(word in combined_text for word in ['sad', 'depressed', 'hopeless', 'worthless', 'tired', 'sleep', 'down']):
                assessment_rec = "phq9"
                conversation_stage = "assessment"
            elif any(word in combined_text for word in ['anxious', 'worry', 'panic', 'nervous', 'restless', 'fear']):
                assessment_rec = "gad7"
                conversation_stage = "assessment"
            elif any(word in combined_text for word in ['health', 'sick', 'disease', 'symptoms', 'body', 'illness']):
                assessment_rec = "whiteley"
                conversation_stage = "assessment"
        
        return {
            "message": message,
            "assessment_recommendation": assessment_rec,
            "conversation_stage": conversation_stage
        }
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama local LLM"""
        try:
            payload = {
                "model": "llama3.2",  # Default model, can be configured
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Analysis could not be generated.')
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama query failed: {str(e)}")
            raise
    
    def _query_openrouter(self, prompt: str) -> str:
        """Query OpenRouter cloud LLM"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "anthropic/claude-3-sonnet",  # Good for medical analysis
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                self.openrouter_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"OpenRouter query failed: {str(e)}")
            raise
    
    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI GPT API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",  # Use GPT-4o for medical analysis
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a clinical psychiatrist providing comprehensive mental health assessments. Provide professional, evidence-based analysis while emphasizing the need for in-person professional evaluation."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                error_msg = f"OpenAI API error: {response.status_code}"
                if response.status_code == 401:
                    error_msg += " - Invalid API key"
                elif response.status_code == 429:
                    error_msg += " - Rate limit exceeded"
                elif response.status_code == 400:
                    error_msg += " - Bad request"
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"OpenAI query failed: {str(e)}")
            raise
    
    def _generate_fallback_report(self, dsm_matches: List[Dict], language: str) -> str:
        """Generate basic report when LLM is unavailable"""
        
        if language == 'zh':
            report = """# 精神健康評估報告

## 臨床印象
基於提供的症狀描述和DSM-5-TR標準分析，建議進行專業心理健康評估。

## 初步分析
"""
            if dsm_matches:
                report += "根據症狀分析，可能需要評估以下狀況：\n"
                for match in dsm_matches[:3]:
                    report += f"- {match['disorder']} (符合度: {match['confidence']:.1f}%)\n"
            
            report += """
## 建議事項
1. **立即行動**: 尋求合格心理健康專業人員的評估
2. **安全評估**: 如有自傷或傷害他人想法，請立即聯繫急診服務
3. **支持系統**: 與信任的家人或朋友分享您的困擾
4. **自我照護**: 維持規律作息、適度運動、均衡飲食

## 重要提醒
此分析僅供參考，不能替代專業醫療診斷。請務必諮詢合格的心理健康專業人員。
"""
        else:
            report = """# Mental Health Assessment Report

## Clinical Impression
Based on the symptom description and DSM-5-TR criteria analysis, professional mental health evaluation is recommended.

## Initial Analysis
"""
            if dsm_matches:
                report += "Based on symptom analysis, evaluation may be warranted for:\n"
                for match in dsm_matches[:3]:
                    report += f"- {match['disorder']} ({match['confidence']:.1f}% symptom match)\n"
            
            report += """
## Recommendations
1. **Immediate Action**: Seek evaluation from qualified mental health professional
2. **Safety Assessment**: If experiencing thoughts of self-harm or harm to others, contact emergency services immediately
3. **Support System**: Share concerns with trusted family members or friends
4. **Self-Care**: Maintain regular sleep schedule, exercise, and balanced nutrition

## Important Notice
This analysis is for informational purposes only and cannot replace professional medical diagnosis. Please consult with qualified mental health professionals.
"""
        
        return report

class AdminManager:
    """Admin panel management system"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hour
        self.admin_credentials = {
            'admin': self._hash_password(os.getenv('ADMIN_PASSWORD', 'admin123')),
            'doctor': self._hash_password(os.getenv('DOCTOR_PASSWORD', 'doctor123'))
        }
        self.system_start_time = datetime.now()
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = os.getenv('PASSWORD_SALT', 'psyfind_salt_2024')
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        """Authenticate admin user"""
        if username in self.admin_credentials:
            hashed_password = self._hash_password(password)
            return self.admin_credentials[username] == hashed_password
        return False
    
    def create_admin_session(self, username: str) -> str:
        """Create admin session"""
        session_id = secrets.token_urlsafe(32)
        permissions = self._get_user_permissions(username)
        db_manager.create_admin_session(session_id, username, permissions)
        return session_id
    
    def _get_user_permissions(self, username: str) -> List[str]:
        """Get user permissions based on role"""
        if username == 'admin':
            return ['view_analytics', 'view_sessions', 'manage_sessions', 'system_control', 'user_management']
        elif username == 'doctor':
            return ['view_analytics', 'view_sessions']
        return []
    
    def validate_admin_session(self, session_id: str) -> bool:
        """Validate admin session"""
        session_data = db_manager.get_admin_session(session_id)
        if not session_data:
            return False
        
        # Check if session is expired
        last_activity = datetime.fromisoformat(session_data['last_activity'])
        if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
            db_manager.terminate_admin_session(session_id)
            return False
        
        # Update last activity
        db_manager.update_admin_activity(session_id)
        return True
    
    def get_analytics_data(self) -> Dict:
        """Get comprehensive analytics data"""
        stats = db_manager.get_system_stats()
        return {
            'active_sessions': stats['active_sessions'],
            'total_sessions': stats['total_sessions'],
            'total_assessments': stats['total_assessments'],
            'assessment_types': stats['assessment_types'],
            'daily_stats': stats['daily_stats'],
            'system_health': {
                'uptime': self.system_start_time,
                'memory_usage': self._get_memory_usage(),
                'llm_status': self._check_llm_status()
            }
        }
    
    def get_active_sessions(self) -> List[Dict]:
        """Get list of active user sessions"""
        sessions = db_manager.get_active_sessions()
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                'session_id': session['session_id'][:16] + '...',  # Truncate for privacy
                'created_at': session['created_at'],
                'last_activity': session['last_activity'],
                'message_count': session['message_count'],
                'language': session['language'],
                'conversation_stage': session['conversation_stage']
            })
        return formatted_sessions
    
    def terminate_session(self, session_id: str) -> bool:
        """Terminate a user session"""
        # Find the full session ID from truncated version
        sessions = db_manager.get_active_sessions()
        full_session_id = None
        for session in sessions:
            if session['session_id'].startswith(session_id.replace('...', '')):
                full_session_id = session['session_id']
                break
        
        if full_session_id:
            # Mark session as inactive
            db_manager.cleanup_expired_sessions(timeout_hours=0)  # Force cleanup
            logger.info(f"Admin terminated session: {full_session_id}")
            return True
        return False
    
    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 0.0
    
    def _check_llm_status(self) -> str:
        """Check LLM service status"""
        try:
            if llm_service.preferred_provider == 'openai' and llm_service.openai_api_key:
                return 'openai_ready'
            elif llm_service.preferred_provider == 'ollama':
                return 'ollama_ready'
            else:
                return 'fallback_mode'
        except:
            return 'error'
    
    def update_assessment_stats(self, assessment_type: str):
        """Update assessment statistics"""
        self.analytics_data['total_assessments'] += 1
        if assessment_type not in self.analytics_data['assessment_types']:
            self.analytics_data['assessment_types'][assessment_type] = 0
        self.analytics_data['assessment_types'][assessment_type] += 1
        
        # Update daily stats
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.analytics_data['daily_stats']:
            self.analytics_data['daily_stats'][today] = {'assessments': 0, 'sessions': 0}
        self.analytics_data['daily_stats'][today]['assessments'] += 1

class DSMAnalyzer:
    """DSM-5-TR based psychiatric symptom analyzer"""
    
    def __init__(self):
        self.dsm_criteria = self.load_dsm_criteria()
        self.psychiatrists = self.load_psychiatrists()
        
    def load_dsm_criteria(self) -> Dict:
        """Load DSM-5-TR diagnostic criteria"""
        try:
            with open('assets/dsm5_criteria.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("DSM-5-TR criteria file not found, using default criteria")
            return self.get_default_dsm_criteria()
    
    def load_psychiatrists(self) -> List[Dict]:
        """Load psychiatrist database"""
        try:
            psychiatrists = []
            with open('assets/psychiatrists.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert languages string to list
                    row['languages'] = row['languages'].split(',')
                    psychiatrists.append(row)
            return psychiatrists
        except FileNotFoundError:
            logger.warning("Psychiatrist database not found, using sample data")
            return self.get_sample_psychiatrists()
    
    def get_default_dsm_criteria(self) -> Dict:
        """Default DSM-5-TR criteria for common disorders"""
        return {
            "major_depressive_disorder": {
                "code": "296.2x",
                "name": "Major Depressive Disorder",
                "criteria": {
                    "A": "Five (or more) of the following symptoms during the same 2-week period",
                    "symptoms": [
                        "Depressed mood most of the day",
                        "Markedly diminished interest or pleasure",
                        "Significant weight loss or gain",
                        "Insomnia or hypersomnia",
                        "Psychomotor agitation or retardation",
                        "Fatigue or loss of energy",
                        "Feelings of worthlessness or guilt",
                        "Diminished ability to think or concentrate",
                        "Recurrent thoughts of death or suicide"
                    ]
                },
                "keywords": ["depression", "sad", "hopeless", "worthless", "suicide", "sleep", "appetite", "energy", "concentration"]
            },
            "generalized_anxiety_disorder": {
                "code": "300.02",
                "name": "Generalized Anxiety Disorder",
                "criteria": {
                    "A": "Excessive anxiety and worry for at least 6 months",
                    "symptoms": [
                        "Restlessness or feeling on edge",
                        "Being easily fatigued",
                        "Difficulty concentrating",
                        "Irritability",
                        "Muscle tension",
                        "Sleep disturbance"
                    ]
                },
                "keywords": ["anxiety", "worry", "nervous", "restless", "tension", "panic", "fear", "stress"]
            },
            "panic_disorder": {
                "code": "300.01",
                "name": "Panic Disorder",
                "criteria": {
                    "A": "Recurrent unexpected panic attacks",
                    "symptoms": [
                        "Palpitations or accelerated heart rate",
                        "Sweating",
                        "Trembling or shaking",
                        "Shortness of breath",
                        "Feelings of choking",
                        "Chest pain or discomfort",
                        "Nausea or abdominal distress",
                        "Feeling dizzy or lightheaded",
                        "Chills or heat sensations",
                        "Paresthesias",
                        "Derealization or depersonalization",
                        "Fear of losing control",
                        "Fear of dying"
                    ]
                },
                "keywords": ["panic", "attack", "heart", "breathing", "chest", "dizzy", "fear", "control", "dying"]
            },
            "bipolar_disorder": {
                "code": "296.xx",
                "name": "Bipolar Disorder",
                "criteria": {
                    "manic_episode": "Distinct period of abnormally elevated mood",
                    "symptoms": [
                        "Inflated self-esteem or grandiosity",
                        "Decreased need for sleep",
                        "More talkative than usual",
                        "Flight of ideas or racing thoughts",
                        "Distractibility",
                        "Increased goal-directed activity",
                        "Excessive involvement in risky activities"
                    ]
                },
                "keywords": ["manic", "mania", "elevated", "grandiose", "sleep", "talkative", "racing", "risky", "mood swings"]
            },
            "adhd": {
                "code": "314.xx",
                "name": "Attention-Deficit/Hyperactivity Disorder",
                "criteria": {
                    "inattention": "Six or more symptoms of inattention for at least 6 months",
                    "hyperactivity": "Six or more symptoms of hyperactivity-impulsivity for at least 6 months"
                },
                "keywords": ["attention", "hyperactive", "impulsive", "focus", "concentrate", "restless", "fidget", "interrupt"]
            },
            "ptsd": {
                "code": "309.81",
                "name": "Post-Traumatic Stress Disorder",
                "criteria": {
                    "A": "Exposure to actual or threatened death, serious injury, or sexual violence",
                    "symptoms": [
                        "Intrusive memories or dreams",
                        "Dissociative reactions (flashbacks)",
                        "Intense psychological distress",
                        "Avoidance of trauma-related stimuli",
                        "Negative alterations in cognitions and mood",
                        "Alterations in arousal and reactivity"
                    ]
                },
                "keywords": ["trauma", "flashback", "nightmare", "avoidance", "hypervigilant", "startle", "intrusive", "dissociation"]
            }
        }
    
    def get_sample_psychiatrists(self) -> List[Dict]:
        """Sample psychiatrist data"""
        return [
            {
                "name": "Dr. Sarah Chen",
                "specialty": "General Psychiatry",
                "subspecialty": "Depression, Anxiety Disorders",
                "languages": ["English", "Mandarin"],
                "location": "Downtown Medical Center",
                "phone": "(555) 123-4567",
                "experience": "15 years",
                "approach": "Cognitive Behavioral Therapy, Medication Management"
            },
            {
                "name": "Dr. Michael Rodriguez",
                "specialty": "Child & Adolescent Psychiatry",
                "subspecialty": "ADHD, Autism Spectrum Disorders",
                "languages": ["English", "Spanish"],
                "location": "Children's Mental Health Clinic",
                "phone": "(555) 234-5678",
                "experience": "12 years",
                "approach": "Family Therapy, Behavioral Interventions"
            },
            {
                "name": "Dr. Emily Johnson",
                "specialty": "Trauma & PTSD Specialist",
                "subspecialty": "EMDR, Complex Trauma",
                "languages": ["English", "French"],
                "location": "Trauma Recovery Center",
                "phone": "(555) 345-6789",
                "experience": "18 years",
                "approach": "EMDR, Somatic Therapies"
            }
        ]
    
    def analyze_whiteley_responses(self, responses: Dict[str, int], age: int, duration: str) -> Dict:
        """Analyze Whiteley 7 questionnaire responses"""
        
        # Calculate Whiteley 7 total score (0-28)
        total_score = sum(responses.values())
        
        # Interpret Whiteley 7 scores
        if total_score >= 21:
            severity = "severe"
            interpretation = "High health anxiety - significant hypochondriacal concerns"
        elif total_score >= 14:
            severity = "moderate"
            interpretation = "Moderate health anxiety - some hypochondriacal concerns"
        elif total_score >= 7:
            severity = "mild"
            interpretation = "Mild health anxiety - minimal hypochondriacal concerns"
        else:
            severity = "minimal"
            interpretation = "Minimal health anxiety - within normal range"
        
        # Generate DSM-5-TR matches based on Whiteley scores
        matches = []
        
        # Health Anxiety/Illness Anxiety Disorder
        if total_score >= 14:
            confidence = min(((total_score - 14) / 14) * 100 + 50, 95)
            matches.append({
                "disorder": "Illness Anxiety Disorder",
                "disorder_zh": "疾病焦慮症",
                "code": "300.3",
                "confidence": confidence,
                "matched_keywords": ["health anxiety", "somatic concerns", "illness preoccupation"],
                "matched_keywords_zh": ["健康焦慮", "身體症狀關注", "疾病專注"],
                "criteria": {
                    "A": "Preoccupation with having or acquiring a serious illness",
                    "B": "Somatic symptoms are not present or mild in intensity",
                    "C": "High level of anxiety about health"
                }
            })
        
        # Somatic Symptom Disorder (if high symptom awareness)
        if responses.get('q2', 0) >= 3 or responses.get('q6', 0) >= 3 or responses.get('q7', 0) >= 3:
            confidence = min(((responses.get('q2', 0) + responses.get('q6', 0) + responses.get('q7', 0)) / 12) * 100, 90)
            matches.append({
                "disorder": "Somatic Symptom Disorder",
                "disorder_zh": "身體症狀障礙症",
                "code": "300.82",
                "confidence": confidence,
                "matched_keywords": ["multiple symptoms", "body awareness", "aches and pains"],
                "matched_keywords_zh": ["多種症狀", "身體覺察", "疼痛不適"],
                "criteria": {
                    "A": "One or more somatic symptoms that are distressing",
                    "B": "Excessive thoughts, feelings, or behaviors related to symptoms",
                    "C": "Symptoms persist for more than 6 months"
                }
            })
        
        # Generalized Anxiety Disorder (if high worry)
        if responses.get('q1', 0) >= 3:
            confidence = min((responses.get('q1', 0) / 4) * 80, 85)
            matches.append({
                "disorder": "Generalized Anxiety Disorder",
                "disorder_zh": "廣泛性焦慮症",
                "code": "300.02",
                "confidence": confidence,
                "matched_keywords": ["excessive worry", "health concerns", "anxiety"],
                "matched_keywords_zh": ["過度擔憂", "健康關注", "焦慮"],
                "criteria": {
                    "A": "Excessive anxiety and worry for at least 6 months",
                    "B": "Difficult to control worry",
                    "C": "Associated with physical symptoms"
                }
            })
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "whiteley_score": total_score,
            "severity": severity,
            "interpretation": interpretation,
            "analysis": matches[:3],
            "recommendations": self.get_whiteley_recommendations(total_score, severity, age)
        }
    
    def get_whiteley_recommendations(self, score: int, severity: str, age: int) -> List[str]:
        """Generate recommendations based on Whiteley 7 results"""
        recommendations = [
            "This assessment is for screening purposes only and does not constitute a medical diagnosis.",
            "Please consult with a qualified mental health professional for proper evaluation."
        ]
        
        if severity == "severe":
            recommendations.extend([
                "Your responses suggest significant health anxiety that may benefit from professional treatment.",
                "Consider cognitive-behavioral therapy (CBT) specifically for health anxiety.",
                "Mindfulness and relaxation techniques may help manage anxiety symptoms.",
                "Avoid excessive medical consultations or internet health searches."
            ])
        elif severity == "moderate":
            recommendations.extend([
                "Your responses indicate moderate health anxiety that could benefit from intervention.",
                "Consider speaking with a counselor about your health concerns.",
                "Practice stress management and relaxation techniques.",
                "Limit health-related internet searches and focus on reliable medical sources."
            ])
        elif severity == "mild":
            recommendations.extend([
                "Your responses show mild health anxiety, which is manageable with self-care.",
                "Regular exercise and stress management can help reduce anxiety.",
                "Maintain regular medical check-ups but avoid excessive health monitoring."
            ])
        else:
            recommendations.extend([
                "Your responses indicate minimal health anxiety, which is within normal range.",
                "Continue maintaining healthy lifestyle habits.",
                "Regular medical care as recommended by your healthcare provider is sufficient."
            ])
        
        return recommendations
    
    def analyze_phq9_responses(self, responses: Dict[str, int], age: int, duration: str) -> Dict:
        """Analyze PHQ-9 questionnaire responses for depression screening"""
        
        # Calculate PHQ-9 total score (0-27)
        total_score = sum(responses.values())
        
        # Interpret PHQ-9 scores
        if total_score >= 20:
            severity = "severe"
            interpretation = "Severe depression"
        elif total_score >= 15:
            severity = "moderately_severe"
            interpretation = "Moderately severe depression"
        elif total_score >= 10:
            severity = "moderate"
            interpretation = "Moderate depression"
        elif total_score >= 5:
            severity = "mild"
            interpretation = "Mild depression"
        else:
            severity = "minimal"
            interpretation = "Minimal depression"
        
        # Generate DSM-5-TR matches based on PHQ-9 scores
        matches = []
        
        if total_score >= 10:
            confidence = min(((total_score - 10) / 17) * 100 + 60, 95)
            matches.append({
                "disorder": "Major Depressive Disorder",
                "disorder_zh": "重度憂鬱症",
                "code": "296.2x",
                "confidence": confidence,
                "matched_keywords": ["depression", "low mood", "anhedonia", "sleep disturbance"],
                "matched_keywords_zh": ["憂鬱", "情緒低落", "失樂症", "睡眠障礙"],
                "criteria": {
                    "A": "Five or more symptoms present during 2-week period",
                    "B": "Symptoms cause significant distress or impairment",
                    "C": "Not attributable to substance use or medical condition"
                }
            })
        
        if total_score >= 5:
            confidence = min(((total_score - 5) / 22) * 80 + 40, 85)
            matches.append({
                "disorder": "Persistent Depressive Disorder",
                "disorder_zh": "持續性憂鬱症",
                "code": "300.4",
                "confidence": confidence,
                "matched_keywords": ["chronic depression", "persistent low mood", "dysthymia"],
                "matched_keywords_zh": ["慢性憂鬱", "持續低落情緒", "輕鬱症"],
                "criteria": {
                    "A": "Depressed mood for most days for at least 2 years",
                    "B": "Two or more additional symptoms present",
                    "C": "Symptoms cause significant distress or impairment"
                }
            })
        
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "phq9_score": total_score,
            "severity": severity,
            "interpretation": interpretation,
            "analysis": matches[:3],
            "recommendations": self.get_phq9_recommendations(total_score, severity, age)
        }
    
    def analyze_gad7_responses(self, responses: Dict[str, int], age: int, duration: str) -> Dict:
        """Analyze GAD-7 questionnaire responses for anxiety screening"""
        
        # Calculate GAD-7 total score (0-21)
        total_score = sum(responses.values())
        
        # Interpret GAD-7 scores
        if total_score >= 15:
            severity = "severe"
            interpretation = "Severe anxiety"
        elif total_score >= 10:
            severity = "moderate"
            interpretation = "Moderate anxiety"
        elif total_score >= 5:
            severity = "mild"
            interpretation = "Mild anxiety"
        else:
            severity = "minimal"
            interpretation = "Minimal anxiety"
        
        # Generate DSM-5-TR matches based on GAD-7 scores
        matches = []
        
        if total_score >= 10:
            confidence = min(((total_score - 10) / 11) * 100 + 70, 95)
            matches.append({
                "disorder": "Generalized Anxiety Disorder",
                "disorder_zh": "廣泛性焦慮症",
                "code": "300.02",
                "confidence": confidence,
                "matched_keywords": ["anxiety", "worry", "restlessness", "muscle tension"],
                "matched_keywords_zh": ["焦慮", "擔心", "不安", "肌肉緊張"],
                "criteria": {
                    "A": "Excessive anxiety and worry for at least 6 months",
                    "B": "Difficult to control the worry",
                    "C": "Associated with physical symptoms"
                }
            })
        
        if total_score >= 8:
            confidence = min(((total_score - 8) / 13) * 85 + 50, 90)
            matches.append({
                "disorder": "Panic Disorder",
                "disorder_zh": "恐慌症",
                "code": "300.01",
                "confidence": confidence,
                "matched_keywords": ["panic attacks", "fear", "physical symptoms", "avoidance"],
                "matched_keywords_zh": ["恐慌發作", "恐懼", "身體症狀", "迴避"],
                "criteria": {
                    "A": "Recurrent unexpected panic attacks",
                    "B": "Persistent concern about additional attacks",
                    "C": "Significant behavioral changes"
                }
            })
        
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "gad7_score": total_score,
            "severity": severity,
            "interpretation": interpretation,
            "analysis": matches[:3],
            "recommendations": self.get_gad7_recommendations(total_score, severity, age)
        }
    
    def get_phq9_recommendations(self, score: int, severity: str, age: int) -> List[str]:
        """Generate recommendations based on PHQ-9 results"""
        recommendations = [
            "This assessment is for screening purposes only and does not constitute a medical diagnosis.",
            "Please consult with a qualified mental health professional for proper evaluation."
        ]
        
        if severity == "severe":
            recommendations.extend([
                "Your responses suggest severe depression that requires immediate professional attention.",
                "Consider contacting a mental health crisis line if you have thoughts of self-harm.",
                "Seek evaluation for medication and/or psychotherapy.",
                "Consider cognitive-behavioral therapy (CBT) or interpersonal therapy (IPT)."
            ])
        elif severity == "moderately_severe":
            recommendations.extend([
                "Your responses indicate moderately severe depression that would benefit from treatment.",
                "Consider scheduling an appointment with a mental health professional.",
                "Psychotherapy and/or medication may be helpful.",
                "Maintain social connections and engage in pleasant activities when possible."
            ])
        elif severity == "moderate":
            recommendations.extend([
                "Your responses suggest moderate depression that could benefit from intervention.",
                "Consider counseling or therapy to address your symptoms.",
                "Regular exercise, good sleep hygiene, and stress management may help.",
                "Monitor your symptoms and seek help if they worsen."
            ])
        elif severity == "mild":
            recommendations.extend([
                "Your responses indicate mild depression symptoms.",
                "Consider lifestyle changes such as regular exercise and stress reduction.",
                "Monitor your mood and seek professional help if symptoms persist or worsen.",
                "Maintain social connections and engage in enjoyable activities."
            ])
        
        return recommendations
    
    def get_gad7_recommendations(self, score: int, severity: str, age: int) -> List[str]:
        """Generate recommendations based on GAD-7 results"""
        recommendations = [
            "This assessment is for screening purposes only and does not constitute a medical diagnosis.",
            "Please consult with a qualified mental health professional for proper evaluation."
        ]
        
        if severity == "severe":
            recommendations.extend([
                "Your responses suggest severe anxiety that would benefit from professional treatment.",
                "Consider cognitive-behavioral therapy (CBT) specifically for anxiety disorders.",
                "Medication may be helpful in combination with therapy.",
                "Practice relaxation techniques such as deep breathing and mindfulness."
            ])
        elif severity == "moderate":
            recommendations.extend([
                "Your responses indicate moderate anxiety that could benefit from intervention.",
                "Consider speaking with a counselor about anxiety management strategies.",
                "Regular exercise, adequate sleep, and stress reduction techniques may help.",
                "Limit caffeine and alcohol intake as they can worsen anxiety."
            ])
        elif severity == "mild":
            recommendations.extend([
                "Your responses show mild anxiety symptoms.",
                "Practice stress management and relaxation techniques.",
                "Regular exercise and good sleep hygiene can help reduce anxiety.",
                "Monitor your symptoms and seek help if they worsen."
            ])
        
        return recommendations
    
    def analyze_symptoms_text(self, symptoms: str, age: int, duration: str, language: str = 'en') -> Dict:
        """Analyze free-text symptoms using expanded DSM-5-TR criteria"""
        symptoms_lower = symptoms.lower()
        matches = []
        
        for disorder_key, disorder_data in self.dsm_criteria.items():
            score = 0
            matched_keywords = []
            
            # Use appropriate keywords based on language
            keywords = disorder_data.get("keywords_zh", []) if language == 'zh' else disorder_data.get("keywords", [])
            
            # Check for keyword matches
            for keyword in keywords:
                if keyword.lower() in symptoms_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                confidence = min(score / len(keywords) * 100, 95)
                
                # Prepare disorder info with translations
                disorder_info = {
                    "disorder": disorder_data["name"],
                    "code": disorder_data["code"],
                    "confidence": confidence,
                    "matched_keywords": matched_keywords,
                    "criteria": disorder_data["criteria"]
                }
                
                # Add Chinese translations if available
                if language == 'zh':
                    disorder_info["disorder_zh"] = disorder_data.get("name_zh", disorder_data["name"])
                    disorder_info["matched_keywords_zh"] = matched_keywords
                else:
                    disorder_info["disorder_zh"] = disorder_data.get("name_zh")
                    disorder_info["matched_keywords_zh"] = disorder_data.get("keywords_zh", [])[:len(matched_keywords)]
                
                matches.append(disorder_info)
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "analysis": matches[:5],  # Top 5 matches
            "recommendations": self.get_recommendations(matches, age)
        }
    
    def get_recommendations(self, matches: List[Dict], age: int) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = [
            "This analysis is for informational purposes only and does not constitute a medical diagnosis.",
            "Please consult with a qualified mental health professional for proper evaluation.",
            "Consider keeping a mood/symptom diary to track patterns."
        ]
        
        if matches:
            top_match = matches[0]
            if "depression" in top_match["disorder"].lower():
                recommendations.extend([
                    "Consider screening for suicidal ideation if depressive symptoms are present.",
                    "Evaluate for medical conditions that may contribute to mood symptoms."
                ])
            elif "anxiety" in top_match["disorder"].lower():
                recommendations.extend([
                    "Consider ruling out medical causes of anxiety (thyroid, cardiac issues).",
                    "Assess for substance use that may contribute to anxiety symptoms."
                ])
            elif "trauma" in top_match["disorder"].lower() or "ptsd" in top_match["disorder"].lower():
                recommendations.extend([
                    "Trauma-informed care approach is essential.",
                    "Consider specialized trauma therapy (EMDR, CPT, PE)."
                ])
        
        return recommendations
    
    def find_matching_psychiatrists(self, analysis: Dict, location_preference: str = "", language_preference: str = "") -> List[Dict]:
        """Find psychiatrists based on analysis results"""
        if not analysis["analysis"]:
            return self.psychiatrists[:3]  # Return general psychiatrists
        
        top_disorder = analysis["analysis"][0]["disorder"].lower()
        matched_psychiatrists = []
        
        for psychiatrist in self.psychiatrists:
            score = 0
            
            # Check specialty match
            specialty_lower = psychiatrist["subspecialty"].lower()
            if any(keyword in specialty_lower for keyword in ["depression", "anxiety"] if keyword in top_disorder):
                score += 3
            elif "trauma" in top_disorder and "trauma" in specialty_lower:
                score += 3
            elif "adhd" in top_disorder and "adhd" in specialty_lower:
                score += 3
            elif "bipolar" in top_disorder and "bipolar" in specialty_lower:
                score += 3
            
            # Check language preference
            if language_preference and language_preference in psychiatrist["languages"]:
                score += 2
            
            # Check location preference
            if location_preference and location_preference.lower() in psychiatrist["location"].lower():
                score += 1
            
            psychiatrist["match_score"] = score
            matched_psychiatrists.append(psychiatrist)
        
        # Sort by match score
        matched_psychiatrists.sort(key=lambda x: x["match_score"], reverse=True)
        return matched_psychiatrists[:5]

# Initialize services
db_manager = DatabaseManager()
llm_service = LLMService()
analyzer = DSMAnalyzer()
admin_manager = AdminManager()

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_session_id = session.get('admin_session_id')
        if not admin_session_id or not admin_manager.validate_admin_session(admin_session_id):
            return jsonify({"error": "Admin authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            admin_session_id = session.get('admin_session_id')
            if not admin_session_id or not admin_manager.validate_admin_session(admin_session_id):
                return jsonify({"error": "Admin authentication required"}), 401
            
            admin_session = db_manager.get_admin_session(admin_session_id)
            if not admin_session or permission not in admin_session.get('permissions', []):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze Whiteley questionnaire responses and recommend psychiatrists"""
    try:
        data = request.json
        
        # Extract form data
        age = int(data.get('age', 25))
        duration = data.get('duration', '')
        location = data.get('location', '')
        language = data.get('language', 'English')
        
        # Extract assessment type and responses
        assessment_type = data.get('assessment_type', 'whiteley')
        
        # Extract questionnaire responses
        responses = {}
        question_count = 7  # Default for Whiteley
        
        if assessment_type == 'phq9':
            question_count = 9
        elif assessment_type == 'gad7':
            question_count = 7
        elif assessment_type == 'whiteley':
            question_count = 7
        
        for i in range(1, question_count + 1):
            q_key = f'q{i}'
            if q_key in data:
                responses[q_key] = int(data[q_key])
        
        # Validate input
        if len(responses) != question_count:
            return jsonify({"error": "Please complete all questionnaire items"}), 400
        
        # Analyze responses based on assessment type
        if assessment_type == 'whiteley':
            analysis = analyzer.analyze_whiteley_responses(responses, age, duration)
        elif assessment_type == 'phq9':
            analysis = analyzer.analyze_phq9_responses(responses, age, duration)
        elif assessment_type == 'gad7':
            analysis = analyzer.analyze_gad7_responses(responses, age, duration)
        else:
            # Default to Whiteley
            analysis = analyzer.analyze_whiteley_responses(responses, age, duration)
        
        # Find matching psychiatrists
        psychiatrists = analyzer.find_matching_psychiatrists(
            analysis, location, language
        )
        
        # Generate LLM-powered detailed report
        current_lang = 'zh' if language == 'Traditional Chinese' else 'en'
        
        # Get chat history for context
        session_id = data.get('session_id', '')
        chat_history = []
        if session_id:
            chat_history = db_manager.get_chat_history(session_id)
            logger.info(f"Retrieved {len(chat_history)} messages from chat history for session {session_id}")
        
        # Create comprehensive symptom summary including chat context
        if assessment_type == 'whiteley':
            assessment_summary = f"Whiteley 7 Health Anxiety Assessment completed. Total score: {analysis['whiteley_score']}/28. Severity: {analysis['severity']}. {analysis['interpretation']}"
        elif assessment_type == 'phq9':
            assessment_summary = f"PHQ-9 Depression Assessment completed. Total score: {analysis['phq9_score']}/27. Severity: {analysis['severity']}. {analysis['interpretation']}"
        elif assessment_type == 'gad7':
            assessment_summary = f"GAD-7 Anxiety Assessment completed. Total score: {analysis['gad7_score']}/21. Severity: {analysis['severity']}. {analysis['interpretation']}"
        else:
            # Generic fallback
            assessment_summary = f"Mental health assessment completed. Severity: {analysis.get('severity', 'unknown')}. {analysis.get('interpretation', 'Assessment results available.')}"
        
        # Combine assessment results with chat context
        if chat_history and len(chat_history) > 0:
            # Filter out system messages and format conversation
            user_messages = [msg for msg in chat_history if msg.get('role') in ['user', 'assistant']]
            if user_messages:
                # Format conversation for clinical analysis
                chat_context = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in user_messages[-10:]])  # Last 10 messages
                symptom_summary = f"{assessment_summary}\n\nPatient Conversation History:\n{chat_context}\n\nPlease incorporate insights from both the assessment scores and the conversation history to provide a comprehensive clinical analysis."
                logger.info(f"Including {len(user_messages)} chat messages in clinical report for session {session_id}")
            else:
                symptom_summary = assessment_summary
                logger.info(f"No user/assistant messages found in chat history for session {session_id}")
        else:
            symptom_summary = assessment_summary
            logger.info(f"No chat history found for session {session_id}")
        
        # Generate clinical report once at backend
        unredacted_report = llm_service.generate_analysis_report(
            symptom_summary, age, duration, analysis["analysis"], current_lang
        )
        
        # Create redacted version for frontend (filter out medication recommendations)
        redacted_report = filter_medication_recommendations(unredacted_report, current_lang)
        
        # Save assessment results to database with unredacted report for admin access
        session_id = data.get('session_id', '')
        if session_id:
            db_manager.save_assessment_result(
                session_id=session_id,
                assessment_type=assessment_type,
                responses=data,
                score=analysis.get('whiteley_score') or analysis.get('phq9_score') or analysis.get('gad7_score') or 0,
                severity=analysis.get('severity', 'unknown'),
                interpretation=analysis.get('interpretation', ''),
                dsm_analysis=analysis.get('analysis', []),
                clinical_report=unredacted_report  # Store unredacted version for admin
            )
            
            # Log the clinical report generation for audit trail
            db_manager.log_system_event('clinical_report_generated', {
                'session_id': session_id,
                'assessment_type': assessment_type,
                'report_length': len(unredacted_report),
                'redacted_length': len(redacted_report),
                'language': current_lang
            }, session_id)
        
        # Prepare response with redacted report for frontend
        response = {
            "analysis": analysis,
            "psychiatrists": psychiatrists,
            "detailed_report": redacted_report,  # Send redacted version to frontend
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({"error": "Analysis failed. Please try again."}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle LLM-powered chat conversation"""
    try:
        data = request.json
        
        # Extract chat data
        session_id = data.get('session_id', 'default')
        user_message = data.get('message', '')
        language = data.get('language', 'en')
        
        # Validate input
        if not user_message.strip():
            return jsonify({"error": "Please provide a message"}), 400
        
        # Get LLM response
        response_data = llm_service.chat_conversation(session_id, user_message, language)
        
        # Log session start event
        if user_message in ["START_CONVERSATION", "FRESH_START_CONVERSATION"]:
            db_manager.log_system_event('session_start', {'language': language}, session_id)
        
        # Prepare response
        response = {
            "message": response_data["message"],
            "assessment_recommendation": response_data.get("assessment_recommendation", "none"),
            "conversation_stage": response_data.get("conversation_stage", "support"),
            "follow_up_questions": response_data.get("follow_up_questions", []),
            "psychoeducation": response_data.get("psychoeducation", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Chat failed. Please try again."}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "PsyFind"})

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login endpoint"""
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if admin_manager.authenticate_admin(username, password):
            admin_session_id = admin_manager.create_admin_session(username)
            session['admin_session_id'] = admin_session_id
            logger.info(f"Admin login successful: {username}")
            return jsonify({"success": True, "redirect": "/admin/dashboard"})
        else:
            logger.warning(f"Admin login failed: {username}")
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    """Admin logout endpoint"""
    admin_session_id = session.get('admin_session_id')
    if admin_session_id:
        db_manager.terminate_admin_session(admin_session_id)
    session.pop('admin_session_id', None)
    return jsonify({"success": True})

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('admin_dashboard.html')

@app.route('/admin/api/analytics')
@admin_permission_required('view_analytics')
def admin_analytics():
    """Get analytics data"""
    try:
        analytics = admin_manager.get_analytics_data()
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Admin analytics error: {str(e)}")
        return jsonify({"error": "Failed to fetch analytics"}), 500

@app.route('/admin/api/sessions')
@admin_permission_required('view_sessions')
def admin_sessions():
    """Get active sessions"""
    try:
        sessions = admin_manager.get_active_sessions()
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Admin sessions error: {str(e)}")
        return jsonify({"error": "Failed to fetch sessions"}), 500

@app.route('/admin/api/sessions/<session_id>/terminate', methods=['POST'])
@admin_permission_required('manage_sessions')
def admin_terminate_session(session_id):
    """Terminate a user session"""
    try:
        # Find full session ID (since we only show truncated ones)
        full_session_id = None
        active_sessions = db_manager.get_active_sessions()
        for session in active_sessions:
            if session['session_id'].startswith(session_id.replace('...', '')):
                full_session_id = session['session_id']
                break
        
        if full_session_id and admin_manager.terminate_session(full_session_id):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Session not found"}), 404
            
    except Exception as e:
        logger.error(f"Admin terminate session error: {str(e)}")
        return jsonify({"error": "Failed to terminate session"}), 500

@app.route('/admin/api/system/health')
@admin_permission_required('system_control')
def admin_system_health():
    """Get system health information"""
    try:
        stats = db_manager.get_system_stats()
        health_data = {
            'uptime': (datetime.now() - admin_manager.system_start_time).total_seconds(),
            'memory_usage': admin_manager._get_memory_usage(),
            'llm_status': admin_manager._check_llm_status(),
            'active_sessions': stats['active_sessions'],
            'total_sessions': stats['total_sessions'],
            'total_assessments': stats['total_assessments']
        }
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Admin system health error: {str(e)}")
        return jsonify({"error": "Failed to fetch system health"}), 500

@app.route('/admin/api/system/cleanup', methods=['POST'])
@admin_permission_required('system_control')
def admin_cleanup_sessions():
    """Cleanup expired sessions"""
    try:
        initial_count = len(db_manager.get_active_sessions())
        cleaned = db_manager.cleanup_expired_sessions(timeout_hours=1)
        final_count = len(db_manager.get_active_sessions())
        
        return jsonify({
            "success": True, 
            "cleaned_sessions": cleaned,
            "remaining_sessions": final_count
        })
    except Exception as e:
        logger.error(f"Admin cleanup error: {str(e)}")
        return jsonify({"error": "Failed to cleanup sessions"}), 500

# Assessment Analytics Endpoints
@app.route('/admin/api/assessments/overview')
@admin_permission_required('view_analytics')
def admin_assessments_overview():
    """Get comprehensive assessment overview"""
    try:
        conn = db_manager.get_connection()
        
        # Recent assessments
        cursor = conn.execute('''
            SELECT assessment_type, score, severity, created_at, session_id
            FROM assessment_results 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        recent_assessments = [dict(row) for row in cursor.fetchall()]
        
        # Assessment distribution
        cursor = conn.execute('''
            SELECT assessment_type, severity, COUNT(*) as count
            FROM assessment_results 
            GROUP BY assessment_type, severity
            ORDER BY assessment_type, severity
        ''')
        distribution = [dict(row) for row in cursor.fetchall()]
        
        # Daily trends (last 30 days)
        cursor = conn.execute('''
            SELECT DATE(created_at) as date, assessment_type, COUNT(*) as count
            FROM assessment_results 
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY DATE(created_at), assessment_type
            ORDER BY date DESC
        ''')
        daily_trends = [dict(row) for row in cursor.fetchall()]
        
        # Average scores by type
        cursor = conn.execute('''
            SELECT assessment_type, AVG(score) as avg_score, COUNT(*) as total_count
            FROM assessment_results 
            GROUP BY assessment_type
        ''')
        avg_scores = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "recent_assessments": recent_assessments,
            "distribution": distribution,
            "daily_trends": daily_trends,
            "average_scores": avg_scores
        })
    except Exception as e:
        logger.error(f"Assessment overview error: {str(e)}")
        return jsonify({"error": "Failed to fetch assessment data"}), 500

@app.route('/admin/api/reports/generate', methods=['POST'])
@admin_permission_required('view_analytics')
def admin_generate_report():
    """Generate comprehensive system report"""
    try:
        data = request.get_json()
        report_type = data.get('type', 'summary')
        date_range = data.get('date_range', 7)  # days
        
        conn = db_manager.get_connection()
        
        # System summary
        cursor = conn.execute('''
            SELECT COUNT(*) as total_sessions FROM user_sessions
        ''')
        total_sessions = cursor.fetchone()['total_sessions']
        
        cursor = conn.execute('''
            SELECT COUNT(*) as total_assessments FROM assessment_results
        ''')
        total_assessments = cursor.fetchone()['total_assessments']
        
        # Recent activity
        cursor = conn.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as sessions
            FROM user_sessions 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        '''.format(date_range))
        session_activity = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute('''
            SELECT DATE(created_at) as date, assessment_type, COUNT(*) as count
            FROM assessment_results 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY DATE(created_at), assessment_type
            ORDER BY date DESC
        '''.format(date_range))
        assessment_activity = [dict(row) for row in cursor.fetchall()]
        
        # Performance metrics
        cursor = conn.execute('''
            SELECT assessment_type, AVG(score) as avg_score, 
                   MIN(score) as min_score, MAX(score) as max_score
            FROM assessment_results 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY assessment_type
        '''.format(date_range))
        performance_metrics = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_type": report_type,
            "date_range_days": date_range,
            "summary": {
                "total_sessions": total_sessions,
                "total_assessments": total_assessments,
                "active_sessions": len(db_manager.get_active_sessions())
            },
            "activity": {
                "sessions": session_activity,
                "assessments": assessment_activity
            },
            "performance": performance_metrics
        }
        
        return jsonify(report)
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return jsonify({"error": "Failed to generate report"}), 500

@app.route('/admin/api/logs')
@admin_permission_required('system_control')
def admin_system_logs():
    """Get system event logs"""
    try:
        limit = request.args.get('limit', 100, type=int)
        event_type = request.args.get('type', None)
        
        conn = db_manager.get_connection()
        
        query = '''
            SELECT event_type, event_data, session_id, timestamp
            FROM system_events 
        '''
        params = []
        
        if event_type:
            query += ' WHERE event_type = ?'
            params.append(event_type)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor = conn.execute(query, params)
        logs = []
        for row in cursor.fetchall():
            log_entry = dict(row)
            log_entry['event_data'] = json.loads(log_entry['event_data'])
            logs.append(log_entry)
        
        conn.close()
        
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"System logs error: {str(e)}")
        return jsonify({"error": "Failed to fetch logs"}), 500

@app.route('/admin/api/backup/create', methods=['POST'])
@admin_permission_required('system_control')
def admin_create_backup():
    """Create database backup"""
    try:
        import shutil
        from datetime import datetime
        
        backup_name = f"psyfind_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = f"backups/{backup_name}"
        
        # Create backups directory if it doesn't exist
        os.makedirs('backups', exist_ok=True)
        
        # Copy database file
        shutil.copy2(db_manager.db_path, backup_path)
        
        # Log backup event
        db_manager.log_system_event('backup_created', {'backup_file': backup_name})
        
        return jsonify({
            "success": True,
            "backup_file": backup_name,
            "backup_path": backup_path,
            "created_at": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Backup creation error: {str(e)}")
        return jsonify({"error": "Failed to create backup"}), 500

@app.route('/admin/api/backup/list')
@admin_permission_required('system_control')
def admin_list_backups():
    """List available backups"""
    try:
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            return jsonify({"backups": []})
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                file_stat = os.stat(file_path)
                backups.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({"backups": backups})
    except Exception as e:
        logger.error(f"Backup list error: {str(e)}")
        return jsonify({"error": "Failed to list backups"}), 500

@app.route('/admin/api/settings')
@admin_permission_required('system_control')
def admin_get_settings():
    """Get system settings"""
    try:
        settings = {
            "llm_provider": os.getenv('LLM_PROVIDER', 'auto'),
            "session_timeout": 3600,
            "max_sessions": 1000,
            "debug_mode": os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            "system_info": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "database_path": db_manager.db_path,
                "uptime": (datetime.now() - admin_manager.system_start_time).total_seconds()
            }
        }
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Settings fetch error: {str(e)}")
        return jsonify({"error": "Failed to fetch settings"}), 500

@app.route('/admin/api/settings', methods=['POST'])
@admin_permission_required('system_control')
def admin_update_settings():
    """Update system settings"""
    try:
        data = request.get_json()
        
        # Log settings change
        db_manager.log_system_event('settings_updated', data)
        
        return jsonify({"success": True, "message": "Settings updated successfully"})
    except Exception as e:
        logger.error(f"Settings update error: {str(e)}")
        return jsonify({"error": "Failed to update settings"}), 500

# Clinical Data Access Endpoints (Admin Only)
@app.route('/admin/api/clinical/sessions')
@admin_permission_required('view_analytics')
def admin_clinical_sessions():
    """Get sessions with clinical data access"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = db_manager.get_connection()
        
        # Get sessions with assessment data
        cursor = conn.execute('''
            SELECT DISTINCT us.session_id, us.created_at, us.last_activity, 
                   us.language, us.message_count, us.conversation_stage,
                   COUNT(ar.id) as assessment_count
            FROM user_sessions us
            LEFT JOIN assessment_results ar ON us.session_id = ar.session_id
            WHERE us.is_active = 1 OR ar.id IS NOT NULL
            GROUP BY us.session_id
            ORDER BY us.last_activity DESC
            LIMIT ?
        ''', (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            session_data = dict(row)
            
            # Get message count from chat_messages table
            msg_cursor = conn.execute('''
                SELECT COUNT(*) as msg_count FROM chat_messages WHERE session_id = ?
            ''', (session_data['session_id'],))
            session_data['actual_message_count'] = msg_cursor.fetchone()['msg_count']
            
            sessions.append(session_data)
        
        conn.close()
        
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Clinical sessions error: {str(e)}")
        return jsonify({"error": "Failed to fetch clinical sessions"}), 500

@app.route('/admin/api/clinical/session/<session_id>')
@admin_permission_required('view_analytics')
def admin_clinical_session_detail(session_id):
    """Get complete clinical data for a session"""
    try:
        conn = db_manager.get_connection()
        
        # Get session info
        cursor = conn.execute('''
            SELECT * FROM user_sessions WHERE session_id = ?
        ''', (session_id,))
        session_info = cursor.fetchone()
        
        if not session_info:
            return jsonify({"error": "Session not found"}), 404
        
        session_data = dict(session_info)
        
        # Get complete chat history (unfiltered)
        cursor = conn.execute('''
            SELECT role, content, timestamp, metadata
            FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        chat_history = []
        for row in cursor.fetchall():
            msg = dict(row)
            msg['metadata'] = json.loads(msg['metadata'])
            chat_history.append(msg)
        
        # Get assessment results with unredacted clinical reports
        cursor = conn.execute('''
            SELECT assessment_type, score, severity, interpretation, 
                   dsm_analysis, clinical_report, responses, created_at
            FROM assessment_results 
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))
        
        assessments = []
        for row in cursor.fetchall():
            assessment = dict(row)
            assessment['dsm_analysis'] = json.loads(assessment['dsm_analysis'])
            assessment['responses'] = json.loads(assessment['responses'])
            assessments.append(assessment)
        
        conn.close()
        
        return jsonify({
            "session_info": session_data,
            "chat_history": chat_history,
            "assessments": assessments,
            "total_messages": len(chat_history),
            "total_assessments": len(assessments)
        })
        
    except Exception as e:
        logger.error(f"Clinical session detail error: {str(e)}")
        return jsonify({"error": "Failed to fetch session details"}), 500

@app.route('/admin/api/clinical/reports')
@admin_permission_required('view_analytics')
def admin_clinical_reports():
    """Get all clinical reports (unredacted)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        assessment_type = request.args.get('type', None)
        
        conn = db_manager.get_connection()
        
        query = '''
            SELECT ar.*, us.language, us.created_at as session_created
            FROM assessment_results ar
            JOIN user_sessions us ON ar.session_id = us.session_id
        '''
        params = []
        
        if assessment_type:
            query += ' WHERE ar.assessment_type = ?'
            params.append(assessment_type)
        
        query += ' ORDER BY ar.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor = conn.execute(query, params)
        
        reports = []
        for row in cursor.fetchall():
            report = dict(row)
            report['dsm_analysis'] = json.loads(report['dsm_analysis'])
            report['responses'] = json.loads(report['responses'])
            # clinical_report contains unredacted version
            reports.append(report)
        
        conn.close()
        
        return jsonify({"reports": reports})
        
    except Exception as e:
        logger.error(f"Clinical reports error: {str(e)}")
        return jsonify({"error": "Failed to fetch clinical reports"}), 500

@app.route('/admin/api/clinical/export/<session_id>')
@admin_permission_required('system_control')
def admin_export_clinical_data(session_id):
    """Export complete clinical data for a session"""
    try:
        # Get complete session data
        response = admin_clinical_session_detail(session_id)
        if response.status_code != 200:
            return response
        
        session_data = response.get_json()
        
        # Create comprehensive clinical export
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "session_info": session_data["session_info"],
            "clinical_summary": {
                "total_messages": session_data["total_messages"],
                "total_assessments": session_data["total_assessments"],
                "conversation_duration": session_data["session_info"]["last_activity"],
                "language": session_data["session_info"]["language"]
            },
            "complete_chat_history": session_data["chat_history"],
            "assessment_results": session_data["assessments"],
            "admin_notes": "Complete clinical record with unredacted medication recommendations"
        }
        
        # Log export event
        db_manager.log_system_event('clinical_export', {
            'session_id': session_id,
            'exported_by': 'admin',
            'export_type': 'complete_clinical_record'
        }, session_id)
        
        return jsonify(export_data)
        
    except Exception as e:
        logger.error(f"Clinical export error: {str(e)}")
        return jsonify({"error": "Failed to export clinical data"}), 500

# Doctor Management API Endpoints
@app.route('/admin/api/doctors', methods=['GET'])
@admin_permission_required('view_analytics')
def admin_get_doctors():
    """Get all doctors"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
        doctors = db_manager.get_doctors(active_only=active_only, limit=limit)
        return jsonify({"doctors": doctors})
    except Exception as e:
        logger.error(f"Get doctors error: {str(e)}")
        return jsonify({"error": "Failed to fetch doctors"}), 500

@app.route('/admin/api/doctors', methods=['POST'])
@admin_permission_required('system_control')
def admin_create_doctor():
    """Create a new doctor"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'specialty', 'languages']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        doctor_id = db_manager.create_doctor(data)
        
        # Log doctor creation
        db_manager.log_system_event('doctor_created', {
            'doctor_id': doctor_id,
            'name': data.get('name'),
            'specialty': data.get('specialty')
        })
        
        return jsonify({"success": True, "doctor_id": doctor_id})
    except Exception as e:
        logger.error(f"Create doctor error: {str(e)}")
        return jsonify({"error": "Failed to create doctor"}), 500

@app.route('/admin/api/doctors/<int:doctor_id>', methods=['GET'])
@admin_permission_required('view_analytics')
def admin_get_doctor(doctor_id):
    """Get a specific doctor"""
    try:
        doctor = db_manager.get_doctor(doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        
        return jsonify({"doctor": doctor})
    except Exception as e:
        logger.error(f"Get doctor error: {str(e)}")
        return jsonify({"error": "Failed to fetch doctor"}), 500

@app.route('/admin/api/doctors/<int:doctor_id>', methods=['PUT'])
@admin_permission_required('system_control')
def admin_update_doctor(doctor_id):
    """Update a doctor"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'specialty', 'languages']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        success = db_manager.update_doctor(doctor_id, data)
        if not success:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Log doctor update
        db_manager.log_system_event('doctor_updated', {
            'doctor_id': doctor_id,
            'name': data.get('name'),
            'specialty': data.get('specialty')
        })
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Update doctor error: {str(e)}")
        return jsonify({"error": "Failed to update doctor"}), 500

@app.route('/admin/api/doctors/<int:doctor_id>', methods=['DELETE'])
@admin_permission_required('system_control')
def admin_delete_doctor(doctor_id):
    """Delete (deactivate) a doctor"""
    try:
        success = db_manager.delete_doctor(doctor_id)
        if not success:
            return jsonify({"error": "Doctor not found"}), 404
        
        # Log doctor deletion
        db_manager.log_system_event('doctor_deleted', {'doctor_id': doctor_id})
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Delete doctor error: {str(e)}")
        return jsonify({"error": "Failed to delete doctor"}), 500

@app.route('/admin/api/doctors/search', methods=['GET'])
@admin_permission_required('view_analytics')
def admin_search_doctors():
    """Search doctors"""
    try:
        query = request.args.get('q', '')
        specialty = request.args.get('specialty', None)
        
        if not query:
            return jsonify({"doctors": []})
        
        doctors = db_manager.search_doctors(query, specialty)
        return jsonify({"doctors": doctors})
    except Exception as e:
        logger.error(f"Search doctors error: {str(e)}")
        return jsonify({"error": "Failed to search doctors"}), 500

if __name__ == '__main__':
    # Create assets directory if it doesn't exist
    os.makedirs('assets', exist_ok=True)
    
    # Import doctors from CSV after database is ready
    try:
        db_manager._import_doctors_from_csv()
    except Exception as e:
        logger.error(f"Error during CSV import: {str(e)}")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
