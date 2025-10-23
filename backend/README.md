# Dental Chatbot Backend - Node.js/Express

This is the Node.js/Express version of the Dental Chatbot API backend.

## Technology Stack

- **Node.js** - Runtime environment
- **Express** - Web framework
- **JWT (jsonwebtoken)** - Authentication
- **bcryptjs** - Password hashing
- **CORS** - Cross-origin resource sharing
- **Helmet** - Security headers
- **Morgan** - HTTP request logger
- **Express Rate Limit** - Rate limiting

## Installation

```bash
npm install
```

## Environment Variables

Create a `.env` file in the backend-node directory:

```env
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
API_KEY=dental-chatbot-api-key-2025
PORT=8000
NODE_ENV=development
```

## Running the Server

### Development Mode (with auto-reload):
```bash
npm run dev
```

### Production Mode:
```bash
npm start
```

## API Endpoints

### Authentication

#### Login (POST /api/chatbot/login)
```bash
curl -X POST http://localhost:8000/api/chatbot/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

#### Generate Token (POST /api/chatbot/token)
```bash
curl -X POST http://localhost:8000/api/chatbot/token \
  -H "Content-Type: application/json" \
  -d '{"api_key":"dental-chatbot-api-key-2025","user_id":"test_user"}'
```

#### Verify Token (GET /api/chatbot/verify)
```bash
curl -X GET http://localhost:8000/api/chatbot/verify \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Other Endpoints

- **Health Check**: GET /health
- **Root**: GET /
- **Chat**: POST /api/chatbot/chat (requires authentication)

## Demo Credentials

| Username | Password  |
|----------|-----------|
| demo     | demo123   |
| admin    | admin123  |

## Features

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ Rate limiting (100 requests per 15 minutes)
- ✅ Security headers with Helmet
- ✅ CORS configuration
- ✅ Request logging
- ✅ Error handling
- ✅ Token expiration (15 minutes default)

## Migration from Python/FastAPI

This backend maintains 100% API compatibility with the original Python/FastAPI backend. All endpoints, request/response formats, and authentication mechanisms are identical.

