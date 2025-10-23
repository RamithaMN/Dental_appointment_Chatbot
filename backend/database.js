/**
 * PostgreSQL Database Connection and Query Utilities
 */

const { Pool } = require('pg');
const config = require('./config');

// Create PostgreSQL connection pool
const pool = new Pool({
  host: config.DB_HOST,
  port: config.DB_PORT,
  database: config.DB_NAME,
  user: config.DB_USER,
  password: config.DB_PASSWORD,
  max: 20, // Maximum number of clients in the pool
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Handle pool errors
pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

/**
 * Execute a query
 * @param {string} text - SQL query text
 * @param {Array} params - Query parameters
 * @returns {Promise<Object>} Query result
 */
async function query(text, params) {
  const start = Date.now();
  try {
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    
    if (config.NODE_ENV === 'development') {
      console.log('Executed query', { text, duration, rows: res.rowCount });
    }
    
    return res;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
}

/**
 * Get a client from the pool for transactions
 * @returns {Promise<Object>} Client object
 */
async function getClient() {
  const client = await pool.connect();
  const query = client.query.bind(client);
  const release = client.release.bind(client);
  
  // Set a timeout to release the client
  const timeout = setTimeout(() => {
    console.error('Client checkout timeout');
    client.release();
  }, 5000);
  
  // Monkey patch to clear timeout on release
  client.release = () => {
    clearTimeout(timeout);
    return release();
  };
  
  return client;
}

/**
 * Test database connection
 * @returns {Promise<boolean>} True if connection successful
 */
async function testConnection() {
  try {
    const result = await query('SELECT NOW() as current_time');
    console.log('✓ Database connected successfully at:', result.rows[0].current_time);
    return true;
  } catch (error) {
    console.error('✗ Database connection failed:', error.message);
    return false;
  }
}

/**
 * Close all database connections
 */
async function closePool() {
  await pool.end();
  console.log('Database pool closed');
}

// ================================================================
// User Queries
// ================================================================

/**
 * Get user by username
 * @param {string} username - Username
 * @returns {Promise<Object|null>} User object or null
 */
async function getUserByUsername(username) {
  const result = await query(
    'SELECT * FROM users WHERE username = $1 AND deleted_at IS NULL',
    [username]
  );
  return result.rows[0] || null;
}

/**
 * Get user by ID
 * @param {string} userId - User ID (UUID)
 * @returns {Promise<Object|null>} User object or null
 */
async function getUserById(userId) {
  const result = await query(
    'SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL',
    [userId]
  );
  return result.rows[0] || null;
}

/**
 * Update user last login timestamp
 * @param {string} userId - User ID
 */
async function updateLastLogin(userId) {
  await query(
    'UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = $1',
    [userId]
  );
}

// ================================================================
// Appointment Queries
// ================================================================

/**
 * Create new appointment
 * @param {Object} appointmentData - Appointment details
 * @returns {Promise<Object>} Created appointment
 */
async function createAppointment(appointmentData) {
  const {
    patientId,
    patientName,
    patientEmail,
    patientPhone,
    appointmentDate,
    appointmentTime,
    appointmentType,
    reasonForVisit,
    notes,
    chatSessionId
  } = appointmentData;
  
  const result = await query(
    `INSERT INTO appointments (
      patient_id, patient_name, patient_email, patient_phone,
      appointment_date, appointment_time, appointment_type,
      reason_for_visit, notes, chat_session_id, status
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'scheduled')
    RETURNING *`,
    [
      patientId, patientName, patientEmail, patientPhone,
      appointmentDate, appointmentTime, appointmentType,
      reasonForVisit, notes || null, chatSessionId || null
    ]
  );
  
  return result.rows[0];
}

/**
 * Get appointments for a patient
 * @param {string} patientId - Patient user ID
 * @param {string} status - Optional status filter
 * @returns {Promise<Array>} List of appointments
 */
async function getPatientAppointments(patientId, status = null) {
  let queryText = 'SELECT * FROM appointments WHERE patient_id = $1';
  const params = [patientId];
  
  if (status) {
    queryText += ' AND status = $2';
    params.push(status);
  }
  
  queryText += ' ORDER BY appointment_date DESC, appointment_time DESC';
  
  const result = await query(queryText, params);
  return result.rows;
}

/**
 * Get upcoming appointments
 * @param {number} limit - Number of appointments to return
 * @returns {Promise<Array>} List of upcoming appointments
 */
async function getUpcomingAppointments(limit = 10) {
  const result = await query(
    `SELECT * FROM v_upcoming_appointments
     LIMIT $1`,
    [limit]
  );
  return result.rows;
}

/**
 * Update appointment status
 * @param {string} appointmentId - Appointment ID
 * @param {string} newStatus - New status
 * @returns {Promise<Object>} Updated appointment
 */
async function updateAppointmentStatus(appointmentId, newStatus) {
  const result = await query(
    `UPDATE appointments 
     SET status = $1, updated_at = CURRENT_TIMESTAMP
     WHERE id = $2
     RETURNING *`,
    [newStatus, appointmentId]
  );
  return result.rows[0];
}

/**
 * Check appointment slot availability
 * @param {string} date - Appointment date (YYYY-MM-DD)
 * @param {string} time - Appointment time (HH:MM:SS)
 * @returns {Promise<boolean>} True if available
 */
async function checkSlotAvailability(date, time) {
  const result = await query(
    `SELECT COUNT(*) as count FROM appointments
     WHERE appointment_date = $1
     AND appointment_time = $2
     AND status NOT IN ('cancelled', 'no_show')`,
    [date, time]
  );
  return parseInt(result.rows[0].count) === 0;
}

// ================================================================
// Chat Session Queries
// ================================================================

/**
 * Create new chat session
 * @param {Object} sessionData - Session details
 * @returns {Promise<Object>} Created session
 */
async function createChatSession(sessionData) {
  const {
    userId,
    username,
    sessionToken,
    ipAddress,
    userAgent
  } = sessionData;
  
  const result = await query(
    `INSERT INTO chat_sessions (
      user_id, username, session_token, ip_address, user_agent, status
    ) VALUES ($1, $2, $3, $4, $5, 'active')
    RETURNING *`,
    [userId || null, username || null, sessionToken, ipAddress || null, userAgent || null]
  );
  
  return result.rows[0];
}

/**
 * Get chat session by token
 * @param {string} sessionToken - Session token
 * @returns {Promise<Object|null>} Session object or null
 */
async function getChatSession(sessionToken) {
  const result = await query(
    'SELECT * FROM chat_sessions WHERE session_token = $1',
    [sessionToken]
  );
  return result.rows[0] || null;
}

/**
 * Update chat session
 * @param {string} sessionId - Session ID
 * @param {Object} updates - Fields to update
 * @returns {Promise<Object>} Updated session
 */
async function updateChatSession(sessionId, updates) {
  const {
    messageCount,
    totalTokens,
    primaryIntent,
    appointmentCreated,
    appointmentId,
    feedbackRating,
    status
  } = updates;
  
  const result = await query(
    `UPDATE chat_sessions 
     SET 
       message_count = COALESCE($1, message_count),
       total_tokens_used = COALESCE($2, total_tokens_used),
       primary_intent = COALESCE($3, primary_intent),
       appointment_created = COALESCE($4, appointment_created),
       appointment_id = COALESCE($5, appointment_id),
       feedback_rating = COALESCE($6, feedback_rating),
       status = COALESCE($7, status),
       last_activity_at = CURRENT_TIMESTAMP
     WHERE id = $8
     RETURNING *`,
    [messageCount, totalTokens, primaryIntent, appointmentCreated, appointmentId, feedbackRating, status, sessionId]
  );
  return result.rows[0];
}

/**
 * End chat session
 * @param {string} sessionId - Session ID
 */
async function endChatSession(sessionId) {
  await query(
    `UPDATE chat_sessions 
     SET status = 'ended', ended_at = CURRENT_TIMESTAMP
     WHERE id = $1`,
    [sessionId]
  );
}

/**
 * Log chat message
 * @param {Object} messageData - Message details
 * @returns {Promise<Object>} Created message
 */
async function logChatMessage(messageData) {
  const {
    sessionId,
    role,
    messageText,
    tokensUsed,
    responseTimeMs,
    llmModel,
    detectedIntent,
    sequenceNumber
  } = messageData;
  
  const result = await query(
    `INSERT INTO chat_messages (
      session_id, role, message_text, tokens_used, response_time_ms,
      llm_model, detected_intent, sequence_number
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    RETURNING *`,
    [sessionId, role, messageText, tokensUsed || 0, responseTimeMs || null, llmModel || null, detectedIntent || null, sequenceNumber]
  );
  
  return result.rows[0];
}

// ================================================================
// Analytics Queries
// ================================================================

/**
 * Get chat analytics for date range
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {Promise<Array>} Analytics data
 */
async function getChatAnalytics(startDate, endDate) {
  const result = await query(
    `SELECT * FROM v_chat_analytics
     WHERE date BETWEEN $1 AND $2
     ORDER BY date DESC`,
    [startDate, endDate]
  );
  return result.rows;
}

/**
 * Get appointment statistics
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {Promise<Array>} Statistics data
 */
async function getAppointmentStats(startDate, endDate) {
  const result = await query(
    `SELECT * FROM v_daily_appointment_stats
     WHERE appointment_date BETWEEN $1 AND $2
     ORDER BY appointment_date DESC`,
    [startDate, endDate]
  );
  return result.rows;
}

// ================================================================
// Audit Log
// ================================================================

/**
 * Log audit event
 * @param {Object} auditData - Audit details
 */
async function logAudit(auditData) {
  const {
    userId,
    username,
    action,
    resourceType,
    resourceId,
    ipAddress,
    userAgent,
    requestMethod,
    requestPath,
    oldValues,
    newValues,
    status,
    errorMessage
  } = auditData;
  
  await query(
    `INSERT INTO audit_log (
      user_id, username, action, resource_type, resource_id,
      ip_address, user_agent, request_method, request_path,
      old_values, new_values, status, error_message
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
    [
      userId || null,
      username || null,
      action,
      resourceType || null,
      resourceId || null,
      ipAddress || null,
      userAgent || null,
      requestMethod || null,
      requestPath || null,
      oldValues ? JSON.stringify(oldValues) : null,
      newValues ? JSON.stringify(newValues) : null,
      status || 'success',
      errorMessage || null
    ]
  );
}

module.exports = {
  query,
  getClient,
  testConnection,
  closePool,
  
  // User functions
  getUserByUsername,
  getUserById,
  updateLastLogin,
  
  // Appointment functions
  createAppointment,
  getPatientAppointments,
  getUpcomingAppointments,
  updateAppointmentStatus,
  checkSlotAvailability,
  
  // Chat session functions
  createChatSession,
  getChatSession,
  updateChatSession,
  endChatSession,
  logChatMessage,
  
  // Analytics functions
  getChatAnalytics,
  getAppointmentStats,
  
  // Audit functions
  logAudit
};

