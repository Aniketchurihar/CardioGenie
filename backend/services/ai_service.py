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
        name = patient_data.get('name', '')
        
        base_prompt = """You are CardioGenie, a friendly AI cardiology assistant. You have a warm, professional, and empathetic personality.

CONVERSATION RULES:
- Be conversational and natural, like a real healthcare assistant
- Use the patient's name when you know it to personalize responses
- Progress the conversation naturally - don't get stuck asking for every detail
- If patient mentions symptoms, acknowledge them and explore further
- Keep responses warm but concise (under 30 words)
- NEVER mention "tasks", "phases", or internal processes
- Act like a real person, not a robot

MEDICAL RULES:
- NO medical diagnoses or medical advice
- Collect essential info (name, email) and symptoms efficiently
- If patient shares symptoms, focus on those rather than missing demographics
- Ask ONE question at a time, but be flexible about progression"""

        if phase == "basic_info":
            missing = []
            if not patient_data.get('name'): missing.append("name")
            if not patient_data.get('email'): missing.append("email") 
            if not patient_data.get('age'): missing.append("age")
            if not patient_data.get('gender'): missing.append("gender")
            
            name = patient_data.get('name', '')
            has_essential = patient_data.get('name') and patient_data.get('email')
            info_count = 4 - len(missing)
            
            if len(missing) == 4:
                context = "First interaction. Be welcoming and ask for name, age, and what brings them here. Don't interrogate - be natural."
            elif "name" in missing:
                context = "You need the patient's name to personalize the conversation. Be friendly and welcoming."
            elif not has_essential:
                context = f"You know {name}'s name. You MUST get their email for appointment scheduling - this is mandatory before proceeding."
            elif info_count >= 2:
                context = f"You have {name}'s essential info. You can ask for one more detail, but prioritize moving to symptoms if they mention any health concerns."
            else:
                context = f"You have enough info about {name}. Focus on their health concerns and symptoms now."
                
        elif phase == "symptoms":
            context = f"You have {name}'s basic information. Now ask about their cardiovascular symptoms naturally and conversationally."
            
        elif phase == "follow_up":
            context = f"You're helping {name} with their symptoms. Ask for more details about their condition naturally."
            
        else:
            context = "Be welcoming and start collecting basic patient information."

        return base_prompt + f"\n\nCONTEXT: {context}"
    
    def _get_fallback_response(self, phase: str, patient_data: Dict[str, Any]) -> str:
        """Smart rule-based responses that progress naturally"""
        
        if phase == "basic_info":
            # Check what basic info is missing
            missing = []
            if not patient_data.get('name'): missing.append("name")
            if not patient_data.get('email'): missing.append("email")
            if not patient_data.get('age'): missing.append("age")
            if not patient_data.get('gender'): missing.append("gender")
            
            name = patient_data.get('name', '')
            info_count = 4 - len(missing)
            
            # First interaction - be welcoming and ask for multiple pieces of info
            if len(missing) == 4:
                return "Hello! I'm CardioGenie, your AI cardiology assistant. I'm here to help you with your heart health concerns. To get started, could you please tell me your name, age, and what's bringing you here today?"
            
            # If we have some info but missing critical pieces, ask smartly
            elif "name" in missing:
                return "I'd love to help you today! Could you please tell me your name so I can assist you better?"
            
            # Email is ALWAYS required - ask for it if missing
            elif "email" in missing:
                return f"Thanks, {name}! I'll need your email address to send you appointment details. What's your email?"
            
            # If we have name and email, we can be more flexible about age/gender
            elif info_count >= 2:
                missing_optional = [item for item in missing if item not in ['name', 'email']]
                if len(missing_optional) == 1:
                    if "age" in missing_optional:
                        return f"Great, {name}! One quick question - what's your age? Then we can discuss your health concerns."
                    elif "gender" in missing_optional:
                        return f"Perfect, {name}! Just need to know your gender for our records, then we can talk about what's bothering you."
                else:
                    # Multiple optional items missing - ask for one and move on
                    return f"Thanks, {name}! What's your age? And more importantly, what cardiovascular symptoms are you experiencing?"
            
            # If we have enough info, move to symptoms
            else:
                return f"Perfect, {name}! Now I'd like to understand what's bringing you here today. What cardiovascular symptoms or concerns are you experiencing?"
        
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