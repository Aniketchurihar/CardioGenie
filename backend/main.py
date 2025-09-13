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
from fastapi.responses import JSONResponse, RedirectResponse
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

# Debug configuration for Railway
print("=== RAILWAY CONFIG DEBUG ===")
config.debug_config()
print("==============================")

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
            return RedirectResponse(
                url="http://localhost:3001/index.html?calendar=connected",
                status_code=302
            )
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
    """Process basic information collection"""
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
        
    # Move to symptoms phase if all info collected
    if patient.name and patient.email and patient.age and patient.gender:
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
    """Check if consultation is complete"""
    basic_info_complete = all([patient.name, patient.email, patient.age, patient.gender])
    has_symptoms = len(patient.symptoms) > 0
    has_responses = len(patient.responses) > 0
    
    return basic_info_complete and has_symptoms and has_responses

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT) 