'use client';

import React from 'react';
import { ChatMessage } from '@/hooks/useChat';
import { User, Bot, Clock, CheckCircle } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
  onConfirmAppointment?: () => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onConfirmAppointment }) => {
  const isUser = message.role === 'user';
  const timeString = message.timestamp.toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });

  // Check if this is an appointment summary message
  const isAppointmentSummary = !isUser && (
    message.content.includes('📅 **Appointment Summary:**') ||
    message.content.includes('To confirm this appointment') ||
    message.content.includes('Book Appointment') ||
    message.content.includes('book appointment') ||
    message.content.includes('click the \'Book Appointment\' button') ||
    message.content.includes('receptionist call you to finalize') ||
    message.content.includes('complete your booking')
  );

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-xs lg:max-w-md ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-200 text-gray-600'
          }`}>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </div>
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`px-4 py-2 rounded-lg ${
              isUser
                ? 'bg-blue-500 text-white rounded-br-sm'
                : 'bg-gray-100 text-gray-900 rounded-bl-sm'
            }`}
          >
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            
            {/* Appointment Confirmation Button */}
            {isAppointmentSummary && onConfirmAppointment && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <button
                  onClick={onConfirmAppointment}
                  className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Confirm Appointment
                </button>
              </div>
            )}
          </div>
          
          {/* Timestamp */}
          <div className={`flex items-center mt-1 text-xs text-gray-500 ${
            isUser ? 'flex-row-reverse' : 'flex-row'
          }`}>
            <Clock className="h-3 w-3 mr-1" />
            <span>{timeString}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
