# 🦷 Dental Chatbot Application

A complete full-stack dental chatbot application with **Node.js/Express backend**, **Python/LangChain AI chatbot**, and **Next.js frontend**.

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key (or Anthropic/Local model)

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use any editor
```

Minimum required in `.env`:
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
- **Container**: `dental-frontend`
- **Features**: 
  - Chat interface
  - Appointment booking
  - User authentication
  - Responsive design

### 2. Backend (Node.js/Express)
- **Port**: 8000
- **Container**: `dental-backend`
- **Features**:
  - JWT authentication
  - API gateway
  - Request forwarding to chatbot
  - Rate limiting

### 3. Chatbot Service (Python/LangChain)
- **Port**: 8001
- **Container**: `dental-chatbot`
- **Features**:
  - LangChain-powered conversations
  - Multi-provider LLM support
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

### Advanced Configuration

See `.env.example` for all available options including:
- Conversation history length
- Memory type (buffer/summary/token)
- Session timeout
- Model parameters (temperature, max tokens)

## 📦 Project Structure

```
ChatBot_Dental/
├── backend/                    # Node.js Express API
│   ├── app.js
│   ├── auth.js
│   ├── config.js
│   ├── middleware.js
│   ├── package.json
│   └── Dockerfile
├── chatbot-service/            # Python LangChain service
│   ├── app.py
│   ├── chatbot_chain.py
│   ├── conversation_manager.py
│   ├── llm_provider.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml          # Main Docker configuration
├── .env.example                # Environment template
└── README.md                   # This file
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

## 📚 Documentation

- **LangChain Guide**: `CHATBOT_SERVICE_GUIDE.md`
- **Docker Setup**: `DOCKER_SETUP_COMPLETE.md`
- **LangChain Summary**: `LANGCHAIN_CHATBOT_SUMMARY.md`
- **API Examples**: Check `/docs` endpoint when services are running

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
```
