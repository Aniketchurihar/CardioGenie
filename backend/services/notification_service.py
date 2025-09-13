"""
Notification Service Module
Handles Telegram and calendar notifications for CardioGenie
"""

import requests
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import base64

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import Config
from database.models import DatabaseManager

class NotificationService:
    """Professional notification service for medical consultations"""
    
    def __init__(self, config):
        self.config = config
        self.calendar_service = None
        self.db_manager = DatabaseManager(config.DATABASE_PATH)  # Database storage
        self._setup_google_calendar()
    
    def _save_credentials(self, credentials):
        """Save Google OAuth credentials to database for persistence"""
        try:
            creds_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            success = self.db_manager.save_oauth_credentials('google_calendar', creds_data)
            if success:
                print("✅ Google credentials saved to database")
            return success
            
        except Exception as e:
            print(f"❌ Failed to save credentials: {e}")
            return False
    
    def _load_credentials(self):
        """Load Google OAuth credentials from database"""
        try:
            creds_data = self.db_manager.load_oauth_credentials('google_calendar')
            
            if not creds_data:
                print("📁 No Google credentials found in database")
                return None
            
            # Parse expiry date if available
            expiry = None
            if creds_data.get('expires_at'):
                from datetime import datetime
                expiry = datetime.fromisoformat(creds_data['expires_at'])
            
            credentials = Credentials(
                token=creds_data.get('token'),
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data.get('token_uri'),
                client_id=creds_data.get('client_id'),
                client_secret=creds_data.get('client_secret'),
                scopes=creds_data.get('scopes'),
                expiry=expiry
            )
            
            # Check if credentials are expired and refresh if needed
            if credentials.expired and credentials.refresh_token:
                print("🔄 Refreshing expired Google credentials...")
                credentials.refresh(Request())
                self._save_credentials(credentials)  # Save refreshed credentials
                print("✅ Google credentials refreshed successfully")
            
            print("✅ Google credentials loaded from database")
            return credentials
            
        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")
            return None
    
    async def send_consultation_summary(self, patient_data: Dict[str, Any], 
                                      symptoms: List[str], responses: Dict[str, Any]) -> bool:
        """Send consultation summary to doctor via Telegram"""
        try:
            summary = self._format_consultation_summary(patient_data, symptoms, responses)
            
            telegram_url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": self.config.DOCTOR_CHAT_ID,
                "text": summary,
                "parse_mode": "HTML"
            }
            
            response = requests.post(telegram_url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _format_consultation_summary(self, patient_data: Dict[str, Any], 
                                   symptoms: List[str], responses: Dict[str, Any]) -> str:
        """Format professional consultation summary"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = f"""<b>CARDIOLOGY CONSULTATION REQUEST</b>

<b>Patient Information:</b>
• Name: {patient_data.get('name', 'Not provided')}
• Email: {patient_data.get('email', 'Not provided')}
• Age: {patient_data.get('age', 'Not provided')}
• Gender: {patient_data.get('gender', 'Not provided')}

<b>Reported Symptoms:</b> {', '.join(symptoms) if symptoms else 'None specified'}

<b>Clinical Assessment:</b>"""

        # Format responses with question labels
        for symptom, symptom_responses in responses.items():
            if symptom_responses:
                summary += f"\n\n<b>{symptom.upper()}:</b>"
                for i, response in enumerate(symptom_responses, 1):
                    summary += f"\n  {i}. {response}"

        summary += f"\n\n<b>Consultation Time:</b> {timestamp}"
        summary += f"\n<b>Status:</b> Awaiting physician review"
        
        return summary
    
    def _setup_google_calendar(self):
        """Setup Google Calendar service with persistent token storage"""
        if not GOOGLE_AVAILABLE:
            print("Google Calendar API not available - using mock implementation")
            return
            
        try:
            # Try to load existing credentials first
            credentials = self._load_credentials()
            
            if credentials and credentials.valid:
                # Use existing valid credentials
                self.calendar_service = build('calendar', 'v3', credentials=credentials)
                print("✅ Google Calendar service initialized with saved credentials")
            else:
                # No valid credentials - will need OAuth flow
                self.calendar_service = None
                print("🔑 No valid credentials found - OAuth authentication required")
            
            # Initialize OAuth flow for when needed
            if hasattr(self.config, 'GOOGLE_CLIENT_ID') and self.config.GOOGLE_CLIENT_ID:
                self._init_oauth_flow()
                print("Google Calendar OAuth ready")
            else:
                print("Google Calendar credentials not configured - using mock implementation")
            
        except Exception as e:
            print(f"Google Calendar setup failed: {e}")
            self.calendar_service = None
    
    def _init_oauth_flow(self):
        """Initialize OAuth flow for Google Calendar"""
        try:
            from google_auth_oauthlib.flow import Flow
            
            # Create flow from client config
            client_config = {
                "web": {
                    "client_id": self.config.GOOGLE_CLIENT_ID,
                    "client_secret": self.config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.GOOGLE_REDIRECT_URI]
                }
            }
            
            self.oauth_flow = Flow.from_client_config(
                client_config,
                scopes=self.config.GOOGLE_SCOPES,
                redirect_uri=self.config.GOOGLE_REDIRECT_URI
            )
            
        except Exception as e:
            print(f"OAuth flow initialization failed: {e}")
            self.oauth_flow = None
    
    def get_oauth_url(self):
        """Get OAuth authorization URL for Google Calendar"""
        if not self.oauth_flow:
            return None
            
        try:
            auth_url, _ = self.oauth_flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            return auth_url
        except Exception as e:
            print(f"Failed to generate OAuth URL: {e}")
            return None
    
    def handle_oauth_callback(self, authorization_code):
        """Handle OAuth callback and initialize calendar service with persistent storage"""
        if not self.oauth_flow:
            return False
            
        try:
            # Exchange code for credentials
            self.oauth_flow.fetch_token(code=authorization_code)
            credentials = self.oauth_flow.credentials
            
            # Save credentials persistently
            if self._save_credentials(credentials):
                print("✅ Google credentials saved for future use")
            
            # Build calendar service
            self.calendar_service = build('calendar', 'v3', credentials=credentials)
            print("✅ Google Calendar service authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ OAuth callback handling failed: {e}")
            return False
    
    async def _create_google_calendar_event(self, patient_data: Dict[str, Any], appointment_time: datetime) -> bool:
        """Create actual Google Calendar event"""
        if not self.calendar_service:
            return False
            
        try:
            # Event details - Doctor inviting patient
            event = {
                'summary': f'Cardiology Consultation - {patient_data.get("name", "Patient")}',
                'description': f'''
CARDIOLOGY CONSULTATION

Patient Information:
• Name: {patient_data.get("name", "Not provided")}
• Email: {patient_data.get("email", "Not provided")}
• Age: {patient_data.get("age", "Not provided")}
• Gender: {patient_data.get("gender", "Not provided")}

Reported Symptoms: {", ".join(patient_data.get("symptoms", []))}

Consultation Details:
• Duration: 30 minutes
• Type: Cardiology Assessment
• Provider: Dr. {self.config.DOCTOR_EMAIL}

This appointment was scheduled through CardioGenie AI Assistant.
Please join the video call at the scheduled time.
                '''.strip(),
                'start': {
                    'dateTime': appointment_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (appointment_time + timedelta(minutes=30)).isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [
                    {
                        'email': patient_data.get('email', ''),
                        'displayName': patient_data.get('name', 'Patient'),
                        'responseStatus': 'needsAction'
                    }
                ],
                # Note: organizer will be set automatically to the authenticated user (doctor)
                # The authenticated user should be the doctor's account
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'email', 'minutes': 60},       # 1 hour before
                        {'method': 'popup', 'minutes': 15},       # 15 minutes before
                    ],
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f'cardiogenie-{int(appointment_time.timestamp())}',
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                },
                'sendUpdates': 'all',  # Send email invites to all attendees
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': False
            }
            
            # Create the event in the authenticated calendar (doctor's calendar)
            # This will send invites from the authenticated user (doctor) to the patient
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendNotifications=True,  # Force send notifications
                sendUpdates='all'  # Send email invites to all attendees
            ).execute()
            
            print(f'Google Calendar event created: {created_event.get("htmlLink")}')
            print(f'Calendar invite sent from {self.config.DOCTOR_EMAIL} to {patient_data.get("email")}')
            
            # Also send a direct email notification as backup
            await self._send_appointment_email(patient_data, created_event, appointment_time)
            
            return True
            
        except Exception as e:
            print(f'Google Calendar event creation failed: {e}')
            return False
    
    async def _send_appointment_email(self, patient_data: Dict[str, Any], calendar_event: Dict[str, Any], appointment_time: datetime):
        """Send appointment confirmation email as backup"""
        try:
            # For now, we'll log the email content that would be sent
            # In production, you'd integrate with an email service like SendGrid, AWS SES, etc.
            
            meet_link = calendar_event.get('hangoutLink', 'Video link will be provided')
            calendar_link = calendar_event.get('htmlLink', 'Calendar link not available')
            
            email_content = f"""
Subject: Cardiology Consultation Appointment Confirmation

Dear {patient_data.get('name', 'Patient')},

Your cardiology consultation has been scheduled successfully.

APPOINTMENT DETAILS:
• Date & Time: {appointment_time.strftime('%B %d, %Y at %I:%M %p')}
• Duration: 30 minutes
• Type: Cardiology Assessment
• Provider: Dr. {self.config.DOCTOR_EMAIL}

PATIENT INFORMATION:
• Name: {patient_data.get('name', 'Not provided')}
• Email: {patient_data.get('email', 'Not provided')}
• Age: {patient_data.get('age', 'Not provided')}
• Gender: {patient_data.get('gender', 'Not provided')}

REPORTED SYMPTOMS: {', '.join(patient_data.get('symptoms', []))}

JOIN YOUR APPOINTMENT:
• Video Meeting: {meet_link}
• Calendar Event: {calendar_link}

IMPORTANT REMINDERS:
• Please join the video call 5 minutes before your scheduled time
• Have your insurance information ready
• Prepare any questions you'd like to discuss
• You will receive reminder notifications 24 hours and 1 hour before your appointment

If you need to reschedule or have any questions, please contact our office.

Best regards,
CardioGenie - Cardiology Department
{self.config.DOCTOR_EMAIL}

This appointment was scheduled through CardioGenie AI Assistant.
            """.strip()
            
            print("=" * 60)
            print("EMAIL NOTIFICATION CONTENT:")
            print("=" * 60)
            print(f"To: {patient_data.get('email')}")
            print(f"From: {self.config.DOCTOR_EMAIL}")
            print(email_content)
            print("=" * 60)
            print("NOTE: In production, this would be sent via email service")
            print("=" * 60)
            
        except Exception as e:
            print(f"Email backup notification failed: {e}")
    
    async def schedule_appointment(self, patient_data: Dict[str, Any]) -> str:
        """Schedule appointment with Google Calendar integration"""
        try:
            # Calculate appointment time (next available slot after 1 hour)
            now = datetime.now()
            appointment_time = now + timedelta(hours=1)
            
            # Round to next 15-minute slot
            minutes = appointment_time.minute
            rounded_minutes = ((minutes // 15) + 1) * 15
            if rounded_minutes >= 60:
                appointment_time = appointment_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                appointment_time = appointment_time.replace(minute=rounded_minutes, second=0, microsecond=0)
            
            # Try to create Google Calendar event
            calendar_created = await self._create_google_calendar_event(patient_data, appointment_time)
            
            # Format response message
            formatted_time = appointment_time.strftime('%Y-%m-%d at %H:%M')
            
            if calendar_created:
                return f"{formatted_time} (Google Calendar invite sent)"
            else:
                # Fallback: Create a detailed appointment summary
                patient_email = patient_data.get('email', 'No email provided')
                doctor_email = self.config.DOCTOR_EMAIL
                
                appointment_summary = f"""
Appointment Details:
• Time: {formatted_time}
• Patient: {patient_data.get('name', 'Not provided')} ({patient_email})
• Doctor: {doctor_email}
• Duration: 30 minutes
• Type: Cardiology Consultation
• Symptoms: {', '.join(patient_data.get('symptoms', []))}

Calendar invites would be sent to:
- Patient: {patient_email}
- Doctor: {doctor_email}

Meeting Link: Video consultation will be provided via email
                """.strip()
                
                print(f"Appointment scheduled: {appointment_summary}")
                return f"{formatted_time} (Calendar details logged for manual processing)"
            
        except Exception as e:
            print(f"Appointment scheduling error: {e}")
            return "Appointment scheduling temporarily unavailable" 