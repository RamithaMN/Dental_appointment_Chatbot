# 🦷 Dental Appointment Chatbot

A complete full-stack AI-powered dental chatbot application with intelligent date handling, appointment scheduling, and business hours enforcement.

## ✨ Key Features

- 🤖 **Smart Date Handling**: Correctly calculates day-of-week for any date
- 🚫 **Sunday Closure Detection**: Automatically blocks Sunday appointments
- ⏰ **Saturday Hours Enforcement**: Only offers 9:00 AM - 2:00 PM slots on Saturdays
- 📅 **Interactive Appointment Booking**: One-click appointment confirmation
- 🔐 **Secure Authentication**: JWT-based user authentication
- 🐳 **Docker Ready**: Complete containerized deployment
- 🌐 **Multi-LLM Support**: OpenAI, Anthropic, and local models

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (or Anthropic/Local model)

### 1. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env
```

**Minimum required in `.env`:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

### 2. Start All Services
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Chatbot Service**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### 4. Login
Use these demo credentials:
- Username: `demo` / Password: `demo123`
- Username: `admin` / Password: `admin123`

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Dental Chatbot System                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐         ┌──────────┐         ┌───────────┐  │
│  │ Frontend │ ──JWT──>│  Node.js │ ──HTTP─>│  Python   │  │
│  │ Next.js  │ <──────│  Express │ <──────│ LangChain │  │
│  └──────────┘         └──────────┘         └───────────┘  │
│   Port 3000            Port 8000            Port 8001     │
│                                                             │
│                                             ┌─────────────┐│
│                                             │  LLM API    ││
│                                             │ (OpenAI/    ││
│                                             │  Anthropic) ││
│                                             └─────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Services

### 1. Frontend (Next.js)
- **Port**: 3000
- **Features**: 
  - Interactive chat interface
  - Appointment booking with confirmation buttons
  - User authentication
  - Responsive design with Tailwind CSS

### 2. Backend (Node.js/Express)
- **Port**: 8000
- **Features**:
  - JWT authentication
  - API gateway
  - Request forwarding to chatbot
  - Rate limiting and security

### 3. Chatbot Service (Python/LangChain)
- **Port**: 8001
- **Features**:
  - LangChain-powered conversations
  - Multi-provider LLM support
  - Smart date handling and business hours enforcement
  - Session management
  - Context-aware responses

## 🔧 Configuration

### LLM Provider Options

#### Option 1: OpenAI (Recommended)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
```

#### Option 2: Anthropic Claude
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
```

#### Option 3: Local/Open Source
```env
LLM_PROVIDER=local
LOCAL_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2
```

## 🛠️ Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f chatbot-service

# Restart a service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build

# Check status
docker-compose ps

# Stop and remove everything (including volumes)
docker-compose down -v
```

## 📦 Project Structure

```
ChatBot_Dental/
├── backend/                    # Node.js Express API
│   ├── app.js                 # Main Express server
│   ├── auth.js                # JWT authentication
│   ├── appointments.js        # Appointment management
│   ├── database.js           # Database operations
│   ├── middleware.js         # Security middleware
│   └── Dockerfile
├── chatbot-service/           # Python LangChain service
│   ├── app.py                # FastAPI application
│   ├── chatbot_chain.py      # Core chatbot logic
│   ├── conversation_manager.py # Session management
│   ├── llm_provider.py       # LLM provider factory
│   ├── models.py             # Data models
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts
│   │   ├── hooks/            # Custom hooks
│   │   └── lib/              # Utility functions
│   ├── package.json
│   └── Dockerfile
├── database/                  # Database setup
│   └── init.sql              # PostgreSQL schema
├── docker-compose.yml         # Main Docker configuration
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🧪 Testing

### Test Backend
```bash
curl http://localhost:8000/health
```

### Test Chatbot Service
```bash
curl http://localhost:8001/health
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/chatbot/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

### Test Chat (requires token)
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/chatbot/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Send message
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"I need a dental checkup"}'
```

## 🐛 Troubleshooting

### Services Won't Start
**Check logs:**
```bash
docker-compose logs
```

**Common issues:**
- Missing `.env` file → Copy from `.env.example`
- Invalid API key → Check your LLM provider credentials
- Port conflicts → Stop services on ports 3000, 8000, 8001

### Chatbot Not Responding
**Check chatbot service health:**
```bash
curl http://localhost:8001/health
```

**View chatbot logs:**
```bash
docker-compose logs chatbot-service
```

**Common issues:**
- Missing or invalid API key
- LLM provider rate limits
- Network connectivity

### Container Keeps Restarting
**Check specific container:**
```bash
docker-compose ps
docker logs dental-chatbot
```

**Restart specific service:**
```bash
docker-compose restart chatbot-service
```

## 🚀 Development Mode

To run services locally without Docker:

### Backend
```bash
cd backend
npm install
node app.js
```

### Chatbot Service
```bash
cd chatbot-service
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 Monitoring

### View All Services
```bash
docker-compose ps
```

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Chatbot
curl http://localhost:8001/health

# Frontend
curl -I http://localhost:3000
```

### Resource Usage
```bash
docker stats
```

## 🔐 Security Notes

1. **Never commit `.env`** - It contains your API keys
2. **Change default SECRET_KEY** in production
3. **Use HTTPS** in production
4. **Enable firewall** rules for production deployment
5. **Regularly update** dependencies

## 💰 Cost Considerations

### OpenAI Pricing (Approximate)
- **GPT-3.5-Turbo**: ~$0.002 per 1K tokens (~$0.01 per conversation)
- **GPT-4**: ~$0.03 per 1K tokens (~$0.15 per conversation)

### Free Alternative
Use `LLM_PROVIDER=local` for free open-source models (requires more resources)

## 🎯 Key Improvements

### Smart Date Handling
- ✅ Correctly calculates day-of-week for any date
- ✅ Handles multiple date formats (14th december, December 14th)
- ✅ Prevents incorrect date calculations

### Business Hours Enforcement
- ✅ **Sunday Closure**: Automatically blocks Sunday appointments
- ✅ **Saturday Hours**: Only offers 9:00 AM - 2:00 PM slots
- ✅ **Smart Week Selection**: Shows appropriate future dates

### Interactive Features
- ✅ **Appointment Confirmation Buttons**: One-click booking
- ✅ **Patient Name Extraction**: Includes names in summaries
- ✅ **Conditional Summaries**: Only for confirmed bookings

### Technical Features
- ✅ **Multi-LLM Support**: OpenAI, Anthropic, Local models
- ✅ **Session Management**: Persistent conversations
- ✅ **Error Handling**: Robust error recovery
- ✅ **Docker Deployment**: Easy containerized setup

## 📚 API Documentation

When services are running, visit:
- **Backend API**: http://localhost:8000/docs
- **Chatbot API**: http://localhost:8001/docs

## 🤝 Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify `.env` configuration
3. Ensure API key is valid
4. Check health endpoints

## 📄 License

MIT License

---



**Get started in 3 commands:**
```bash
cp .env.example .env          # Configure
# Edit .env with your API key
docker-compose up --build     # Run
# Open http://localhost:3000  # Use
```# Updated git configuration
# Author configuration updated to RamithaMN
