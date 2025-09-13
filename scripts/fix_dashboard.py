#!/usr/bin/env python3
"""
Fix Dashboard Script
Initializes database and tests dashboard functionality
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import DatabaseManager
from backend.config import Config

def initialize_database():
    """Initialize database with all required tables"""
    print("🔧 Initializing database...")
    
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_PATH)
    
    # Initialize database with medical dataset
    try:
        db_manager.initialize_database()
        print("✅ Database initialized successfully")
        
        # Check if tables exist
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tables created: {', '.join(tables)}")
        
        # Add some test data if no patients exist
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        
        if patient_count == 0:
            print("📝 Adding test patient data...")
            test_patients = [
                {
                    'session_id': 'test_001',
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'age': 45,
                    'gender': 'Male',
                    'symptoms': '["chest pain", "shortness of breath"]',
                    'responses': '{"chest_pain_duration": "2 hours", "pain_intensity": "7/10"}',
                    'status': 'completed',
                    'created_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat()
                },
                {
                    'session_id': 'test_002',
                    'name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'age': 32,
                    'gender': 'Female',
                    'symptoms': '["palpitations", "dizziness"]',
                    'responses': '{"palpitation_frequency": "daily", "dizzy_episodes": "3 times this week"}',
                    'status': 'in_progress',
                    'created_at': datetime.now().isoformat(),
                    'completed_at': None
                },
                {
                    'session_id': 'test_003',
                    'name': 'Bob Johnson',
                    'email': 'bob@example.com',
                    'age': 58,
                    'gender': 'Male',
                    'symptoms': '["fatigue", "chest pressure"]',
                    'responses': '{"fatigue_duration": "2 weeks", "pressure_location": "center chest"}',
                    'status': 'completed',
                    'created_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat()
                }
            ]
            
            for patient in test_patients:
                cursor.execute("""
                    INSERT INTO patients (session_id, name, email, age, gender, symptoms, responses, status, created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient['session_id'], patient['name'], patient['email'], 
                    patient['age'], patient['gender'], patient['symptoms'], 
                    patient['responses'], patient['status'], patient['created_at'], patient['completed_at']
                ))
            
            conn.commit()
            print(f"✅ Added {len(test_patients)} test patients")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_dashboard_data():
    """Test dashboard data generation"""
    print("\n🧪 Testing dashboard data generation...")
    
    try:
        config = Config()
        db_manager = DatabaseManager(config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]
        print(f"📊 Total patients: {total_patients}")
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        print(f"✅ Completed consultations: {completed}")
        
        cursor.execute("SELECT COUNT(*) FROM symptom_rules")
        symptoms = cursor.fetchone()[0]
        print(f"🏥 Symptom rules loaded: {symptoms}")
        
        cursor.execute("SELECT COUNT(*) FROM oauth_credentials")
        oauth_count = cursor.fetchone()[0]
        print(f"🔐 OAuth credentials: {oauth_count}")
        
        # Test recent consultations query
        cursor.execute("""
            SELECT session_id, name, email, age, gender, symptoms, responses, status, created_at, completed_at
            FROM patients 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        print(f"📋 Recent consultations: {len(recent)}")
        
        for row in recent:
            print(f"   - {row[1]} ({row[4]}, {row[3]}) - {row[7]}")
        
        conn.close()
        print("✅ Dashboard data test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard data test failed: {e}")
        return False

def main():
    """Main function"""
    print("🏥 CardioGenie Dashboard Fix Script")
    print("=" * 50)
    
    # Initialize database
    if not initialize_database():
        print("❌ Failed to initialize database")
        return
    
    # Test dashboard data
    if not test_dashboard_data():
        print("❌ Failed to test dashboard data")
        return
    
    print("\n🎉 Dashboard fix completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the backend server: python backend/main.py")
    print("2. Visit: http://localhost:8000/doctor")
    print("3. Or test API: curl http://localhost:8000/admin/dashboard")

if __name__ == "__main__":
    main() 