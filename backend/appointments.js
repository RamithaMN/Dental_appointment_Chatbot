/**
 * Appointment Scheduling Routes and Logic
 */

const express = require('express');
const db = require('./database');
const auth = require('./auth');

const router = express.Router();

/**
 * Create new appointment
 * POST /api/appointments
 */
router.post('/', auth.getCurrentUser, async (req, res) => {
  try {
    const {
      appointmentDate,
      appointmentTime,
      appointmentType,
      reasonForVisit,
      notes,
      chatSessionId
    } = req.body;

    // Validation
    if (!appointmentDate || !appointmentTime || !appointmentType || !reasonForVisit) {
      return res.status(400).json({
        detail: 'Missing required fields: appointmentDate, appointmentTime, appointmentType, reasonForVisit'
      });
    }

    // Get user details
    const user = await db.getUserByUsername(req.user.sub);
    if (!user) {
      return res.status(404).json({ detail: 'User not found' });
    }

    // Check slot availability
    const isAvailable = await db.checkSlotAvailability(appointmentDate, appointmentTime);
    if (!isAvailable) {
      return res.status(409).json({
        detail: 'This time slot is not available. Please choose another time.'
      });
    }

    // Create appointment
    const appointment = await db.createAppointment({
      patientId: user.id,
      patientName: user.full_name,
      patientEmail: user.email,
      patientPhone: user.phone,
      appointmentDate,
      appointmentTime,
      appointmentType,
      reasonForVisit,
      notes,
      chatSessionId
    });

    // Log audit event
    await db.logAudit({
      userId: user.id,
      username: user.username,
      action: 'CREATE_APPOINTMENT',
      resourceType: 'appointment',
      resourceId: appointment.id,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      requestMethod: req.method,
      requestPath: req.path,
      newValues: appointment,
      status: 'success'
    });

    res.status(201).json({
      message: 'Appointment created successfully',
      appointment: {
        id: appointment.id,
        appointmentDate: appointment.appointment_date,
        appointmentTime: appointment.appointment_time,
        appointmentType: appointment.appointment_type,
        status: appointment.status,
        reasonForVisit: appointment.reason_for_visit
      }
    });
  } catch (error) {
    console.error('Create appointment error:', error);
    res.status(500).json({
      detail: 'Failed to create appointment'
    });
  }
});

/**
 * Get user's appointments
 * GET /api/appointments
 */
router.get('/', auth.getCurrentUser, async (req, res) => {
  try {
    const user = await db.getUserByUsername(req.user.sub);
    if (!user) {
      return res.status(404).json({ detail: 'User not found' });
    }

    const status = req.query.status || null;
    const appointments = await db.getPatientAppointments(user.id, status);

    res.json({
      appointments: appointments.map(apt => ({
        id: apt.id,
        appointmentDate: apt.appointment_date,
        appointmentTime: apt.appointment_time,
        appointmentType: apt.appointment_type,
        status: apt.status,
        reasonForVisit: apt.reason_for_visit,
        dentistName: apt.dentist_name,
        notes: apt.notes,
        createdAt: apt.created_at
      }))
    });
  } catch (error) {
    console.error('Get appointments error:', error);
    res.status(500).json({
      detail: 'Failed to retrieve appointments'
    });
  }
});

/**
 * Get appointment by ID
 * GET /api/appointments/:id
 */
router.get('/:id', auth.getCurrentUser, async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await db.query(
      'SELECT * FROM appointments WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ detail: 'Appointment not found' });
    }

    const appointment = result.rows[0];

    // Check if user owns this appointment
    const user = await db.getUserByUsername(req.user.sub);
    if (user.id !== appointment.patient_id && user.role !== 'admin') {
      return res.status(403).json({ detail: 'Access denied' });
    }

    res.json({ appointment });
  } catch (error) {
    console.error('Get appointment error:', error);
    res.status(500).json({
      detail: 'Failed to retrieve appointment'
    });
  }
});

/**
 * Update appointment status
 * PATCH /api/appointments/:id/status
 */
router.patch('/:id/status', auth.getCurrentUser, async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!status) {
      return res.status(400).json({ detail: 'Status is required' });
    }

    const validStatuses = ['scheduled', 'confirmed', 'cancelled', 'completed', 'no_show', 'rescheduled'];
    if (!validStatuses.includes(status)) {
      return res.status(400).json({ 
        detail: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
      });
    }

    const updatedAppointment = await db.updateAppointmentStatus(id, status);

    if (!updatedAppointment) {
      return res.status(404).json({ detail: 'Appointment not found' });
    }

    // Log audit event
    const user = await db.getUserByUsername(req.user.sub);
    await db.logAudit({
      userId: user.id,
      username: user.username,
      action: 'UPDATE_APPOINTMENT_STATUS',
      resourceType: 'appointment',
      resourceId: id,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      requestMethod: req.method,
      requestPath: req.path,
      newValues: { status },
      status: 'success'
    });

    res.json({
      message: 'Appointment status updated',
      appointment: updatedAppointment
    });
  } catch (error) {
    console.error('Update appointment status error:', error);
    res.status(500).json({
      detail: 'Failed to update appointment status'
    });
  }
});

/**
 * Cancel appointment
 * POST /api/appointments/:id/cancel
 */
router.post('/:id/cancel', auth.getCurrentUser, async (req, res) => {
  try {
    const { id } = req.params;
    const { reason } = req.body;

    const user = await db.getUserByUsername(req.user.sub);

    const result = await db.query(
      `UPDATE appointments 
       SET status = 'cancelled',
           cancelled_by = $1,
           cancellation_reason = $2,
           cancelled_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $3
       RETURNING *`,
      [user.id, reason || null, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ detail: 'Appointment not found' });
    }

    // Log audit event
    await db.logAudit({
      userId: user.id,
      username: user.username,
      action: 'CANCEL_APPOINTMENT',
      resourceType: 'appointment',
      resourceId: id,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      newValues: { status: 'cancelled', reason },
      status: 'success'
    });

    res.json({
      message: 'Appointment cancelled successfully',
      appointment: result.rows[0]
    });
  } catch (error) {
    console.error('Cancel appointment error:', error);
    res.status(500).json({
      detail: 'Failed to cancel appointment'
    });
  }
});

/**
 * Get available time slots
 * GET /api/appointments/availability/:date
 */
router.get('/availability/:date', auth.getCurrentUser, async (req, res) => {
  try {
    const { date } = req.params;

    // Validate date format
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return res.status(400).json({ detail: 'Invalid date format. Use YYYY-MM-DD' });
    }

    const result = await db.query(
      'SELECT * FROM get_available_slots($1)',
      [date]
    );

    const slots = result.rows;

    res.json({
      date,
      available_slots: slots.map(slot => ({
        time: slot.slot_time,
        dentistId: slot.dentist_id,
        dentistName: slot.dentist_name
      }))
    });
  } catch (error) {
    console.error('Get availability error:', error);
    res.status(500).json({
      detail: 'Failed to retrieve available slots'
    });
  }
});

/**
 * Get upcoming appointments (admin/staff only)
 * GET /api/appointments/upcoming/all
 */
router.get('/upcoming/all', auth.getCurrentUser, async (req, res) => {
  try {
    const user = await db.getUserByUsername(req.user.sub);
    
    if (!['admin', 'staff', 'dentist'].includes(user.role)) {
      return res.status(403).json({ detail: 'Access denied' });
    }

    const limit = parseInt(req.query.limit) || 10;
    const appointments = await db.getUpcomingAppointments(limit);

    res.json({
      appointments
    });
  } catch (error) {
    console.error('Get upcoming appointments error:', error);
    res.status(500).json({
      detail: 'Failed to retrieve upcoming appointments'
    });
  }
});

module.exports = router;

