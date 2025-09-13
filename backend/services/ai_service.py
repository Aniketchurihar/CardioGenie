"""
AI Service Module
Handles all AI-related operations for CardioGenie
"""

import json
import sys
import os
import requests
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import Config

class AIService:
    """Professional AI service for medical consultations"""
    
    def __init__(self, config):
        self.config = config
        self.groq_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients"""
        # Debug: Check if environment variables are being read
        import os
        print(f"DEBUG: GROQ_API_KEY exists in env: {'GROQ_API_KEY' in os.environ}")
        print(f"DEBUG: GROQ_API_KEY value length: {len(self.config.GROQ_API_KEY) if self.config.GROQ_API_KEY else 0}")
        
        # Initialize Groq client with simpler approach
        self.groq_client = None
        
        if self.config.GROQ_API_KEY:
            try:
                # Try direct HTTP requests to Groq API if library fails
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    print("SUCCESS: Groq API connection verified - using HTTP requests")
                    self.groq_client = "http_mode"  # Flag to use HTTP requests
                else:
                    print(f"WARNING: Groq API test failed: {response.status_code}")
                    self.groq_client = None
            except Exception as e:
                print(f"WARNING: Groq API connection failed: {e}")
                self.groq_client = None
        else:
            print("WARNING: GROQ_API_KEY not found - using fallback responses")
            self.groq_client = None
    
    async def generate_welcome_message(self) -> str:
        """Generate empathetic welcome message"""
        # Use consistent CardioGenie branding
        return "Hi! I'm CardioGenie, your AI assistant for cardiology consultations. To provide you with the best care, could you please share your name, age, and gender?"
    
    async def extract_patient_information(self, message: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information using simple pattern matching"""
        import re
        
        extracted = {}
        message_lower = message.lower()
        
        # Extract name (if missing)
        if not current_data.get('name'):
            # Look for "my name is", "I'm", or just assume first words are name
            name_patterns = [
                r"(?:my name is|i'm|i am)\s+([a-zA-Z\s]+?)(?:\s*,|\s*age|\s*\d|\s*male|\s*female|$)",
                r"^([a-zA-Z\s]+?)(?:\s*,|\s*age|\s*\d|\s*male|\s*female)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    extracted['name'] = match.group(1).strip().title()
                    break
        
        # Extract email (if missing)
        if not current_data.get('email'):
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
            if email_match:
                extracted['email'] = email_match.group(0).lower()
        
        # Extract age (if missing)
        if not current_data.get('age'):
            age_patterns = [
                r'(?:age|old)\s*(?:is)?\s*(\d{1,3})',
                r'(\d{1,3})\s*(?:years?\s*old|yrs?)',
                r'\b(\d{1,3})\s*(?:years?|yrs?)\b'
            ]
            for pattern in age_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    age = int(match.group(1))
                    if 1 <= age <= 120:  # Reasonable age range
                        extracted['age'] = age
                        break
        
        # Extract gender (if missing)
        if not current_data.get('gender'):
            if any(word in message_lower for word in ['male', 'man', 'boy', 'gentleman']):
                extracted['gender'] = 'Male'
            elif any(word in message_lower for word in ['female', 'woman', 'girl', 'lady']):
                extracted['gender'] = 'Female'
        
        return extracted
    
    async def generate_response(self, patient_data: Dict[str, Any], user_message: str, phase: str) -> str:
        """Generate contextual AI response"""
        if not self.groq_client:
            return self._get_fallback_response(phase, patient_data)
        
        try:
            system_prompt = self._build_system_prompt(patient_data, phase)
            
            if self.groq_client == "http_mode":
                # Use direct HTTP requests to Groq API
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "max_tokens": 80,
                        "temperature": 0.2
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    print(f"Groq API error: {response.status_code}")
                    return self._get_fallback_response(phase, patient_data)
            else:
                # Use Groq library (if it works)
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=80,
                    temperature=0.2
                )
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_response(phase, patient_data)
    
    def _build_system_prompt(self, patient_data: Dict[str, Any], phase: str) -> str:
        """Build system prompt based on conversation phase"""
        base_prompt = """You are CardioGenie, a rule-based AI assistant for cardiology consultations.

STRICT RULES:
- Follow ONLY the structured conversation flow: Basic Info → Symptoms → Follow-up Questions
- Ask ONE question at a time
- Keep responses under 20 words
- NO medical diagnoses or medical advice
- Use ONLY database rules, NOT your medical knowledge

Current phase: {phase}
Patient data: Name: {name}, Email: {email}, Age: {age}, Gender: {gender}

Your ONLY job is to collect information systematically."""

        phase_instructions = {
            "basic_info": "Ask for ONE missing piece: name, email, age, or gender. Nothing else.",
            "symptoms": "Ask ONLY: 'What cardiovascular symptoms are you experiencing?'",
            "follow_up": "NEVER used - follow-up questions come from database rules only.",
            "completed": "Say: 'Thank you. The cardiologist will be notified.'"
        }

        return base_prompt.format(
            phase=phase,
            name=patient_data.get('name', 'Not provided'),
            email=patient_data.get('email', 'Not provided'),
            age=patient_data.get('age', 'Not provided'),
            gender=patient_data.get('gender', 'Not provided')
        ) + f"\n\nCurrent task: {phase_instructions.get(phase, 'Assist the patient.')}"
    
    def _get_fallback_response(self, phase: str, patient_data: Dict[str, Any]) -> str:
        """Rule-based responses following the document requirements"""
        
        if phase == "basic_info":
            # Check what basic info is missing
            missing = []
            if not patient_data.get('name'): missing.append("name")
            if not patient_data.get('email'): missing.append("email")
            if not patient_data.get('age'): missing.append("age")
            if not patient_data.get('gender'): missing.append("gender")
            
            if len(missing) == 4:  # First interaction
                return "Hello! I'm CardioGenie, your AI cardiology assistant. Could you please tell me your name?"
            elif "name" in missing:
                return "Could you please tell me your name?"
            elif "email" in missing:
                return "What's your email address?"
            elif "age" in missing:
                return "How old are you?"
            elif "gender" in missing:
                return "What's your gender?"
            else:
                return "Thank you! Now, what cardiovascular symptoms are you experiencing?"
        
        elif phase == "symptoms":
            return "What cardiovascular symptoms are you experiencing? Please describe symptoms like chest pain, shortness of breath, palpitations, or fatigue."
        
        elif phase == "follow_up":
            return "Could you provide more details about your symptoms?"
        
        elif phase == "completed":
            return "Thank you for providing all the information. I'm now notifying the cardiologist and scheduling your appointment. You'll receive a calendar invite shortly!"
        
        else:
            return "Hello! I'm CardioGenie, your AI cardiology assistant. Could you please tell me your name to get started?" 