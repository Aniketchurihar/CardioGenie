# 🚂 CardioGenie - Railway Deployment Guide

## 🎯 **Single Railway Deployment (Recommended)**

Deploy your **entire CardioGenie application** on Railway with SQLite database persistence - everything in one place!

---

## ✅ **What's Included:**
- ✅ **Backend API** (FastAPI with all endpoints)
- ✅ **Frontend UI** (React app served by FastAPI)
- ✅ **SQLite Database** (50 medical symptoms + patient data)
- ✅ **WebSocket Chat** (Real-time communication)
- ✅ **Google Calendar** (Appointment scheduling)
- ✅ **Telegram Notifications** (Doctor alerts)

---

## 🚀 **Step-by-Step Deployment**

### **Step 1: Prepare Your Repository**

Your code is already configured for Railway deployment with:
- ✅ `railway.json` configuration file
- ✅ Frontend moved to `backend/static/`
- ✅ Relative URLs for production
- ✅ Environment variable support

### **Step 2: Deploy to Railway**

1. **Create Railway Account:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project:**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**
   - Choose your CardioGenie repository

3. **Configure Environment Variables:**
   Add these in Railway dashboard → Variables:
   ```
   GROQ_API_KEY=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
   TELEGRAM_BOT_TOKEN=8331574104:AAGK0sljHsfNk9Q_I2FYdncG4cDEJM5O6bQ
   DOCTOR_CHAT_ID=6789621640
   DOCTOR_EMAIL=aniket.ch71@gmail.com
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   ```

4. **Set Google Redirect URI:**
   After deployment, update this variable:
   ```
   GOOGLE_REDIRECT_URI=https://your-app-name.railway.app/auth/google/callback
   ```

### **Step 3: Update Google OAuth Settings**

1. **Go to Google Cloud Console:**
   - Visit [console.cloud.google.com](https://console.cloud.google.com)
   - Navigate to **APIs & Services** → **Credentials**

2. **Update OAuth Client:**
   - Click your OAuth 2.0 Client ID
   - Add to **Authorized redirect URIs:**
     ```
     https://your-app-name.railway.app/auth/google/callback
     ```
   - Save changes

### **Step 4: Test Your Deployment**

1. **Access Your App:**
   ```
   https://your-app-name.railway.app
   ```

2. **Health Check:**
   ```
   https://your-app-name.railway.app/health
   ```

3. **Test Features:**
   - ✅ Chat interface loads
   - ✅ WebSocket connection works
   - ✅ Google Calendar authentication
   - ✅ Appointment scheduling
   - ✅ Telegram notifications

---

## 🎯 **Your Final URLs**

After deployment, you'll have **ONE URL** for everything:

- **🏠 Frontend:** `https://your-app.railway.app/`
- **🔧 Health Check:** `https://your-app.railway.app/health`
- **📅 Google Auth:** `https://your-app.railway.app/auth/google`
- **💬 WebSocket:** `wss://your-app.railway.app/ws/chat`
- **📊 API Docs:** `https://your-app.railway.app/docs`

---

## 💾 **Database Persistence**

### **SQLite on Railway:**
- ✅ **Automatic Persistence** - Your database survives deployments
- ✅ **50 Medical Symptoms** - Pre-loaded from dataset
- ✅ **Patient Sessions** - Stored during conversations
- ✅ **No External DB Needed** - Everything included

### **Database Location:**
```
/app/database/cardiogenie_production.db
```

### **Cleanup (if needed):**
Use your cleanup script locally, then redeploy:
```bash
python scripts/cleanup_database.py
git add .
git commit -m "Database reset"
git push
```

---

## 🔧 **Configuration Files**

### **railway.json** (Already created):
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

### **requirements.txt** (Already updated):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
groq==0.4.1
requests==2.31.0
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
gunicorn==21.2.0
```

---

## 🎬 **Demo Flow for Hackathon**

### **1. Open Your App:**
```
https://your-app.railway.app
```

### **2. Doctor Setup (First Time):**
- Modal appears for Google Calendar authentication
- Click "Authenticate Google Calendar"
- Complete OAuth flow in new tab
- Return to app - setup complete!

### **3. Patient Consultation:**
- Enter patient details (name, age, gender, email)
- Describe symptoms (e.g., "chest pain")
- Answer 2-3 follow-up questions from medical database
- Automatic appointment scheduling
- Doctor receives Telegram notification

### **4. Verification:**
- Check patient email for calendar invite
- Check doctor Telegram for notification
- Verify appointment in Google Calendar

---

## 💡 **Hackathon Pro Tips**

### **🎯 Demo Preparation:**
1. **Test full flow** before presentation
2. **Prepare demo scenarios** (different symptoms)
3. **Have backup local version** ready
4. **Practice the story** - patient journey to appointment

### **🔍 Monitoring:**
- **Railway Logs:** Monitor real-time application logs
- **Health Endpoint:** Quick status check during demo
- **Error Handling:** App gracefully handles failures

### **⚡ Performance:**
- **Fast Loading:** Single deployment = faster response
- **WebSocket:** Real-time chat experience
- **Database:** Local SQLite = no network latency

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**❌ Build Fails:**
- Check `requirements.txt` syntax
- Verify all dependencies are available
- Check Railway build logs

**❌ App Won't Start:**
- Verify `railway.json` start command
- Check environment variables are set
- Review application logs

**❌ Frontend Not Loading:**
- Ensure `backend/static/index.html` exists
- Check static files mounting in `main.py`
- Verify root endpoint serves frontend

**❌ WebSocket Issues:**
- Ensure WSS protocol for HTTPS
- Check CORS configuration
- Verify WebSocket endpoint path

**❌ Google OAuth Fails:**
- Update redirect URI in Google Console
- Check `GOOGLE_REDIRECT_URI` environment variable
- Verify OAuth client credentials

**❌ Database Issues:**
- Check if `docs/Datasetab94d2b.json` exists
- Verify database initialization in startup
- Review database path configuration

---

## 📊 **Resource Usage**

### **Railway Free Tier:**
- ✅ **$5 monthly credit** (plenty for hackathon)
- ✅ **512MB RAM** (sufficient for SQLite + FastAPI)
- ✅ **1GB storage** (more than enough for database)
- ✅ **Custom domains** available
- ✅ **HTTPS** included automatically

### **Estimated Usage:**
- **Deployment:** ~2-3 minutes
- **Cold start:** ~10-15 seconds
- **Memory usage:** ~200-300MB
- **Storage:** ~50MB (with database)

---

## 🏆 **Success Checklist**

Before your hackathon presentation:

- [ ] ✅ App deployed and accessible
- [ ] ✅ Health check returns "healthy"
- [ ] ✅ Frontend loads with beautiful UI
- [ ] ✅ Chat functionality works
- [ ] ✅ Google Calendar authenticated
- [ ] ✅ Test appointment scheduling
- [ ] ✅ Telegram notifications working
- [ ] ✅ Demo scenarios prepared
- [ ] ✅ Backup plan ready

---

## 🎉 **You're Ready!**

Your **CardioGenie** application is now:
- 🌐 **Publicly accessible** with professional URL
- 💾 **Database persistent** across deployments
- 🔒 **Secure** with HTTPS and environment variables
- ⚡ **Fast** with single-deployment architecture
- 💰 **Free** to host during hackathon
- 🏆 **Demo-ready** for winning presentation

**Total deployment time:** 15-30 minutes  
**Total cost:** $0 (Railway free tier)

---

## 📞 **Support**

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Railway Discord:** [railway.app/discord](https://railway.app/discord)
- **FastAPI Docs:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

**Good luck with your hackathon! 🚂🏆** 