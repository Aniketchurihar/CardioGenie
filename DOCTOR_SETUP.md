# 👨‍⚕️ Doctor Setup Guide - CardioGenie

## One-Time Google Calendar Setup

### Overview

As the **doctor**, you need to authenticate Google Calendar **once** to enable automatic appointment scheduling for all patients. After this setup, every patient consultation will automatically:

- ✅ Send calendar invites from your email to patients
- ✅ Create Google Meet links for video consultations
- ✅ Set automatic reminders (24h and 1h before)
- ✅ Include patient details and symptoms in the event

---

## 🚀 Quick Setup Steps

### 1. Start the Application

```bash
# Terminal 1: Start Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend && python server.py
```

### 2. Open the Application

- **URL:** http://localhost:3001/index.html
- Look at the **footer** - you'll see calendar status

### 3. Doctor Authentication

- **If you see:** "Doctor Setup Required" (yellow button)
- **Click it** to authenticate with your Google account (`aniket.ch71@gmail.com`)
- **Sign in** and grant calendar permissions
- **Done!** Status will change to "Doctor Calendar Ready" (green)

---

## 🎯 What Happens After Setup

### For Every Patient:

1. Patient completes consultation via chat
2. **Automatic calendar invite** sent from `aniket.ch71@gmail.com` to patient
3. **Google Meet link** included for video consultation
4. **Patient receives email** with appointment details
5. **Doctor gets notification** via Telegram

### No Patient Action Required:

- ❌ Patients don't need to authenticate anything
- ❌ No popups or additional steps for patients
- ✅ Seamless appointment scheduling experience

---

## 🔧 Troubleshooting

### "This app isn't verified" Warning

1. Click **"Advanced"**
2. Click **"Go to CardioGenie (unsafe)"**
3. Grant calendar permissions

### Calendar Status Shows "Offline"

- Check Google Cloud Console setup
- Ensure Calendar API is enabled
- Verify OAuth credentials are correct

### Still Need Help?

- Check `Google_Calendar_Integration_Guide.md` for detailed setup
- Ensure you're using the doctor's Google account for authentication

---

## ✅ Success Indicators

**You'll know setup is complete when:**

- Footer shows: "✓ Doctor Calendar Ready" (green)
- Test patient consultation creates real calendar events
- Patients receive actual email invitations
- Google Meet links are automatically generated

**Ready for Hackathon Demo!** 🎉
