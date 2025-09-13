# 🚀 CardioGenie - Free Hosting Deployment Guide

## Overview

Deploy your **CardioGenie** hackathon project for **FREE** using modern cloud platforms. This guide provides step-by-step instructions for hosting all three components.

---

## 🏗️ **Architecture Components**

1. **Backend (FastAPI)** - Python API server
2. **Frontend (React)** - Single HTML file with CDN React
3. **Database (SQLite)** - File-based database

---

## 🆓 **Free Hosting Options**

### **Option 1: Railway (Recommended) 🚂**

**Best for:** Full-stack deployment with database persistence

#### **Backend Deployment:**

1. **Create account:** [railway.app](https://railway.app)
2. **Connect GitHub:** Link your repository
3. **Deploy backend:**
   ```bash
   # Create railway.json in project root
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
     }
   }
   ```
4. **Set environment variables:**
   - `PORT=8000`
   - `GROQ_API_KEY=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`
   - `TELEGRAM_BOT_TOKEN=8331574104:AAGK0sljHsfNk9Q_I2FYdncG4cDEJM5O6bQ`
   - `DOCTOR_CHAT_ID=6789621640`

#### **Frontend Deployment:**

1. **Deploy to Netlify:** [netlify.com](https://netlify.com)
2. **Drag & drop** the `frontend` folder
3. **Update API URLs** in `index.html` to Railway backend URL

---

### **Option 2: Render + Netlify 🎨**

**Best for:** Separate backend/frontend deployment

#### **Backend (Render):**

1. **Create account:** [render.com](https://render.com)
2. **Create Web Service** from GitHub
3. **Settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3.10+

#### **Frontend (Netlify):**

1. **Create account:** [netlify.com](https://netlify.com)
2. **Deploy** `frontend` folder
3. **Update** backend URLs in code

---

### **Option 3: Vercel (Serverless) ⚡**

**Best for:** Serverless deployment

#### **Setup:**

1. **Create account:** [vercel.com](https://vercel.com)
2. **Create** `vercel.json`:
   ```json
   {
     "builds": [
       {
         "src": "backend/main.py",
         "use": "@vercel/python"
       },
       {
         "src": "frontend/*",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "backend/main.py"
       },
       {
         "src": "/(.*)",
         "dest": "frontend/$1"
       }
     ]
   }
   ```

---

## 📁 **Deployment-Ready File Structure**

```
CardioGenie/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── config.py              # Configuration
│   └── services/              # AI & Notification services
├── frontend/
│   ├── index.html             # React app (single file)
│   └── server.py              # Local development only
├── database/
│   └── cardiogenie_production.db
├── docs/
│   └── Datasetab94d2b.json    # Medical dataset
├── requirements.txt           # Python dependencies
├── railway.json              # Railway config
├── vercel.json               # Vercel config
└── README.md                 # Project documentation
```

---

## 🔧 **Pre-Deployment Checklist**

### **1. Update Configuration for Production:**

**File: `backend/config.py`**

```python
import os

class Config:
    # Use environment variables in production
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/cardiogenie_production.db")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-key-here")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-token-here")
    DOCTOR_CHAT_ID = os.getenv("DOCTOR_CHAT_ID", "your-chat-id")

    # Update for production domain
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://your-domain.com/auth/google/callback")

    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
```

### **2. Update Frontend API URLs:**

**File: `frontend/index.html`**

```javascript
// Replace localhost with your deployed backend URL
const API_BASE = "https://your-backend-url.railway.app";
const WS_BASE = "wss://your-backend-url.railway.app";

// Update all fetch calls
fetch(`${API_BASE}/auth/google/status`);
const ws = new WebSocket(`${WS_BASE}/ws/chat/${sessionId}`);
```

### **3. Create Production Requirements:**

**File: `requirements.txt`**

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
groq==0.4.1
requests==2.31.0
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
```

---

## 🌐 **Step-by-Step Railway Deployment**

### **Step 1: Prepare Repository**

```bash
# Create railway.json
echo '{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
  }
}' > railway.json

# Commit changes
git add .
git commit -m "Prepare for Railway deployment"
git push
```

### **Step 2: Deploy Backend**

1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub**
3. Select your repository
4. **Add Variables:**
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `DOCTOR_CHAT_ID`
   - `DOCTOR_EMAIL`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

### **Step 3: Deploy Frontend**

1. Go to [netlify.com](https://netlify.com)
2. **Drag & drop** `frontend` folder
3. **Update** `index.html` with Railway backend URL
4. **Redeploy**

### **Step 4: Update Google OAuth**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. **Update redirect URI:**
   - `https://your-railway-app.railway.app/auth/google/callback`

---

## 🎯 **Final URLs Structure**

After deployment, you'll have:

- **Frontend:** `https://your-app.netlify.app`
- **Backend API:** `https://your-app.railway.app`
- **Health Check:** `https://your-app.railway.app/health`
- **Google OAuth:** `https://your-app.railway.app/auth/google`

---

## 🔍 **Testing Deployment**

### **Health Checks:**

```bash
# Backend health
curl https://your-app.railway.app/health

# Frontend access
curl https://your-app.netlify.app

# WebSocket test (use browser dev tools)
new WebSocket('wss://your-app.railway.app/ws/chat/test123')
```

### **Demo Flow:**

1. **Open:** `https://your-app.netlify.app`
2. **Test:** Doctor setup modal (if not authenticated)
3. **Complete:** Patient consultation flow
4. **Verify:** Calendar invite creation

---

## 💡 **Pro Tips for Hackathon**

### **1. Custom Domain (Optional):**

- **Netlify:** Add custom domain for professional look
- **Railway:** Use custom domain for backend

### **2. Environment Management:**

- Keep sensitive keys in platform environment variables
- Never commit API keys to repository

### **3. Demo Preparation:**

- Test full flow before presentation
- Have backup local version ready
- Prepare demo data/scenarios

### **4. Monitoring:**

- Use platform logs for debugging
- Set up basic error tracking
- Monitor API usage limits

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**CORS Errors:**

```python
# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**WebSocket Connection Issues:**

- Ensure WSS (not WS) for HTTPS sites
- Check firewall/proxy settings
- Verify WebSocket support on platform

**Database Persistence:**

- Railway: Database persists automatically
- Render: Use PostgreSQL for production
- Vercel: Consider external database service

---

## 🎉 **Ready for Hackathon!**

Your **CardioGenie** application will be:

- ✅ **Publicly accessible** via HTTPS
- ✅ **Professional URLs** for demo
- ✅ **Fully functional** with all features
- ✅ **Free to host** during hackathon
- ✅ **Scalable** for demo traffic

**Estimated deployment time:** 30-60 minutes

**Total cost:** $0 (Free tier limits apply)

---

## 📞 **Support Resources**

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Netlify Docs:** [docs.netlify.com](https://docs.netlify.com)
- **Render Docs:** [render.com/docs](https://render.com/docs)
- **FastAPI Deployment:** [fastapi.tiangolo.com/deployment](https://fastapi.tiangolo.com/deployment)

**Good luck with your hackathon! 🏆**
