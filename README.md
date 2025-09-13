# 🏥 CardioGenie - Doctor's AI Assistant for Cardiology Consults

> **Production-Ready AI Assistant for Healthcare Hackathons**

CardioGenie is an intelligent AI assistant designed to help cardiologists collect patient symptom information through empathetic conversations, comprehensive medical dataset integration, and seamless notification systems.

## 🚀 **Quick Start**

### **Option 1: One-Command Startup (Recommended)**

```bash
python scripts/start_cardiogenie.py
```

### **Option 2: Manual Startup**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start backend
python backend/main.py

# 4. Start frontend (new terminal)
cd frontend && python server.py
```

## 📁 **Production Directory Structure**

```
CardioGenie/
├── 📱 frontend/           # React.js UI (Single HTML file)
│   ├── index.html        # Main chat interface
│   └── server.py         # Frontend development server
├── 🔧 backend/           # FastAPI Production Backend
│   ├── main.py          # Main application server
│   └── config.py        # Configuration management
├── 🗄️ database/          # Database Layer
│   ├── models.py        # Database models & operations
│   └── cardiogenie.db   # SQLite database file
├── 📋 docs/              # Documentation & Medical Data
│   ├── Datasetab94d2b.json  # Professional medical dataset (50+ symptoms)
│   └── client_secret_*.json # Google Calendar credentials
├── 🛠️ scripts/           # Utility Scripts
│   ├── start_cardiogenie.py  # Production startup script
│   └── cleanup_database.py  # Database management script
├── 📄 requirements.txt   # Python dependencies
├── 🔐 .env              # Environment configuration
└── 📖 README.md         # This file
```

## ✨ **Key Features**

### 🧠 **AI-Powered Conversations**

- **Empathetic AI**: Warm, caring responses using Groq (free) + OpenAI (fallback)
- **Smart Information Extraction**: LLM parses patient info from any format
- **Multi-field Collection**: "I'm John, 28, male" → extracts all 3 fields instantly
- **Context-Aware**: No repetitive questions, intelligent conversation flow

### 🏥 **Professional Medical Integration**

- **Comprehensive Dataset**: 50+ cardiovascular symptoms with professional follow-up questions
- **Evidence-Based**: Questions from symptom_details, vital_signs, and red_flags categories
- **Safety-First**: Red flag questions for critical symptom identification

### 📱 **Real-Time Communication**

- **WebSocket Chat**: Instant messaging with typing indicators
- **Responsive UI**: Beautiful, mobile-friendly interface with animations
- **Live Updates**: Real-time conversation state management

### 🔔 **Smart Notifications**

- **Telegram Integration**: Instant doctor notifications with formatted patient summaries
- **Google Calendar**: Automated appointment scheduling
- **Professional Format**: Clean, medical-grade consultation summaries

## 🛠️ **Database Management**

### **View Database Statistics**

```bash
python scripts/cleanup_database.py --stats-only
```

### **Clean Database (Fresh Start)**

```bash
# Interactive cleanup with confirmation
python scripts/cleanup_database.py

# Force cleanup without confirmation
python scripts/cleanup_database.py --force

# Clean without reinitializing (empty database)
python scripts/cleanup_database.py --no-reinit
```

## ⚙️ **Configuration**

### **Environment Variables (.env)**

```env
# AI Configuration (Required)
GROQ_API_KEY=your_groq_api_key_here          # FREE - Primary AI
OPENAI_API_KEY=your_openai_api_key_here      # PAID - Fallback AI

# Telegram Integration (Required)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DOCTOR_CHAT_ID=your_telegram_chat_id

# Google Calendar (Optional)
DOCTOR_EMAIL=doctor@example.com
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Database (Auto-configured)
DATABASE_PATH=database/cardiogenie.db
```

### **Getting API Keys**

1. **Groq (FREE)**: Visit [console.groq.com](https://console.groq.com) → Create API Key
2. **OpenAI (PAID)**: Visit [platform.openai.com](https://platform.openai.com) → API Keys
3. **Telegram Bot**: Message [@BotFather](https://t.me/botfather) → Create Bot
4. **Telegram Chat ID**: Message [@userinfobot](https://t.me/userinfobot) → Get ID

## 🏗️ **Architecture**

### **Backend (FastAPI)**

- **Production-ready** configuration management
- **Modular design** with separated concerns
- **Database abstraction** layer
- **AI client management** with fallback support
- **WebSocket** real-time communication

### **Frontend (React.js)**

- **Single HTML file** for easy deployment
- **CDN-based** React for quick setup
- **WebSocket integration** for real-time chat
- **Responsive design** with Tailwind CSS
- **Smooth animations** with Framer Motion

### **Database (SQLite)**

- **Portable** single-file database
- **Professional medical dataset** integration
- **Patient data management**
- **Session tracking** and history

## 🎯 **API Endpoints**

- `GET /health` - System health check
- `GET /api/symptoms` - List all available symptoms
- `GET /api/patients` - Patient data (development)
- `WS /ws/chat/{session_id}` - WebSocket chat endpoint

## 🧪 **Testing & Development**

### **Health Check**

```bash
curl http://localhost:8000/health
```

### **WebSocket Test**

Open `http://localhost:3000/index.html` and start chatting!

### **Database Stats**

```bash
python scripts/cleanup_database.py --stats-only
```

## 🚀 **Deployment**

### **Production Checklist**

- [ ] Set `DEBUG=False` in environment
- [ ] Configure production database
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### **Docker Deployment** (Optional)

```dockerfile
# Dockerfile example
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "scripts/start_cardiogenie.py"]
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 **Hackathon Ready**

CardioGenie is specifically designed for healthcare hackathons with:

- ✅ **Quick Setup**: One-command startup
- ✅ **Professional UI**: Beautiful, responsive interface
- ✅ **Real Medical Data**: 50+ symptoms with professional questions
- ✅ **AI Integration**: Free Groq + paid OpenAI fallback
- ✅ **Complete Workflow**: Patient → AI → Doctor notification
- ✅ **Production Quality**: Clean code, proper architecture
- ✅ **Easy Demo**: Comprehensive test scenarios

---

**Built with ❤️ for Healthcare Innovation**
