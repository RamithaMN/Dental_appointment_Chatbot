/**
 * Chat Logging Middleware for Analytics
 */

const db = require('./database');
const { v4: uuidv4 } = require('crypto').randomUUID || require('uuid').v4;

/**
 * Initialize chat session
 * Creates a new session in the database when user starts chatting
 */
async function initializeChatSession(req, res, next) {
  try {
    // Skip if session already exists
    if (req.chatSession) {
      return next();
    }

    // Get user info from JWT token
    const userId = req.user?.sub ? (await db.getUserByUsername(req.user.sub))?.id : null;
    const username = req.user?.sub || null;

    // Generate session token
    const sessionToken = `session_${uuidv4()}`;

    // Create session in database
    const session = await db.createChatSession({
      userId,
      username,
      sessionToken,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent']
    });

    // Attach to request object
    req.chatSession = session;

    next();
  } catch (error) {
    console.error('Chat session initialization error:', error);
    // Don't fail the request, just log the error
    next();
  }
}

/**
 * Log chat interaction
 * Logs each message exchange for analytics
 */
async function logChatInteraction(req, res, next) {
  try {
    // Capture the original send and json functions
    const originalSend = res.send.bind(res);
    const originalJson = res.json.bind(res);
    
    // Store request data
    const requestStart = Date.now();
    const userMessage = req.body.message;
    
    // Get or create session
    let sessionId = req.chatSession?.id;
    if (!sessionId) {
      // Try to get session from header or create new one
      const sessionToken = req.headers['x-session-token'] || `session_${uuidv4()}`;
      let session = await db.getChatSession(sessionToken);
      
      if (!session) {
        const userId = req.user?.sub ? (await db.getUserByUsername(req.user.sub))?.id : null;
        session = await db.createChatSession({
          userId,
          username: req.user?.sub || null,
          sessionToken,
          ipAddress: req.ip,
          userAgent: req.headers['user-agent']
        });
      }
      
      sessionId = session.id;
      req.chatSession = session;
    }

    // Override res.json to capture response
    res.json = function(data) {
      // Log the interaction asynchronously
      logInteractionAsync(sessionId, userMessage, data, Date.now() - requestStart, req).catch(err => {
        console.error('Async chat logging error:', err);
      });
      
      // Send response
      return originalJson(data);
    };

    // Override res.send to capture response
    res.send = function(data) {
      // Try to parse response
      let responseData = data;
      try {
        if (typeof data === 'string') {
          responseData = JSON.parse(data);
        }
      } catch (e) {
        // Not JSON, keep original
      }

      // Log the interaction asynchronously
      logInteractionAsync(sessionId, userMessage, responseData, Date.now() - requestStart, req).catch(err => {
        console.error('Async chat logging error:', err);
      });
      
      // Send response
      return originalSend(data);
    };

    next();
  } catch (error) {
    console.error('Chat logging middleware error:', error);
    // Don't fail the request
    next();
  }
}

/**
 * Async function to log interaction to database
 */
async function logInteractionAsync(sessionId, userMessage, responseData, responseTimeMs, req) {
  try {
    // Get current message count
    const session = await db.query(
      'SELECT message_count FROM chat_sessions WHERE id = $1',
      [sessionId]
    );
    const messageCount = session.rows[0]?.message_count || 0;
    const sequenceNumber = messageCount + 1;

    // Log user message
    await db.logChatMessage({
      sessionId,
      role: 'user',
      messageText: userMessage,
      sequenceNumber,
      responseTimeMs: 0
    });

    // Log bot response
    const botMessage = responseData?.response || responseData?.message || JSON.stringify(responseData);
    await db.logChatMessage({
      sessionId,
      role: 'bot',
      messageText: botMessage,
      sequenceNumber: sequenceNumber + 1,
      responseTimeMs,
      llmModel: 'openai' // Could be dynamic based on config
    });

    // Update session stats
    await db.updateChatSession(sessionId, {
      messageCount: sequenceNumber + 1
    });

    // Detect intent from user message
    const intent = detectIntent(userMessage);
    if (intent && !session.rows[0]?.primary_intent) {
      await db.updateChatSession(sessionId, {
        primaryIntent: intent
      });
    }

    // Check if appointment was created
    if (responseData?.appointment || responseData?.appointment_id) {
      await db.updateChatSession(sessionId, {
        appointmentCreated: true,
        appointmentId: responseData.appointment_id || responseData.appointment?.id
      });
    }
  } catch (error) {
    console.error('Error logging interaction to database:', error);
  }
}

/**
 * Simple intent detection from user message
 * @param {string} message - User message
 * @returns {string|null} Detected intent
 */
function detectIntent(message) {
  if (!message) return null;
  
  const messageLower = message.toLowerCase();
  
  if (messageLower.match(/\b(appointment|schedule|book|reservation|visit)\b/)) {
    return 'appointment_scheduling';
  }
  if (messageLower.match(/\b(service|treatment|procedure|offer|do you)\b/)) {
    return 'service_inquiry';
  }
  if (messageLower.match(/\b(hours|open|closed|time|when)\b/)) {
    return 'office_hours';
  }
  if (messageLower.match(/\b(price|cost|fee|expensive|insurance|payment)\b/)) {
    return 'pricing';
  }
  if (messageLower.match(/\b(emergency|urgent|pain|hurt|ache)\b/)) {
    return 'emergency';
  }
  
  return 'general_question';
}

/**
 * End chat session
 * Marks session as ended when user logs out or times out
 */
async function endChatSessionMiddleware(req, res, next) {
  try {
    if (req.chatSession?.id) {
      await db.endChatSession(req.chatSession.id);
    }
    next();
  } catch (error) {
    console.error('End session error:', error);
    next();
  }
}

/**
 * Get chat analytics endpoint handler
 */
async function getChatAnalytics(req, res) {
  try {
    const { startDate, endDate } = req.query;
    
    if (!startDate || !endDate) {
      return res.status(400).json({
        detail: 'startDate and endDate query parameters are required'
      });
    }

    const analytics = await db.getChatAnalytics(startDate, endDate);
    
    res.json({
      analytics,
      period: { startDate, endDate }
    });
  } catch (error) {
    console.error('Get chat analytics error:', error);
    res.status(500).json({
      detail: 'Failed to retrieve chat analytics'
    });
  }
}

/**
 * Get appointment statistics endpoint handler
 */
async function getAppointmentAnalytics(req, res) {
  try {
    const { startDate, endDate } = req.query;
    
    if (!startDate || !endDate) {
      return res.status(400).json({
        detail: 'startDate and endDate query parameters are required'
      });
    }

    const stats = await db.getAppointmentStats(startDate, endDate);
    
    res.json({
      statistics: stats,
      period: { startDate, endDate }
    });
  } catch (error) {
    console.error('Get appointment analytics error:', error);
    res.status(500).json({
      detail: 'Failed to retrieve appointment statistics'
    });
  }
}

module.exports = {
  initializeChatSession,
  logChatInteraction,
  endChatSessionMiddleware,
  getChatAnalytics,
  getAppointmentAnalytics,
  detectIntent
};

