"""
CardioGenie Database Models and Management
Production-ready database operations
"""

import sqlite3
import json
import os
from typing import List, Dict, Any
from datetime import datetime

class DatabaseManager:
    """Database management class for CardioGenie"""
    
    def __init__(self, db_path: str = "database/cardiogenie_production.db"):
        self.db_path = db_path
        self.ensure_database_directory()
    
    def ensure_database_directory(self):
        """Ensure database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def initialize_database(self, medical_dataset_path: str = "docs/Datasetab94d2b.json"):
        """Initialize database with tables and medical dataset"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create symptom rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptom_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symptom TEXT UNIQUE NOT NULL,
                follow_up_questions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create credentials table for persistent OAuth storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oauth_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT UNIQUE NOT NULL,
                token TEXT,
                refresh_token TEXT,
                token_uri TEXT,
                client_id TEXT,
                client_secret TEXT,
                scopes TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                age INTEGER,
                gender TEXT,
                symptoms TEXT,
                responses TEXT,
                status TEXT DEFAULT 'in_progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # Load comprehensive medical dataset
        symptom_rules = self._load_medical_dataset(medical_dataset_path)
        
        # Insert symptom rules
        for symptom, questions in symptom_rules.items():
            cursor.execute(
                'INSERT OR REPLACE INTO symptom_rules (symptom, follow_up_questions) VALUES (?, ?)',
                (symptom, json.dumps(questions))
            )
        
        conn.commit()
        conn.close()
        
        print(f"Database initialized with {len(symptom_rules)} symptoms")
        return True
    
    def _load_medical_dataset(self, dataset_path: str) -> Dict[str, List[str]]:
        """Load and process medical dataset"""
        try:
            with open(dataset_path, 'r') as f:
                medical_dataset = json.loads(f.read())
            
            symptom_rules = {}
            
            for item in medical_dataset:
                symptom = item['symptom'].lower()
                
                # Extract key questions from different categories
                questions = []
                
                # Get symptom details (most important)
                if 'symptom_details' in item['follow_up_questions']:
                    questions.extend(item['follow_up_questions']['symptom_details'][:2])
                
                # Add one vital signs question
                if 'vital_signs' in item['follow_up_questions']:
                    questions.extend(item['follow_up_questions']['vital_signs'][:1])
                
                # Add one red flag question for safety
                if 'red_flags' in item['follow_up_questions']:
                    questions.extend(item['follow_up_questions']['red_flags'][:1])
                
                # Limit to 4 questions max for efficiency
                questions = questions[:4]
                
                if questions:
                    symptom_rules[symptom] = questions
            
            print(f"Loaded {len(symptom_rules)} symptoms from medical dataset")
            return symptom_rules
            
        except Exception as e:
            print(f"❌ Error loading medical dataset: {e}")
            # Fallback to basic rules
            return {
                "chest pain": [
                    "When did the chest pain start?",
                    "Can you describe the pain (pressure, squeezing, sharp, burning)?",
                    "What is your current blood pressure and heart rate?",
                    "Is the chest pain sudden and severe?"
                ],
                "shortness of breath": [
                    "Is the breathlessness at rest or with exertion?",
                    "Do you have difficulty breathing when lying flat?",
                    "What is your resting oxygen saturation?",
                    "Is the shortness of breath sudden in onset?"
                ]
            }
    
    def get_symptom_questions(self, symptom: str) -> List[str]:
        """Get follow-up questions for a specific symptom"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT follow_up_questions FROM symptom_rules WHERE symptom = ?',
            (symptom.lower(),)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return []
    
    def save_patient_data(self, session_id: str, patient_data: Dict[str, Any]):
        """Save patient data to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO patients 
            (session_id, name, email, age, gender, symptoms, responses, status, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            patient_data.get('name'),
            patient_data.get('email'),
            patient_data.get('age'),
            patient_data.get('gender'),
            json.dumps(patient_data.get('symptoms', [])),
            json.dumps(patient_data.get('responses', {})),
            patient_data.get('status', 'in_progress'),
            patient_data.get('completed_at')
        ))
        
        conn.commit()
        conn.close()
    
    def get_patient_data(self, session_id: str) -> Dict[str, Any]:
        """Get patient data from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM patients WHERE session_id = ?',
            (session_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'session_id', 'name', 'email', 'age', 'gender', 
                      'symptoms', 'responses', 'status', 'created_at', 'completed_at']
            patient_data = dict(zip(columns, result))
            
            # Parse JSON fields
            patient_data['symptoms'] = json.loads(patient_data['symptoms'] or '[]')
            patient_data['responses'] = json.loads(patient_data['responses'] or '{}')
            
            return patient_data
        
        return {}
    
    def cleanup_database(self):
        """Clean up database - remove all data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Drop all tables
        cursor.execute("DROP TABLE IF EXISTS patients")
        cursor.execute("DROP TABLE IF EXISTS symptom_rules")
        
        conn.commit()
        conn.close()
        
        print("Database cleaned up successfully")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count symptoms
        cursor.execute("SELECT COUNT(*) FROM symptom_rules")
        stats['symptoms'] = cursor.fetchone()[0]
        
        # Count patients
        cursor.execute("SELECT COUNT(*) FROM patients")
        stats['patients'] = cursor.fetchone()[0]
        
        # Count completed consultations
        cursor.execute("SELECT COUNT(*) FROM patients WHERE status = 'completed'")
        stats['completed_consultations'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def save_oauth_credentials(self, service: str, credentials_data: Dict[str, Any]) -> bool:
        """Save OAuth credentials to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert scopes list to JSON string
            scopes_json = json.dumps(credentials_data.get('scopes', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO oauth_credentials 
                (service, token, refresh_token, token_uri, client_id, client_secret, scopes, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                service,
                credentials_data.get('token'),
                credentials_data.get('refresh_token'),
                credentials_data.get('token_uri'),
                credentials_data.get('client_id'),
                credentials_data.get('client_secret'),
                scopes_json,
                credentials_data.get('expires_at')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to save OAuth credentials: {e}")
            return False
    
    def load_oauth_credentials(self, service: str) -> Dict[str, Any]:
        """Load OAuth credentials from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT token, refresh_token, token_uri, client_id, client_secret, scopes, expires_at
                FROM oauth_credentials 
                WHERE service = ?
            ''', (service,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'token': result[0],
                    'refresh_token': result[1],
                    'token_uri': result[2],
                    'client_id': result[3],
                    'client_secret': result[4],
                    'scopes': json.loads(result[5]) if result[5] else [],
                    'expires_at': result[6]
                }
            else:
                return {}
                
        except Exception as e:
            print(f"❌ Failed to load OAuth credentials: {e}")
            return {}
    
    def delete_oauth_credentials(self, service: str) -> bool:
        """Delete OAuth credentials from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM oauth_credentials WHERE service = ?', (service,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete OAuth credentials: {e}")
            return False 