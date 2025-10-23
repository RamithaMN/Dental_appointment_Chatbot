/**
 * Main Express application for the Dental Chatbot API.
 */

const express = require('express');
const cors = require('cors');
const config = require('./config');
const auth = require('./auth');
const db = require('./database');
const appointmentRoutes = require('./appointments');
const chatLogging = require('./chatLogging');
const {
  rateLimitMiddleware,
  loggingMiddleware,
  securityHeadersMiddleware,
  requestValidationMiddleware,
  customSecurityHeaders,
  errorHandler,
  RequestLogger
} = require('./middleware');

// Initialize Express app
const app = express();

// Test database connection on startup
db.testConnection().then(connected => {
  if (connected) {
    console.log('✓ PostgreSQL database connected successfully');
  } else {
    console.warn('⚠ Failed to connect to PostgreSQL database');
  }
}).catch(err => {
  console.error('Database connection error:', err);
});

// Configure CORS
app.use(cors({
  origin: config.ALLOWED_ORIGINS,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(requestValidationMiddleware);
app.use(rateLimitMiddleware);
app.use(loggingMiddleware);
app.use(securityHeadersMiddleware);
app.use(customSecurityHeaders);

// ==================== Routes ====================

/**
 * Root endpoint to check API status
 */
app.get('/', (req, res) => {
  res.json({
    status: 'online',
    service: 'Dental Chatbot API',
    version: '1.0.0'
  });
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString().split('T')[0]
  });
});

/**
 * Login with username and password
 * POST /api/chatbot/login
 */
app.post('/api/chatbot/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    // Validate input
    if (!username || !password) {
      return res.status(400).json({
        detail: 'Username and password are required'
      });
    }
    
    // Try database first, fallback to in-memory users
    let user = await db.getUserByUsername(username).catch(() => null);
    
    if (!user) {
      // Fallback to in-memory authentication
      user = await auth.authenticateUser(username, password);
    } else {
      // Verify password from database
      const isValid = await auth.verifyPassword(password, user.password_hash);
      if (!isValid) {
        return res.status(401).json({
          detail: 'Incorrect username or password'
        });
      }
      
      // Update last login
      await db.updateLastLogin(user.id);
    }
    
    if (!user) {
      return res.status(401).json({
        detail: 'Incorrect username or password'
      });
    }
    
    // Create access token
    const tokenData = {
      sub: user.username,
      scope: 'chatbot:access',
      full_name: user.full_name,
      email: user.email
    };
    
    const accessToken = auth.createAccessToken(
      tokenData,
      config.ACCESS_TOKEN_EXPIRE_MINUTES
    );
    
    // Log audit event
    if (user.id) {
      await db.logAudit({
        userId: user.id,
        username: user.username,
        action: 'LOGIN',
        ipAddress: req.ip,
        userAgent: req.headers['user-agent'],
        requestMethod: req.method,
        requestPath: req.path,
        status: 'success'
      }).catch(err => console.error('Audit log error:', err));
    }
    
    res.status(200).json({
      access_token: accessToken,
      token_type: 'bearer',
      expires_in: config.ACCESS_TOKEN_EXPIRE_MINUTES * 60 // Convert to seconds
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      detail: 'Internal server error during login'
    });
  }
});

/**
 * Generate short-lived access token (API Key method)
 * POST /api/chatbot/token
 */
app.post('/api/chatbot/token', (req, res) => {
  try {
    const { api_key, user_id, metadata } = req.body;
    
    // Log request
    RequestLogger.logRequest(req);
    
    // Verify API key
    if (!auth.verifyApiKey(api_key)) {
      RequestLogger.logResponse(res, req, 401);
      return res.status(401).json({
        detail: 'Invalid API key. Please provide a valid API key.'
      });
    }
    
    // Prepare token data
    const tokenData = {
      sub: user_id || 'anonymous',
      scope: 'chatbot:access'
    };
    
    // Add metadata if provided
    if (metadata) {
      tokenData.metadata = metadata;
    }
    
    // Create access token
    const accessToken = auth.createAccessToken(
      tokenData,
      config.ACCESS_TOKEN_EXPIRE_MINUTES
    );
    
    const response = {
      access_token: accessToken,
      token_type: 'bearer',
      expires_in: config.ACCESS_TOKEN_EXPIRE_MINUTES * 60 // Convert to seconds
    };
    
    // Log successful response
    RequestLogger.logResponse(res, req, 201);
    
    res.status(201).json(response);
  } catch (error) {
    console.error('Token generation error:', error);
    res.status(500).json({
      detail: 'Internal server error during token generation'
    });
  }
});

/**
 * Verify access token
 * GET /api/chatbot/verify
 */
app.get('/api/chatbot/verify', auth.getCurrentUser, (req, res) => {
  res.json({
    valid: true,
    user: req.user.sub,
    scope: req.user.scope,
    expires_at: req.user.exp,
    metadata: req.user.metadata || null
  });
});

/**
 * Send message to chatbot (protected endpoint)
 * POST /api/chatbot/chat
 */
app.post('/api/chatbot/chat', 
  auth.getCurrentUser, 
  chatLogging.logChatInteraction, 
  async (req, res) => {
    try {
      const { message, session_id, context } = req.body;
      
      if (!message) {
        return res.status(400).json({
          detail: 'Message is required'
        });
      }
      
      // Forward to chatbot microservice
      const axios = require('axios');
      const chatbotServiceUrl = process.env.CHATBOT_SERVICE_URL || 'http://localhost:8001';
      
      const chatbotResponse = await axios.post(`${chatbotServiceUrl}/api/chat`, {
        message: message,
        session_id: session_id || null,
        user_id: req.user.sub,
        context: {
          user_name: req.user.full_name || req.user.sub,
          ...context
        }
      });
      
      res.json({
        response: chatbotResponse.data.response,
        session_id: chatbotResponse.data.session_id,
        user: req.user.sub,
        timestamp: chatbotResponse.data.timestamp,
        message_count: chatbotResponse.data.message_count
      });
    } catch (error) {
      console.error('Chat error:', error.response?.data || error.message);
      res.status(500).json({
        detail: 'Failed to process chat message. Please try again.',
        error: error.response?.data?.detail || error.message
      });
    }
  }
);

// ==================== Appointment Routes ====================
app.use('/api/appointments', appointmentRoutes);

// ==================== Analytics Routes ====================

/**
 * Get chat analytics
 * GET /api/analytics/chat
 */
app.get('/api/analytics/chat', auth.getCurrentUser, chatLogging.getChatAnalytics);

/**
 * Get appointment analytics
 * GET /api/analytics/appointments
 */
app.get('/api/analytics/appointments', auth.getCurrentUser, chatLogging.getAppointmentAnalytics);

// Error handling middleware (must be last)
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received. Closing database connections...');
  await db.closePool();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received. Closing database connections...');
  await db.closePool();
  process.exit(0);
});

// Start server
const PORT = config.PORT;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  🦷  Dental Chatbot API (Node.js/Express) with PostgreSQL     ║
║                                                                ║
║  Server running on: http://localhost:${PORT}                        ║
║  Environment: ${config.NODE_ENV.padEnd(47)}║
║                                                                ║
║  API Documentation:                                            ║
║    • Health: GET /health                                       ║
║    • Login:  POST /api/chatbot/login                           ║
║    • Token:  POST /api/chatbot/token                           ║
║    • Verify: GET /api/chatbot/verify                           ║
║    • Chat:   POST /api/chatbot/chat                            ║
║                                                                ║
║  Appointments:                                                 ║
║    • Create: POST /api/appointments                            ║
║    • List:   GET  /api/appointments                            ║
║    • View:   GET  /api/appointments/:id                        ║
║    • Cancel: POST /api/appointments/:id/cancel                 ║
║    • Slots:  GET  /api/appointments/availability/:date         ║
║                                                                ║
║  Analytics:                                                    ║
║    • Chat: GET /api/analytics/chat                             ║
║    • Appt: GET /api/analytics/appointments                     ║
║                                                                ║
║  Demo Credentials:                                             ║
║    • Username: demo   | Password: demo123                      ║
║    • Username: admin  | Password: admin123                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;

