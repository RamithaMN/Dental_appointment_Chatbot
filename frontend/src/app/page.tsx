'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import LoginForm from '@/components/LoginForm';
import ChatInterface from '@/components/ChatInterface';
import AppointmentForm, { AppointmentData } from '@/components/AppointmentForm';

export default function Home() {
  const { isAuthenticated } = useAuth();
  const [showAppointmentForm, setShowAppointmentForm] = useState(false);

  const handleAppointmentSubmit = (appointment: AppointmentData) => {
    // Here you would typically send the appointment data to your backend
    console.log('Appointment submitted:', appointment);
    
    // For demo purposes, we'll just show an alert
    alert(`Appointment request submitted for ${appointment.name} on ${appointment.preferredDate} at ${appointment.preferredTime}`);
    
    setShowAppointmentForm(false);
  };

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <>
      <ChatInterface />
      {showAppointmentForm && (
        <AppointmentForm
          onSubmit={handleAppointmentSubmit}
          onCancel={() => setShowAppointmentForm(false)}
        />
      )}
    </>
  );
}