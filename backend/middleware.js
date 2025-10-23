/**
 * Express middleware functions for request handling, rate limiting, logging, and security.
 */

const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const morgan = require('morgan');
const fs = require('fs');
const path = require('path');

// Create logs directory if it doesn't exist
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir);
}

// Create a write stream for logging
const accessLogStream = fs.createWriteStream(
  path.join(logsDir, 'api.log'),
  { flags: 'a' }
);

/**
 * Rate limiting middleware
 * Limits each IP to 100 requests per 15 minutes
 */
const rateLimitMiddleware = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    detail: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Logging middleware using morgan
 */
const loggingMiddleware = morgan('combined', { stream: accessLogStream });

/**
 * Security headers middleware using helmet
 */
const securityHeadersMiddleware = helmet({
  contentSecurityPolicy: false, // Disable CSP for API
  crossOriginEmbedderPolicy: false
});

/**
 * Custom request logger middleware
 */
class RequestLogger {
  static logRequest(req) {
    const logData = {
      timestamp: new Date().toISOString(),
      method: req.method,
      path: req.path,
      query: req.query,
      ip: req.ip || req.connection.remoteAddress,
      userAgent: req.get('user-agent') || 'Unknown',
      userId: req.body?.user_id || req.user?.sub || null
    };
    
    console.log(`[${logData.timestamp}] ${logData.method} ${logData.path} - IP: ${logData.ip}`);
    return logData;
  }
  
  static logResponse(res, req, statusCode) {
    const logData = {
      timestamp: new Date().toISOString(),
      statusCode: statusCode || res.statusCode,
      path: req.path,
      ip: req.ip || req.connection.remoteAddress,
      userId: req.body?.user_id || req.user?.sub || null
    };
    
    console.log(`[${logData.timestamp}] Response ${logData.statusCode} for ${req.method} ${logData.path}`);
    return logData;
  }
}

/**
 * Request validation middleware
 * Adds processing time header to responses
 */
function requestValidationMiddleware(req, res, next) {
  req.startTime = Date.now();
  
  // Override the res.json and res.send methods to add processing time header
  const originalJson = res.json.bind(res);
  const originalSend = res.send.bind(res);
  
  res.json = function(data) {
    const processingTime = (Date.now() - req.startTime) / 1000;
    res.setHeader('X-Process-Time', processingTime.toFixed(3));
    return originalJson(data);
  };
  
  res.send = function(data) {
    const processingTime = (Date.now() - req.startTime) / 1000;
    res.setHeader('X-Process-Time', processingTime.toFixed(3));
    return originalSend(data);
  };
  
  next();
}

/**
 * Custom security headers middleware
 */
function customSecurityHeaders(req, res, next) {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  next();
}

/**
 * Error handling middleware
 */
function errorHandler(err, req, res, next) {
  console.error('Error:', err);
  
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal server error';
  
  res.status(statusCode).json({
    detail: message,
    error: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });
}

module.exports = {
  rateLimitMiddleware,
  loggingMiddleware,
  securityHeadersMiddleware,
  requestValidationMiddleware,
  customSecurityHeaders,
  errorHandler,
  RequestLogger
};

