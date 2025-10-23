/**
 * Authentication utilities for JWT token generation and validation.
 */

const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const config = require('./config');

// Demo user database (in production, use a real database)
const DEMO_USERS = {
  demo: {
    username: 'demo',
    password_hash: '$2b$12$hLUsVYTWOIBfIM8Qrx8Nh.wzP6wCGbat5OpwULDYp5KV/6PP4vki2', // "demo123"
    full_name: 'Demo User',
    email: 'demo@example.com'
  },
  admin: {
    username: 'admin',
    password_hash: '$2b$12$t/OvQZ/qKMQR5mfbiliW2uAtfHIRjdEb5HQ55W1CJgtLRjZE6dWhe', // "admin123"
    full_name: 'Admin User',
    email: 'admin@example.com'
  }
};

/**
 * Create a JWT access token.
 * @param {Object} data - Payload data to encode in the token
 * @param {number} expiresInMinutes - Optional custom expiration time in minutes
 * @returns {string} Encoded JWT token
 */
function createAccessToken(data, expiresInMinutes = null) {
  const payload = {
    ...data,
    iat: Math.floor(Date.now() / 1000),
    type: 'access'
  };
  
  const expiresIn = expiresInMinutes || config.ACCESS_TOKEN_EXPIRE_MINUTES;
  
  const token = jwt.sign(payload, config.SECRET_KEY, {
    algorithm: config.ALGORITHM,
    expiresIn: `${expiresIn}m`
  });
  
  return token;
}

/**
 * Verify and decode a JWT token.
 * @param {string} token - JWT token string to verify
 * @returns {Object} Decoded token payload
 * @throws {Error} If token is invalid or expired
 */
function verifyToken(token) {
  try {
    const payload = jwt.verify(token, config.SECRET_KEY, {
      algorithms: [config.ALGORITHM]
    });
    return payload;
  } catch (error) {
    throw new Error(`Invalid token: ${error.message}`);
  }
}

/**
 * Verify a plain password against a hashed password.
 * @param {string} plainPassword - Plain text password
 * @param {string} hashedPassword - Hashed password to compare against
 * @returns {Promise<boolean>} True if password matches, false otherwise
 */
async function verifyPassword(plainPassword, hashedPassword) {
  return await bcrypt.compare(plainPassword, hashedPassword);
}

/**
 * Hash a password.
 * @param {string} password - Plain text password to hash
 * @returns {Promise<string>} Hashed password
 */
async function hashPassword(password) {
  const salt = await bcrypt.genSalt(12);
  return await bcrypt.hash(password, salt);
}

/**
 * Authenticate a user with username and password.
 * @param {string} username - Username
 * @param {string} password - Plain text password
 * @returns {Promise<Object|null>} User object if authenticated, null otherwise
 */
async function authenticateUser(username, password) {
  const user = DEMO_USERS[username];
  if (!user) {
    return null;
  }
  
  const isValid = await verifyPassword(password, user.password_hash);
  if (!isValid) {
    return null;
  }
  
  return user;
}

/**
 * Verify if the provided API key is valid.
 * @param {string} apiKey - API key to verify
 * @returns {boolean} True if valid, false otherwise
 */
function verifyApiKey(apiKey) {
  return apiKey === config.API_KEY;
}

/**
 * Express middleware to get the current authenticated user from JWT token.
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
function getCurrentUser(req, res, next) {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        detail: 'No valid authorization header found'
      });
    }
    
    const token = authHeader.substring(7); // Remove 'Bearer ' prefix
    const payload = verifyToken(token);
    
    req.user = payload;
    next();
  } catch (error) {
    return res.status(401).json({
      detail: `Invalid token: ${error.message}`
    });
  }
}

module.exports = {
  DEMO_USERS,
  createAccessToken,
  verifyToken,
  verifyPassword,
  hashPassword,
  authenticateUser,
  verifyApiKey,
  getCurrentUser
};

