"""
AI Service Module
Handles all AI-related operations for CardioGenie
"""

import json
import sys
import os
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
        
        if self.config.GROQ_API_KEY:
            try:
                import groq
                # Try different initialization methods for Railway compatibility
                try:
                    self.groq_client = groq.Groq(api_key=self.config.GROQ_API_KEY)
                except TypeError as te:
                    # Fallback for Railway environment compatibility issues
                    print(f"WARNING: Groq client initialization issue: {te}")
                    print("WARNING: AI features will use fallback mode")
                    self.groq_client = None
                    return
                print("SUCCESS: Groq client initialized successfully")
            except ImportError:
                print("WARNING: Groq library not available - AI features will be disabled")
                self.groq_client = None
            except Exception as e:
                print(f"WARNING: Groq initialization failed: {e} - AI features will be disabled")
                self.groq_client = None
        else:
            # For Railway deployment - allow startup without API key, will fail gracefully on first use
            print("WARNING: GROQ_API_KEY not found - AI features will be disabled")
            self.groq_client = None
    
    async def generate_welcome_message(self) -> str:
        """Generate empathetic welcome message"""
        # Use consistent CardioGenie branding
        return "Hi! I'm CardioGenie, your AI assistant for cardiology consultations. To provide you with the best care, could you please share your name, age, and gender?"
    
    async def extract_patient_information(self, message: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information using AI"""
        if not self.groq_client:
            return {}  # Return empty dict if AI is not available
        try:
            prompt = f"""Extract patient information from: "{message}"

Current data:
- Name: {current_data.get('name', 'MISSING')}
- Email: {current_data.get('email', 'MISSING')}
- Age: {current_data.get('age', 'MISSING')}
- Gender: {current_data.get('gender', 'MISSING')}

Extract ONLY missing information. Return JSON format:
{{"name": "extracted_name", "email": "extracted_email", "age": 25, "gender": "Male"}}

For gender, use "Male" or "Female". For age, use integer only.
If nothing can be extracted, return {{}}.

Return only JSON:"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            return json.loads(result_text)
            
        except Exception:
            return {}
    
    async def generate_response(self, patient_data: Dict[str, Any], user_message: str, phase: str) -> str:
        """Generate contextual AI response"""
        if not self.groq_client:
            return "I'm sorry, AI services are currently unavailable. Please check your configuration."
        try:
            system_prompt = self._build_system_prompt(patient_data, phase)
            
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
            
        except Exception:
            return self._get_fallback_response(phase, patient_data)
    
    def _build_system_prompt(self, patient_data: Dict[str, Any], phase: str) -> str:
        """Build system prompt based on conversation phase"""
        base_prompt = """You are CardioGenie, a professional AI assistant for cardiology consultations.

Your role:
- Collect patient information professionally
- Ask relevant medical questions
- Be empathetic but concise
- No medical diagnoses or advice

Current phase: {phase}
Patient data: Name: {name}, Email: {email}, Age: {age}, Gender: {gender}

Guidelines:
- Ask only ONE question at a time
- Keep responses under 25 words
- Be professional and caring
- Use medical terminology appropriately"""

        phase_instructions = {
            "basic_info": "Ask for missing basic information (name, email, age, gender). Be concise.",
            "symptoms": "Ask what cardiovascular symptoms they are experiencing. One question only.",
            "follow_up": "This should not be used - follow-up questions come from database rules.",
            "completed": "Provide professional completion message."
        }

        return base_prompt.format(
            phase=phase,
            name=patient_data.get('name', 'Not provided'),
            email=patient_data.get('email', 'Not provided'),
            age=patient_data.get('age', 'Not provided'),
            gender=patient_data.get('gender', 'Not provided')
        ) + f"\n\nCurrent task: {phase_instructions.get(phase, 'Assist the patient.')}"
    
    def _get_fallback_response(self, phase: str, patient_data: Dict[str, Any]) -> str:
        """Professional fallback responses"""
        fallbacks = {
            "basic_info": "Could you please provide your name, age, and gender?",
            "symptoms": "What cardiovascular symptoms are you experiencing?",
            "follow_up": "Could you provide more details about your symptoms?",
            "completed": "Thank you for providing your information. A cardiologist will review your case."
        }
        return fallbacks.get(phase, "How can I assist you today?") 