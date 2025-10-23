# Dental Chatbot Microservice

A Python-based microservice using LangChain for intelligent dental assistant conversations.

## 🚀 Features

- **LangChain Integration** - Advanced conversation management
- **Multiple LLM Providers** - OpenAI, Anthropic, or local models
- **Conversation Memory** - Maintains context across messages
- **Session Management** - Individual sessions per user
- **Dental Context** - Specialized prompts for dental assistance
- **REST API** - FastAPI-based endpoints
- **Auto Documentation** - Interactive API docs

## 📋 Prerequisites

- Python 3.10+
- pip
- API key for your chosen LLM provider

## 🔧 Installation

1. **Install dependencies:**
```bash
cd chatbot-service
pip install -r requirements.txt
```

2. **Configure environment:**

Create a `.env` file with your settings:

```env
# LLM Provider (choose one: openai, anthropic, local)
LLM_PROVIDER=openai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Configuration (if using Anthropic)
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# Service Configuration
SERVICE_PORT=8001
ENVIRONMENT=development
```

## 🎯 LLM Provider Options

### Option 1: OpenAI (Recommended for Production)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

**Pros:** Best quality, reliable, fast
**Cons:** Costs per API call

### Option 2: Anthropic Claude
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
```

**Pros:** High quality, good reasoning
**Cons:** Costs per API call

### Option 3: Local/Open Source (Mistral, Llama, etc.)
```env
LLM_PROVIDER=local
LOCAL_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2
LOCAL_MODEL_DEVICE=cpu
```

**Pros:** Free, private, no API limits
**Cons:** Requires more resources, may be slower

## 🏃 Running the Service

### Development Mode
```bash
python app.py
```

### Production Mode with Gunicorn
```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

The service will be available at:
- **API**: http://localhost:8001
- **Docs**: http://localhost:8001/docs
- **Health**: http://localhost:8001/health

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Create Session
```bash
POST /api/sessions
{
  "user_id": "user123"
}
```

### Send Message
```bash
POST /api/chat
{
  "message": "I need to schedule a cleaning",
  "session_id": "abc-123",  # optional
  "user_id": "user123",
  "context": {               # optional
    "user_name": "John Doe"
  }
}
```

### Get Session Info
```bash
GET /api/sessions/{session_id}
```

### Clear Session History
```bash
POST /api/sessions/{session_id}/clear
```

### End Session
```bash
DELETE /api/sessions/{session_id}
```

## 🧪 Testing

### Test with cURL
```bash
# Create a session
curl -X POST http://localhost:8001/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user"}'

# Send a message
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What services do you offer?",
    "user_id": "test_user"
  }'
```

### Test with Python
```python
import requests

# Create session
response = requests.post('http://localhost:8001/api/sessions', 
    json={'user_id': 'test_user'})
session_id = response.json()['session_id']

# Send message
response = requests.post('http://localhost:8001/api/chat',
    json={
        'message': 'I need a dental checkup',
        'session_id': session_id,
        'user_id': 'test_user'
    })
print(response.json()['response'])
```

## 🏗️ Architecture

```
chatbot-service/
├── app.py                    # FastAPI application
├── config.py                 # Configuration management
├── models.py                 # Pydantic models
├── llm_provider.py          # LLM provider factory
├── conversation_manager.py   # Session & memory management
├── chatbot_chain.py         # LangChain conversation chain
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openai/anthropic/local) | openai |
| `SERVICE_PORT` | Service port | 8001 |
| `MAX_CONVERSATION_HISTORY` | Max messages to remember | 10 |
| `SESSION_TIMEOUT_MINUTES` | Session expiration time | 30 |
| `CONVERSATION_MEMORY_TYPE` | Memory type (buffer/summary/token) | buffer |

## 🎨 Dental Chatbot Capabilities

The chatbot is configured to help with:
- ✅ Answering dental service questions
- ✅ Appointment scheduling assistance
- ✅ General oral health advice
- ✅ Office hours and contact information
- ✅ Handling common dental concerns
- ✅ Providing empathetic responses

## 🔄 Integration with Main Backend

The Node.js backend automatically forwards chat messages to this service. Configure the backend with:

```env
CHATBOT_SERVICE_URL=http://localhost:8001
```

## 📊 Monitoring

### Check Health
```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "llm_provider": "openai",
  "llm_available": true,
  "active_sessions": 5,
  "timestamp": "2025-10-22T12:00:00"
}
```

## 🐛 Troubleshooting

### LLM Not Available
- Check your API key is set correctly
- Verify API key has sufficient credits
- Check network connectivity

### Slow Responses
- Consider using a faster model
- Reduce MAX_CONVERSATION_HISTORY
- Use buffer memory instead of summary

### Memory Issues with Local Models
- Reduce model size
- Use CPU instead of GPU if GPU memory is limited
- Consider using a cloud LLM provider

## 📝 License

MIT License

---

**Built with ❤️ using Python, LangChain, and FastAPI**

