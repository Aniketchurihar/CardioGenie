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
        """Extract patient information using LLM with proper error handling"""
        try:
            # Build extraction prompt
            prompt = f"""Extract patient information from this message: "{message}"

Current patient data:
- Name: {current_data.get('name', 'MISSING')}
- Email: {current_data.get('email', 'MISSING')}
- Age: {current_data.get('age', 'MISSING')}
- Gender: {current_data.get('gender', 'MISSING')}

Extract ONLY the missing information. Be flexible with natural language.

Examples:
- "Hi I'm John Smith, 25 years old male" → {{"name": "John Smith", "age": 25, "gender": "Male"}}
- "My email is john@gmail.com" → {{"email": "john@gmail.com"}}
- "I am a 30 year old woman" → {{"age": 30, "gender": "Female"}}

Return ONLY valid JSON with extracted info. If nothing found, return {{}}.
Use "Male" or "Female" for gender. Use integer for age.

JSON:"""

            if self.groq_client == "http_mode":
                # Use HTTP requests to Groq API
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.1
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result_text = result["choices"][0]["message"]["content"].strip()
                    
                    # Clean up the response to extract JSON
                    if "{" in result_text and "}" in result_text:
                        start = result_text.find("{")
                        end = result_text.rfind("}") + 1
                        json_str = result_text[start:end]
                        return json.loads(json_str)
                    
            elif self.groq_client:
                # Use Groq library if available
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.1
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # Clean up the response to extract JSON
                if "{" in result_text and "}" in result_text:
                    start = result_text.find("{")
                    end = result_text.rfind("}") + 1
                    json_str = result_text[start:end]
                    return json.loads(json_str)
            
            return {}
            
        except Exception as e:
            print(f"Information extraction error: {e}")
            return {}
    
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
            
            name = patient_data.get('name', '')
            
            if len(missing) == 4:  # First interaction
                return "Hello! I'm CardioGenie, your AI cardiology assistant. I'm here to help you with your heart health concerns. To get started, could you please share your name and a bit about yourself?"
            elif "name" in missing:
                return "I'd love to help you today! Could you please tell me your name so I can assist you better?"
            elif "email" in missing:
                if name:
                    return f"Nice to meet you, {name}! I'll need to send you some information and appointment details. Could you share your email address with me?"
                else:
                    return "I'll need to send you some important information. Could you please share your email address?"
            elif "age" in missing:
                if name:
                    return f"Thanks, {name}! To provide you with the most appropriate care recommendations, could you tell me your age?"
                else:
                    return "To provide you with personalized care, could you tell me your age?"
            elif "gender" in missing:
                if name:
                    return f"Almost done with the basics, {name}! Could you let me know your gender? This helps me understand your health profile better."
                else:
                    return "Could you let me know your gender? This helps me provide more personalized health guidance."
            else:
                if name:
                    return f"Perfect, {name}! Now I'd like to understand what's bringing you here today. What cardiovascular symptoms or concerns are you experiencing?"
                else:
                    return "Great! Now, what cardiovascular symptoms or heart-related concerns are you experiencing today?"
        
        elif phase == "symptoms":
            name = patient_data.get('name', '')
            if name:
                return f"I'm here to help you, {name}. Could you describe what symptoms or concerns brought you here today? For example, are you experiencing chest pain, shortness of breath, heart palpitations, or any other heart-related issues?"
            else:
                return "I'm here to help with your heart health concerns. Could you describe what symptoms you're experiencing? This could be chest pain, shortness of breath, palpitations, or any other cardiovascular symptoms."
        
        elif phase == "follow_up":
            name = patient_data.get('name', '')
            if name:
                return f"Thanks for sharing that, {name}. Could you tell me a bit more about these symptoms? Any additional details would be helpful."
            else:
                return "Thank you for sharing that information. Could you provide some more details about your symptoms?"
        
        elif phase == "completed":
            name = patient_data.get('name', '')
            if name:
                return f"Thank you so much, {name}! I have all the information I need. I'm now connecting you with our cardiology team - they'll be notified about your case and you'll receive an appointment confirmation shortly. Take care!"
            else:
                return "Perfect! I have all the information needed. Our cardiology team will be notified about your case and you'll receive an appointment confirmation shortly. Thank you for using CardioGenie!"
        
        else:
            return "Hello! I'm CardioGenie, your AI cardiology assistant. I'm here to help you with any heart health concerns. Could you please tell me your name so we can get started?" 