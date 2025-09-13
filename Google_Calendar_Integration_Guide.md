# 📅 Google Calendar Integration Setup Guide for CardioGenie

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Google Cloud Console Setup](#google-cloud-console-setup)
4. [Code Configuration](#code-configuration)
5. [Authentication Process](#authentication-process)
6. [Testing the Integration](#testing-the-integration)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide enables **real Google Calendar invites** to be sent from doctor to patients automatically after consultations. The system creates professional calendar events with email notifications, Google Meet links, and automatic reminders.

### Key Features:

- ✅ **Real email invites** from doctor to patient
- ✅ **No patient authentication** required
- ✅ **Google Meet integration** for video consultations
- ✅ **Automatic reminders** (24 hours & 1 hour before)
- ✅ **Professional appearance** with doctor as organizer

---

## Prerequisites

- Google account for the doctor (`aniket.ch71@gmail.com`)
- Access to Google Cloud Console
- CardioGenie application running locally
- Basic understanding of OAuth 2.0

---

## Google Cloud Console Setup

### Step 1: Create Google Cloud Project

1. **Navigate to:** [Google Cloud Console](https://console.cloud.google.com/)
2. **Sign in** with your Google account
3. **Create new project:**
   - Click **"Select a project"** → **"NEW PROJECT"**
   - **Project name:** `CardioGenie`
   - **Organization:** (Leave as default)
   - Click **"CREATE"**

### Step 2: Enable Google Calendar API

1. **Navigate to:** [APIs & Services Library](https://console.cloud.google.com/apis/library)
2. **Search for:** `Google Calendar API`
3. **Click on:** "Google Calendar API" result
4. **Click:** `ENABLE` button
5. **Wait** for API to be enabled (usually takes 1-2 minutes)

### Step 3: Create OAuth 2.0 Credentials

1. **Navigate to:** [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. **Click:** `+ CREATE CREDENTIALS`
3. **Select:** `OAuth 2.0 Client IDs`
4. **If prompted,** configure OAuth consent screen first (see Step 4)
5. **Application type:** `Web application`
6. **Name:** `CardioGenie Calendar Integration`

#### Configure Authorized Redirect URIs:

**For Local Development:**

```
http://localhost:8000/auth/google/callback
```

**For Production (replace with your domain):**

```
https://yourdomain.com/auth/google/callback
```

7. **Click:** `CREATE`
8. **Copy and save** the credentials:

```
Client ID: YOUR_GOOGLE_CLIENT_ID_HERE
Client Secret: YOUR_GOOGLE_CLIENT_SECRET_HERE
```

### Step 4: Configure OAuth Consent Screen

1. **Navigate to:** [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. **User Type:** Select `External`
3. **Click:** `CREATE`

#### Fill Required Information:

- **App name:** `CardioGenie`
- **User support email:** `aniket.ch71@gmail.com`
- **App logo:** (Optional - skip for now)
- **App domain:** (Optional for testing)
- **Authorized domains:** `localhost` (for development)
- **Developer contact information:** `aniket.ch71@gmail.com`

4. **Click:** `SAVE AND CONTINUE`

#### Configure Scopes:

1. **Click:** `ADD OR REMOVE SCOPES`
2. **Search for:** `calendar`
3. **Select:** `https://www.googleapis.com/auth/calendar`
4. **Click:** `UPDATE`
5. **Click:** `SAVE AND CONTINUE`

#### Add Test Users:

1. **Click:** `ADD USERS`
2. **Add email:** `aniket.ch71@gmail.com`
3. **Click:** `SAVE`
4. **Click:** `SAVE AND CONTINUE`

#### Review and Publish:

1. **Review** all settings
2. **Publishing status:** Keep as `Testing` for now
3. **Click:** `BACK TO DASHBOARD`

---

## Code Configuration

### Update Configuration File

**File:** `backend/config.py`

```python
class Config:
    """Universal configuration class for all environments"""

    # Database Configuration
    DATABASE_PATH = "database/cardiogenie_production.db"

    # AI Configuration
    GROQ_API_KEY = "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"

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = "8331574104:AAGK0sljHsfNk9Q_I2FYdncG4cDEJM5O6bQ"
    DOCTOR_CHAT_ID = "6789621640"

    # Google Calendar Configuration
    DOCTOR_EMAIL = "aniket.ch71@gmail.com"  # Doctor's email (organizer)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
    GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 8000

    # Medical Dataset Configuration
    MEDICAL_DATASET_PATH = "docs/Datasetab94d2b.json"

    # Conversation Configuration
    MAX_QUESTIONS_PER_SYMPTOM = 4
    MAX_FOLLOW_UP_QUESTIONS = 2
```

### Install Required Dependencies

**File:** `requirements.txt`

```txt
# Core Framework
fastapi==0.104.1
uvicorn==0.24.0

# WebSocket Support
websockets==12.0

# AI Integration
groq==0.4.1

# HTTP Requests
requests==2.31.0

# Google Calendar API
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

---

## Authentication Process

### Step 1: Start the Application

```bash
# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Start frontend (in new terminal)
cd frontend && python server.py
```

### Step 2: Doctor Authentication (One-Time Setup)

1. **Get OAuth URL:**

```bash
curl http://localhost:8000/auth/google
```

2. **Copy the `auth_url` from response** (example):

```
https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fgoogle%2Fcallback&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&state=xyz&access_type=offline&include_granted_scopes=true&prompt=consent
```

3. **Open URL in incognito browser window**

4. **Sign in with doctor's account:** `aniket.ch71@gmail.com`

5. **Grant permissions:**

   - Click **"Continue"** on app verification screen
   - Select **"See, edit, share, and permanently delete all calendars"**
   - Click **"Continue"**

6. **Verify successful authentication:**

```bash
curl http://localhost:8000/auth/google/status
```

**Expected response:**

```json
{
  "authenticated": true,
  "oauth_ready": true,
  "message": "Google Calendar is ready"
}
```

---

## Testing the Integration

### Step 1: Complete Patient Consultation

1. **Open frontend:** http://localhost:3001/index.html
2. **Start consultation** as a patient
3. **Provide information:**

   - Name: `Test Patient`
   - Email: `patient@example.com`
   - Age: `30`
   - Gender: `Male`
   - Symptoms: `chest pain`

4. **Answer follow-up questions**

### Step 2: Verify Calendar Event Creation

**Check backend logs for:**

```
Google Calendar event created: https://www.google.com/calendar/event?eid=...
Calendar invite sent from aniket.ch71@gmail.com to patient@example.com
```

### Step 3: Verify Email Delivery

**Patient should receive:**

- Email from `aniket.ch71@gmail.com`
- Subject: `Cardiology Consultation - Test Patient`
- Google Meet link included
- Calendar event added to their Google Calendar

---

## Production Deployment

### Environment-Specific Configuration

**Development:**

```python
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
```

**Production:**

```python
GOOGLE_REDIRECT_URI = "https://yourdomain.com/auth/google/callback"
```

### Update Google Cloud Console for Production

1. **Navigate to:** [Credentials](https://console.cloud.google.com/apis/credentials)
2. **Edit OAuth 2.0 Client ID**
3. **Add production redirect URI:**

```
https://yourdomain.com/auth/google/callback
```

### OAuth Consent Screen for Production

1. **Navigate to:** [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. **Publishing status:** Change to `In production`
3. **Submit for verification** (if required)

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "This app isn't verified" Warning

**Problem:** Google shows unverified app warning

**Solutions:**

- **For Testing:** Click `Advanced` → `Go to CardioGenie (unsafe)`
- **For Production:** Submit app for verification or keep as internal

#### 2. No Email Invites Received

**Problem:** Calendar events created but no emails sent

**Checklist:**

- ✅ Doctor account authenticated (not patient)
- ✅ Check spam/junk folders
- ✅ Verify `sendNotifications=True` in API call
- ✅ Ensure patient email is valid

#### 3. Redirect URI Mismatch

**Problem:** `redirect_uri_mismatch` error

**Solution:**

- Ensure exact match in Google Cloud Console
- Include protocol (`http://` or `https://`)
- No trailing slashes

#### 4. Calendar API Not Enabled

**Problem:** API calls fail with 403 error

**Solution:**

1. Go to [APIs Library](https://console.cloud.google.com/apis/library)
2. Search `Google Calendar API`
3. Click `ENABLE`

#### 5. Invalid Client ID/Secret

**Problem:** OAuth fails with invalid credentials

**Solution:**

1. Verify credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Ensure correct project selected
3. Regenerate credentials if needed

### Debug Commands

**Check authentication status:**

```bash
curl http://localhost:8000/auth/google/status
```

**Get new OAuth URL:**

```bash
curl http://localhost:8000/auth/google
```

**Test backend health:**

```bash
curl http://localhost:8000/health
```

---

## API Reference

### OAuth Endpoints

#### Get OAuth Authorization URL

```http
GET /auth/google
```

**Response:**

```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
  "message": "Visit this URL to authorize Google Calendar access"
}
```

#### OAuth Callback Handler

```http
GET /auth/google/callback?code=...&state=...
```

**Response:** Redirects to frontend with `?calendar=connected`

#### Check Authentication Status

```http
GET /auth/google/status
```

**Response:**

```json
{
  "authenticated": true,
  "oauth_ready": true,
  "message": "Google Calendar is ready"
}
```

### Calendar Event Structure

**Automatically created events include:**

- **Organizer:** Doctor's authenticated account
- **Attendee:** Patient's email
- **Duration:** 30 minutes
- **Video:** Google Meet link
- **Reminders:** 24 hours and 1 hour before
- **Description:** Patient details and symptoms

---

## Security Considerations

### Data Protection

- Store credentials securely
- Use environment variables in production
- Implement proper access controls
- Regular credential rotation

### OAuth Security

- Use HTTPS in production
- Validate redirect URIs
- Implement CSRF protection
- Monitor authentication logs

### HIPAA Compliance

- Ensure Google Workspace HIPAA compliance
- Implement proper data handling
- Maintain audit logs
- Regular security assessments

---

## Support and Resources

### Useful Links

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [API Quotas and Limits](https://developers.google.com/calendar/api/guides/quota)

### Contact Information

- **Developer:** CardioGenie Team
- **Email:** aniket.ch71@gmail.com
- **Project:** CardioGenie AI Assistant

---

**Last Updated:** September 13, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅
