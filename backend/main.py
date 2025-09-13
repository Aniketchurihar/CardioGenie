"""
CardioGenie Production Backend
Professional AI Assistant for Cardiology Consultations
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import modular services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_config
from backend.services.ai_service import AIService
from backend.services.notification_service import NotificationService
from database.models import DatabaseManager

# Initialize configuration and services
config = get_config("development")  # Use "production" for production deployment
# config.validate_config()  # Temporarily disabled for Railway deployment

# Initialize services
db_manager = DatabaseManager(config.DATABASE_PATH)
ai_service = AIService(config)
notification_service = NotificationService(config)

# Patient session management
class PatientSession:
    """Patient session data model"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.name: Optional[str] = None
        self.email: Optional[str] = None
        self.age: Optional[int] = None
        self.gender: Optional[str] = None
        self.symptoms: List[str] = []
        self.responses: Dict[str, List[str]] = {}
        self.phase: str = "basic_info"
        self.current_symptom: Optional[str] = None
        self.current_question_index: int = 0
        self.conversation_history: List[str] = []

# WebSocket connection manager
class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.patient_sessions: Dict[str, PatientSession] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.patient_sessions[session_id] = PatientSession(session_id)

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.patient_sessions:
            del self.patient_sessions[session_id]

    async def send_message(self, session_id: str, message: str, sender: str = "ai"):
        if session_id in self.active_connections:
            response = {
                "type": sender,  # Frontend expects 'type' field with 'ai', 'user', or 'system'
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            await self.active_connections[session_id].send_text(json.dumps(response))

# Initialize FastAPI app
app = FastAPI(title="CardioGenie Production API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend (Railway deployment)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Initialize connection manager
manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    db_manager.initialize_database(config.MEDICAL_DATASET_PATH)

# API Endpoints
@app.get("/health")
async def health_check():
    """System health check endpoint"""
    stats = db_manager.get_database_stats()
    return {
        "status": "healthy",
        "database": config.DATABASE_URL,
        "symptoms_loaded": stats.get("symptoms", 0),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/admin/dashboard")
async def doctor_dashboard():
    """Comprehensive doctor dashboard with patient analytics"""
    try:
        from database.models import DatabaseManager
        import sqlite3
        import json
        from datetime import datetime, timedelta
        
        db_manager = DatabaseManager(config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get dashboard statistics
        dashboard_data = {
            "summary": {},
            "recent_consultations": [],
            "symptom_analytics": {},
            "patient_demographics": {},
            "system_status": {}
        }
        
        # Summary Statistics
        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE status = 'completed'")
        completed_consultations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE created_at >= datetime('now', '-24 hours')")
        patients_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE created_at >= datetime('now', '-7 days')")
        patients_this_week = cursor.fetchone()[0]
        
        dashboard_data["summary"] = {
            "total_patients": total_patients,
            "completed_consultations": completed_consultations,
            "patients_today": patients_today,
            "patients_this_week": patients_this_week,
            "completion_rate": round((completed_consultations / max(total_patients, 1)) * 100, 1)
        }
        
        # Recent Consultations (last 10)
        cursor.execute("""
            SELECT session_id, name, email, age, gender, symptoms, responses, status, created_at, updated_at
            FROM patients 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)
        recent_data = cursor.fetchall()
        
        for row in recent_data:
            consultation = {
                "session_id": row[0],
                "name": row[1] or "Not provided",
                "email": row[2] or "Not provided", 
                "age": row[3] or "Not provided",
                "gender": row[4] or "Not provided",
                "symptoms": json.loads(row[5]) if row[5] else [],
                "responses": json.loads(row[6]) if row[6] else {},
                "status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "duration_minutes": None
            }
            
            # Calculate consultation duration
            if row[8] and row[9]:
                try:
                    created = datetime.fromisoformat(row[8].replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(row[9].replace('Z', '+00:00'))
                    duration = (updated - created).total_seconds() / 60
                    consultation["duration_minutes"] = round(duration, 1)
                except:
                    pass
            
            dashboard_data["recent_consultations"].append(consultation)
        
        # Symptom Analytics
        cursor.execute("""
            SELECT symptoms FROM patients 
            WHERE symptoms IS NOT NULL AND symptoms != '[]'
        """)
        symptom_data = cursor.fetchall()
        
        symptom_counts = {}
        for row in symptom_data:
            try:
                symptoms = json.loads(row[0])
                for symptom in symptoms:
                    symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
            except:
                continue
        
        # Sort symptoms by frequency
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        dashboard_data["symptom_analytics"] = {
            "top_symptoms": sorted_symptoms[:10],
            "total_unique_symptoms": len(symptom_counts),
            "most_common": sorted_symptoms[0] if sorted_symptoms else None
        }
        
        # Patient Demographics
        cursor.execute("SELECT gender, COUNT(*) FROM patients WHERE gender IS NOT NULL GROUP BY gender")
        gender_data = cursor.fetchall()
        
        cursor.execute("SELECT age FROM patients WHERE age IS NOT NULL")
        age_data = cursor.fetchall()
        
        age_groups = {"18-30": 0, "31-45": 0, "46-60": 0, "60+": 0}
        for row in age_data:
            age = row[0]
            if age <= 30:
                age_groups["18-30"] += 1
            elif age <= 45:
                age_groups["31-45"] += 1
            elif age <= 60:
                age_groups["46-60"] += 1
            else:
                age_groups["60+"] += 1
        
        dashboard_data["patient_demographics"] = {
            "gender_distribution": dict(gender_data),
            "age_groups": age_groups,
            "average_age": round(sum(row[0] for row in age_data) / max(len(age_data), 1), 1) if age_data else 0
        }
        
        # System Status
        cursor.execute("SELECT COUNT(*) FROM symptom_rules")
        symptom_rules_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM oauth_credentials")
        oauth_status = cursor.fetchone()[0] > 0
        
        dashboard_data["system_status"] = {
            "symptom_rules_loaded": symptom_rules_count,
            "google_oauth_configured": oauth_status,
            "database_size_mb": round(os.path.getsize(config.DATABASE_PATH) / (1024*1024), 2),
            "last_updated": datetime.now().isoformat()
        }
        
        conn.close()
        return dashboard_data
        
    except Exception as e:
        return {"error": f"Dashboard generation failed: {str(e)}"}

@app.get("/admin/patients")
async def get_all_patients():
    """Get all patients with detailed information"""
    try:
        from database.models import DatabaseManager
        import json
        
        db_manager = DatabaseManager(config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, name, email, age, gender, symptoms, responses, status, created_at, updated_at
            FROM patients 
            ORDER BY created_at DESC
        """)
        
        patients = []
        for row in cursor.fetchall():
            patient = {
                "session_id": row[0],
                "name": row[1] or "Not provided",
                "email": row[2] or "Not provided",
                "age": row[3] or "Not provided", 
                "gender": row[4] or "Not provided",
                "symptoms": json.loads(row[5]) if row[5] else [],
                "responses": json.loads(row[6]) if row[6] else {},
                "status": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }
            patients.append(patient)
        
        conn.close()
        return {"patients": patients, "total_count": len(patients)}
        
    except Exception as e:
        return {"error": f"Failed to fetch patients: {str(e)}"}

@app.get("/admin/patient/{session_id}")
async def get_patient_details(session_id: str):
    """Get detailed information for a specific patient"""
    try:
        from database.models import DatabaseManager
        import json
        
        db_manager = DatabaseManager(config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, name, email, age, gender, symptoms, responses, status, created_at, updated_at
            FROM patients 
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        if not row:
            return {"error": "Patient not found"}
        
        patient = {
            "session_id": row[0],
            "name": row[1] or "Not provided",
            "email": row[2] or "Not provided",
            "age": row[3] or "Not provided",
            "gender": row[4] or "Not provided", 
            "symptoms": json.loads(row[5]) if row[5] else [],
            "responses": json.loads(row[6]) if row[6] else {},
            "status": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        }
        
        # Get conversation history if available
        cursor.execute("""
            SELECT message, sender, timestamp FROM conversation_history 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        conversation = []
        for msg_row in cursor.fetchall():
            conversation.append({
                "message": msg_row[0],
                "sender": msg_row[1],
                "timestamp": msg_row[2]
            })
        
        patient["conversation_history"] = conversation
        
        conn.close()
        return patient
        
    except Exception as e:
        return {"error": f"Failed to fetch patient details: {str(e)}"}

@app.get("/admin/analytics")
async def get_analytics():
    """Get detailed analytics for doctor insights"""
    try:
        from database.models import DatabaseManager
        import json
        from datetime import datetime, timedelta
        
        db_manager = DatabaseManager(config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        analytics = {
            "daily_stats": [],
            "symptom_trends": {},
            "completion_analysis": {},
            "response_times": {}
        }
        
        # Daily stats for last 30 days
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT COUNT(*) FROM patients 
                WHERE date(created_at) = ?
            """, (date_str,))
            
            daily_count = cursor.fetchone()[0]
            analytics["daily_stats"].append({
                "date": date_str,
                "patient_count": daily_count
            })
        
        # Symptom trends
        cursor.execute("""
            SELECT symptoms, created_at FROM patients 
            WHERE symptoms IS NOT NULL AND symptoms != '[]'
            AND created_at >= datetime('now', '-30 days')
        """)
        
        symptom_by_date = {}
        for row in cursor.fetchall():
            try:
                symptoms = json.loads(row[0])
                date = row[1][:10]  # Extract date part
                
                if date not in symptom_by_date:
                    symptom_by_date[date] = {}
                
                for symptom in symptoms:
                    symptom_by_date[date][symptom] = symptom_by_date[date].get(symptom, 0) + 1
            except:
                continue
        
        analytics["symptom_trends"] = symptom_by_date
        
        # Completion analysis
        cursor.execute("""
            SELECT status, COUNT(*) FROM patients GROUP BY status
        """)
        
        status_counts = dict(cursor.fetchall())
        analytics["completion_analysis"] = {
            "status_distribution": status_counts,
            "completion_rate": round((status_counts.get('completed', 0) / max(sum(status_counts.values()), 1)) * 100, 1)
        }
        
        conn.close()
        return analytics
        
    except Exception as e:
        return {"error": f"Analytics generation failed: {str(e)}"}

@app.get("/admin/database")
async def database_inspection():
    """Database inspection endpoint for development"""
    try:
        import sqlite3
        import os
        
        db_path = config.DATABASE_PATH
        
        if not os.path.exists(db_path):
            return {"error": f"Database file not found: {db_path}"}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        database_info = {
            "database_path": db_path,
            "database_size_mb": round(os.path.getsize(db_path) / (1024*1024), 2),
            "tables": []
        }
        
        for table in tables:
            table_name = table[0]
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            # Get sample data (first 3 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_data = cursor.fetchall()
            
            table_info = {
                "name": table_name,
                "columns": [{"name": col[1], "type": col[2], "not_null": bool(col[3])} for col in columns],
                "row_count": row_count,
                "sample_data": sample_data[:3]  # Limit to 3 rows for readability
            }
            
            database_info["tables"].append(table_info)
        
        conn.close()
        return database_info
        
    except Exception as e:
        return {"error": f"Database inspection failed: {str(e)}"}

@app.get("/auth/google")
async def google_auth():
    """Initiate Google Calendar OAuth flow"""
    try:
        auth_url = notification_service.get_oauth_url()
        if auth_url:
            return {"auth_url": auth_url, "message": "Visit this URL to authorize Google Calendar access"}
        else:
            return {"error": "Google Calendar OAuth not configured"}
    except Exception as e:
        return {"error": f"OAuth initialization failed: {str(e)}"}

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        # Get authorization code from query parameters
        code = request.query_params.get("code")
        if not code:
            return {"error": "No authorization code received"}
        
        # Handle the OAuth callback
        success = notification_service.handle_oauth_callback(code)
        
        if success:
            # Return HTML that closes the popup and refreshes the parent window
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful</title>
            </head>
            <body>
                <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                    <h2>✅ Google Calendar Connected Successfully!</h2>
                    <p>This window will close automatically...</p>
                </div>
                <script>
                    // Notify parent window and close popup
                    if (window.opener) {
                        window.opener.postMessage({type: 'calendar_connected'}, '*');
                        window.close();
                    } else {
                        // Fallback: redirect to main app
                        window.location.href = '/';
                    }
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        else:
            return {"error": "Failed to authenticate with Google Calendar"}
            
    except Exception as e:
        return {"error": f"OAuth callback failed: {str(e)}"}

@app.get("/auth/google/status")
async def google_auth_status():
    """Check Google Calendar authentication status"""
    try:
        has_service = hasattr(notification_service, 'calendar_service') and notification_service.calendar_service is not None
        has_flow = hasattr(notification_service, 'oauth_flow') and notification_service.oauth_flow is not None
        
        return {
            "authenticated": has_service,
            "oauth_ready": has_flow,
            "message": "Google Calendar is ready" if has_service else "Google Calendar authentication required"
        }
    except Exception as e:
        return {"error": f"Status check failed: {str(e)}"}

@app.get("/api/symptoms")
async def get_symptoms():
    """Get available symptoms for testing"""
    # This would be implemented based on requirements
    return {"message": "Symptoms endpoint available"}

# Core conversation processing
async def process_patient_message(session_id: str, user_message: str) -> str:
    """Process patient message and return AI response"""
    patient = manager.patient_sessions.get(session_id)
    if not patient:
        return "Session error. Please refresh and try again."
    
    # Add to conversation history
    patient.conversation_history.append(f"Patient: {user_message}")
    
    # Process based on current phase
    if patient.phase == "basic_info":
        await process_basic_info(patient, user_message)
    elif patient.phase == "symptoms":
        await process_symptoms(patient, user_message)
    elif patient.phase == "follow_up":
        await process_follow_up(patient, user_message)
    
    # Check if consultation is complete
    if is_consultation_complete(patient):
        patient.phase = "completed"
        await send_notifications(patient)
        return generate_completion_message(patient)
    
    # Generate rule-based response (not AI medical knowledge)
    if patient.phase == "follow_up" and patient.current_symptom:
        # Get next question from database rules
        response = get_next_follow_up_question(patient)
    else:
        # Use AI only for basic conversation flow (not medical knowledge)
        response = await ai_service.generate_response(
            patient.__dict__, user_message, patient.phase
        )
    
    # Add response to history
    patient.conversation_history.append(f"AI: {response}")
    
    # Save patient data
    save_patient_data(patient)
    
    return response

async def process_basic_info(patient: PatientSession, message: str):
    """Process basic information collection with smart progression"""
    current_data = {
        "name": patient.name,
        "email": patient.email,
        "age": patient.age,
        "gender": patient.gender
    }
    
    # Extract information using AI
    extracted_info = await ai_service.extract_patient_information(message, current_data)
    
    # Update patient data
    if extracted_info.get("name") and not patient.name:
        patient.name = extracted_info["name"]
    if extracted_info.get("email") and not patient.email:
        patient.email = extracted_info["email"]
    if extracted_info.get("age") and not patient.age:
        patient.age = extracted_info["age"]
    if extracted_info.get("gender") and not patient.gender:
        patient.gender = extracted_info["gender"]
    
    # Smart progression logic - move to symptoms if we have minimum required info
    has_name = bool(patient.name)
    has_email = bool(patient.email)
    has_age = bool(patient.age)
    has_gender = bool(patient.gender)
    
    # Count how much info we have
    info_count = sum([has_name, has_email, has_age, has_gender])
    
    # Progress to symptoms if we have at least 3 pieces of info, or if user mentions symptoms
    symptom_keywords = ["pain", "chest", "heart", "breath", "dizzy", "tired", "fatigue", "palpitation", "pressure"]
    mentions_symptoms = any(keyword in message.lower() for keyword in symptom_keywords)
    
    # Move to symptoms phase if:
    # 1. All basic info is collected, OR
    # 2. We have at least 3 pieces of info and user mentions symptoms, OR  
    # 3. We have name + email (minimum for appointment) and user mentions symptoms
    if (info_count >= 4) or \
       (info_count >= 3 and mentions_symptoms) or \
       (has_name and has_email and mentions_symptoms):
        patient.phase = "symptoms"

    
async def process_symptoms(patient: PatientSession, message: str):
    """Process symptom identification"""
    # Generate symptom keywords from medical dataset
    symptom_keywords = generate_symptom_keywords()
        
    detected_symptoms = []
    message_lower = message.lower()
    
    for symptom, keywords in symptom_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_symptoms.append(symptom)
        
    if detected_symptoms:
            patient.symptoms.extend(detected_symptoms)
            patient.symptoms = list(set(patient.symptoms))  # Remove duplicates
            patient.phase = "follow_up"
            patient.current_symptom = detected_symptoms[0]
            patient.current_question_index = 0
    
async def process_follow_up(patient: PatientSession, message: str):
    """Process follow-up questions using database rules"""
    if patient.current_symptom:
        # Initialize responses for symptom if not exists
            if patient.current_symptom not in patient.responses:
                patient.responses[patient.current_symptom] = []
            
        # Add patient response to database
    patient.responses[patient.current_symptom].append(message.strip())
        
        # Move to next question
    patient.current_question_index += 1
            
        # Check if we've reached the limit or completed all questions
    if patient.current_question_index >= config.MAX_FOLLOW_UP_QUESTIONS:
        patient.phase = "completed"
        patient.current_symptom = None
        patient.current_symptom = None

def get_next_follow_up_question(patient: PatientSession) -> str:
    """Get next follow-up question from database rules (NO AI medical knowledge)"""
    try:
        with open(config.MEDICAL_DATASET_PATH, 'r') as f:
            medical_dataset = json.loads(f.read())
        
        # Find the symptom data
        symptom_data = None
        for item in medical_dataset:
            if item['symptom'].lower() == patient.current_symptom.lower():
                symptom_data = item
                break
        
        if not symptom_data:
            return "Thank you for that information. Let me schedule your consultation."
        
        # Get questions from specific categories in order
        question_categories = ['symptom_details', 'vital_signs', 'medical_history']
        all_questions = []
        
        for category in question_categories:
            if category in symptom_data['follow_up_questions']:
                all_questions.extend(symptom_data['follow_up_questions'][category])
        
        # Return next question based on current index
        if patient.current_question_index < len(all_questions) and patient.current_question_index < config.MAX_FOLLOW_UP_QUESTIONS:
            return all_questions[patient.current_question_index]
        else:
            # All questions asked, complete consultation
            patient.phase = "completed"
            return "Thank you for providing all the information. I'm now scheduling your consultation with the cardiologist."
            
    except Exception as e:
        print(f"Error getting follow-up question: {e}")
        return "Thank you for that information. Let me schedule your consultation."

def generate_symptom_keywords() -> Dict[str, List[str]]:
    """Generate symptom keywords from medical dataset"""
    try:
        with open(config.MEDICAL_DATASET_PATH, 'r') as f:
            medical_dataset = json.loads(f.read())
        
        symptom_keywords = {}
        
        for item in medical_dataset:
            symptom = item['symptom'].lower()
            keywords = [symptom]
            
            # Add common variations
            if "chest pain" in symptom:
                keywords.extend(["chest pain", "chest hurt", "chest discomfort", "heart pain"])
            elif "shortness of breath" in symptom:
                keywords.extend(["short of breath", "difficulty breathing", "breathless", "dyspnea"])
            elif "palpitation" in symptom:
                keywords.extend(["heart racing", "irregular heartbeat", "palpitation", "heart flutter"])
            elif "fatigue" in symptom:
                keywords.extend(["tired", "exhausted", "weakness", "fatigue"])
            elif "dizziness" in symptom:
                keywords.extend(["dizzy", "lightheaded", "faint", "vertigo"])
            
            symptom_keywords[symptom] = keywords
        
        return symptom_keywords
        
    except Exception:
        # Fallback keywords
        return {
            "chest pain / discomfort": ["chest pain", "chest hurt", "chest discomfort", "heart pain"],
            "shortness of breath (dyspnea)": ["short of breath", "difficulty breathing", "breathless", "dyspnea"]
        }

def is_consultation_complete(patient: PatientSession) -> bool:
    """Check if consultation is complete with flexible requirements"""
    # Essential info: name and email (for appointment scheduling)
    essential_info = patient.name and patient.email
    
    # Optional but helpful: age and gender (at least one)
    demographic_info = patient.age or patient.gender
    
    # Symptoms and responses
    has_symptoms = len(patient.symptoms) > 0
    has_responses = len(patient.responses) > 0
    
    # Complete if we have essential info + demographics + symptoms + responses
    # OR if we have essential info + symptoms and at least 2 follow-up responses
    return (essential_info and demographic_info and has_symptoms and has_responses) or \
           (essential_info and has_symptoms and len(patient.responses) >= 2)

async def send_notifications(patient: PatientSession):
    """Send notifications to doctor"""
    patient_data = {
        "name": patient.name,
        "email": patient.email,
        "age": patient.age,
        "gender": patient.gender
    }
    
    await notification_service.send_consultation_summary(
        patient_data, patient.symptoms, patient.responses
    )
    
    await notification_service.schedule_appointment(patient_data)

def generate_completion_message(patient: PatientSession) -> str:
    """Generate consultation completion message"""
    return f"""Consultation Complete

Summary:
• Patient: {patient.name}
• Email: {patient.email}
• Age: {patient.age}
• Symptoms: {', '.join(patient.symptoms)}

Next Steps:
• Doctor notification sent
• Appointment scheduling in progress
• You will receive confirmation shortly

Thank you for using CardioGenie."""

def save_patient_data(patient: PatientSession):
    """Save patient data to database"""
    patient_data = {
        "name": patient.name,
        "email": patient.email,
        "age": patient.age,
        "gender": patient.gender,
        "symptoms": patient.symptoms,
        "responses": patient.responses,
        "status": patient.phase,
        "completed_at": datetime.now().isoformat() if patient.phase == "completed" else None
    }
    
    db_manager.save_patient_data(patient.session_id, patient_data)

# WebSocket endpoint
@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    # Send welcome message
    welcome_message = await ai_service.generate_welcome_message()
    await manager.send_message(session_id, welcome_message, "ai")
    
    try:
        while True:
            # Receive message from patient
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            patient_message = message_data.get("message", "")
            
            if patient_message.strip():
                # Process message and get response
                ai_response = await process_patient_message(session_id, patient_message)
                
                # Send response
                await manager.send_message(session_id, ai_response, "ai")
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)

# Root endpoint to serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend application"""
    from fastapi.responses import FileResponse
    return FileResponse("backend/static/index.html")

@app.get("/doctor")
async def doctor_dashboard_page():
    """Serve the doctor dashboard page"""
    from fastapi.responses import FileResponse
    return FileResponse("backend/static/doctor_dashboard.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT) 