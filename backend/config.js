/**
 * Configuration settings for the chatbot API.
 * Loads settings from environment variables with defaults.
 */

require('dotenv').config();

const config = {
  // JWT Configuration
  SECRET_KEY: process.env.SECRET_KEY || '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7',
  ALGORITHM: process.env.ALGORITHM || 'HS256',
  ACCESS_TOKEN_EXPIRE_MINUTES: parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES || '15'),
  
  // API Configuration
  API_KEY: process.env.API_KEY || 'dental-chatbot-api-key-2025',
  
  // Server Configuration
  PORT: parseInt(process.env.PORT || '8000'),
  NODE_ENV: process.env.NODE_ENV || 'development',
  
  // Chatbot Service Configuration
  CHATBOT_SERVICE_URL: process.env.CHATBOT_SERVICE_URL || 'http://localhost:8001',
  
  // Database Configuration
  DB_HOST: process.env.DB_HOST || 'localhost',
  DB_PORT: parseInt(process.env.DB_PORT || '5432'),
  DB_NAME: process.env.DB_NAME || 'dental_chatbot',
  DB_USER: process.env.DB_USER || 'dental_user',
  DB_PASSWORD: process.env.DB_PASSWORD || 'dental_pass_2025',
  
  // CORS Configuration
  ALLOWED_ORIGINS: ['http://localhost:3000', 'http://localhost:3001']
};

module.exports = config;

