"""LangChain chatbot implementation with dental assistant prompt."""

from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.schema import BaseMessage
from typing import Dict, List
from llm_provider import llm_manager
from conversation_manager import ConversationSession
from config import settings
import logging

logger = logging.getLogger(__name__)


class DentalChatbot:
    """Dental assistant chatbot using LangChain."""
    
    # Dental assistant system prompt
    SYSTEM_PROMPT = """You are {chatbot_name}, a {chatbot_role} for a dental clinic. Your role is to:

1. **Greet patients warmly** and make them feel comfortable
2. **Answer questions** about dental services, procedures, and oral health
3. **Help with appointment scheduling** by collecting necessary information
4. **Provide general dental care advice** (while noting you're not a replacement for professional diagnosis)
5. **Be empathetic** especially with patients who may have dental anxiety

**IMPORTANT: Today's Date Context**
Today is {current_date}. 

CRITICAL: When patients mention relative dates, you MUST provide the EXACT date with day, month, and year:

- "tomorrow" = {tomorrow_date}
- "Monday" = {monday_date}  
- "Tuesday" = {tuesday_date}
- "Wednesday" = {wednesday_date}
- "Thursday" = {thursday_date}
- "Friday" = {friday_date}
- "Saturday" = {saturday_date}
- "Sunday" = {sunday_date}

CRITICAL: You MUST ALWAYS provide EXACT dates with full month, day, and year. NEVER use vague phrases like:
- "this upcoming Tuesday" 
- "next Tuesday"
- "the following Tuesday"
- "this Tuesday"
- "upcoming Tuesday"

ALWAYS say the exact date like "Tuesday, October 28, 2025" or "Tuesday, November 4, 2025".

CRITICAL APPOINTMENT RULE: When confirming appointments, you MUST always include the full date with month, day, and year. For example:
- Instead of "Tuesday at 12:00 PM" say "Tuesday, October 28, 2025 at 12:00 PM"
- Instead of "appointment for Tuesday" say "appointment for Tuesday, October 28, 2025"
- Always provide the complete date in appointment confirmations

**Services offered by our clinic:**
- General Dentistry (checkups, cleanings, fillings)
- Cosmetic Dentistry (whitening, veneers, bonding)
- Orthodontics (braces, Invisalign)
- Oral Surgery (extractions, wisdom teeth)
- Periodontics (gum disease treatment)
- Endodontics (root canals)
- Emergency Dental Care

**Office Hours:**
- Monday - Friday: 8:00 AM - 6:00 PM
- Saturday: 9:00 AM - 2:00 PM (ONLY offer times between 9:00 AM - 2:00 PM for Saturday appointments)
- Sunday: Closed
- Emergency line available 24/7

**CRITICAL SATURDAY RULE: When booking Saturday appointments, NEVER offer times after 2:00 PM. Saturday hours are strictly 9:00 AM - 2:00 PM.**

**IMPORTANT: When mentioning business hours, always say "Monday through Friday" or "Monday-Friday" without specific dates. Do NOT say "Monday, [date] through Friday, [date]" as this creates confusion.**

**FOR APPOINTMENT SCHEDULING: When showing availability for the current week, use the current week's Monday-Friday dates, not "next" dates.**

**APPOINTMENT BOOKING PROTOCOL:**
When a patient wants to book an appointment, collect this information IN ORDER:

1. **Name** - Get the patient's full name
2. **Date & Time** - Preferred appointment date and time
   - If they say "tomorrow" calculate the actual date
   - If they say a time like "4:30", confirm if they mean AM or PM
   - **IMPORTANT**: For Saturday appointments, only offer times between 9:00 AM - 2:00 PM
   - Common times: 9:00 AM, 10:00 AM, 2:00 PM (Monday-Friday: also 3:00 PM, 4:30 PM)
3. **Reason for Visit** - What type of appointment (checkup, cleaning, pain, emergency, etc.)
4. **Contact Phone** - Phone number to reach them

IMPORTANT APPOINTMENT GUIDELINES:
- Keep track of what information you've already collected
- Don't repeat questions you've already asked
- If the patient provides multiple pieces of information at once, acknowledge all of it
- Confirm all details before saying the appointment is "booked"
- Once you have ALL required information, provide a summary and say: "Great! I have all the details. To complete your booking, please click the 'Book Appointment' button below or I can have our staff call you to finalize it."
- Be natural in conversation - if they answer multiple questions at once, accept all the information

**Example Good Flow:**
User: "I want to book an appointment"
You: "I'd be happy to help you book an appointment! May I have your full name please?"
User: "Rohit"
You: "Thank you, Rohit! When would you like to come in? We're open Monday-Friday 8AM-6PM, and Saturdays 9AM-2PM."
User: "Tomorrow at 4:30"
You: "Perfect! 4:30 PM tomorrow. What brings you in - is this for a routine checkup, cleaning, or something specific?"
User: "cleaning"
You: "Excellent! A teeth cleaning appointment. Last thing - what's the best phone number to reach you at?"
User: "555-1234"
You: "Perfect! Let me confirm: Teeth cleaning appointment for Rohit tomorrow at 4:30 PM, and we'll call you at 555-1234 if needed. To complete your booking, please click the 'Book Appointment' button that will appear, or I can have our receptionist call you to finalize the booking. Is there anything else you'd like to know?"

**Guidelines:**
- Be friendly, professional, and reassuring
- REMEMBER what the patient has already told you in this conversation
- Don't make them repeat information
- If asked for medical diagnosis, remind them to see a dentist for proper examination  
- If you don't know something, be honest and offer to have someone call them back
- Keep responses concise but informative
- Use simple language, avoid complex medical jargon

Remember: Your goal is to help patients and make their experience as pleasant as possible!"""
    
    def __init__(self):
        """Initialize the dental chatbot."""
        self.llm = llm_manager.get_llm()
        logger.info("Dental chatbot initialized")
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        Create the prompt template for the conversation.
        
        Returns:
            ChatPromptTemplate: Configured prompt template
        """
        from datetime import datetime, timedelta
        
        today = datetime.now()
        current_date = today.strftime("%A, %B %d, %Y")
        
        # Calculate all days of the week
        tomorrow = today + timedelta(days=1)
        monday = today + timedelta(days=(7 - today.weekday()) % 7)
        if monday <= today:
            monday += timedelta(days=7)
        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        thursday = monday + timedelta(days=3)
        friday = monday + timedelta(days=4)
        saturday = monday + timedelta(days=5)
        sunday = monday + timedelta(days=6)
        
        date_context = {
            'current_date': current_date,
            'tomorrow_date': tomorrow.strftime("%A, %B %d, %Y"),
            'monday_date': monday.strftime("%A, %B %d, %Y"),
            'tuesday_date': tuesday.strftime("%A, %B %d, %Y"),
            'wednesday_date': wednesday.strftime("%A, %B %d, %Y"),
            'thursday_date': thursday.strftime("%A, %B %d, %Y"),
            'friday_date': friday.strftime("%A, %B %d, %Y"),
            'saturday_date': saturday.strftime("%A, %B %d, %Y"),
            'sunday_date': sunday.strftime("%A, %B %d, %Y")
        }
        
        logger.info(f"Setting date context: {date_context}")
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                self.SYSTEM_PROMPT.format(
                    chatbot_name=settings.CHATBOT_NAME,
                    chatbot_role=settings.CHATBOT_ROLE,
                    **date_context
                )
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
    
    def _create_conversation_chain(self, session: ConversationSession) -> ConversationChain:
        """
        Create a conversation chain for a session.
        
        Args:
            session: Conversation session
            
        Returns:
            ConversationChain: Configured conversation chain
        """
        prompt = self._create_prompt_template()
        
        chain = ConversationChain(
            llm=self.llm,
            prompt=prompt,
            memory=session.memory,
            verbose=settings.ENVIRONMENT == "development"
        )
        
        return chain
    
    async def chat(
        self,
        message: str,
        session: ConversationSession,
        context: Dict = None
    ) -> str:
        """
        Process a chat message and generate a response.
        
        Args:
            message: User's message
            session: Conversation session
            context: Optional additional context
            
        Returns:
            str: Chatbot's response
        """
        try:
            logger.info(f"Processing message for session {session.session_id}")
            
            # Create conversation chain
            chain = self._create_conversation_chain(session)
            
            # Add context if provided
            from datetime import datetime, timedelta
            
            today = datetime.now()
            current_date = today.strftime("%A, %B %d, %Y")
            
            # Calculate next Monday
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:  # If today is Monday, get next Monday
                days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            
            # Calculate all days of the week
            tomorrow = today + timedelta(days=1)
            days_until_tuesday = (1 - today.weekday()) % 7
            if days_until_tuesday == 0:  # If today is Tuesday, get next Tuesday
                days_until_tuesday = 7
            next_tuesday = today + timedelta(days=days_until_tuesday)
            
            input_text = f"""SYSTEM: Today is {current_date}. Next Tuesday is {next_tuesday.strftime('%A, %B %d, %Y')}.

INSTRUCTION: When the user mentions "Tuesday", you MUST respond with the exact date: {next_tuesday.strftime('%A, %B %d, %Y')}. Do NOT use phrases like "next Tuesday" or "the following Tuesday". Always provide the full date with day, month, and year.

User message: {message}"""
            if context:
                context_str = self._format_context(context)
                input_text = f"""SYSTEM: Today is {current_date}. Next Tuesday is {next_tuesday.strftime('%A, %B %d, %Y')}.

INSTRUCTION: When the user mentions "Tuesday", you MUST respond with the exact date: {next_tuesday.strftime('%A, %B %d, %Y')}. Do NOT use phrases like "next Tuesday" or "the following Tuesday". Always provide the full date with day, month, and year.

{context_str}

User message: {message}"""
            
            # Generate response
            response = await chain.apredict(input=input_text)
            
            # Post-process response to replace any date placeholders and provide exact dates
            from datetime import datetime, timedelta
            import re
            
            today = datetime.now()
            current_date = today.strftime("%A, %B %d, %Y")
            
            # Replace common date placeholders with actual dates
            response = response.replace("[insert current date]", current_date)
            response = response.replace("[insert date]", current_date)
            response = response.replace("[insert date based on today's date]", current_date)
            response = response.replace("[please calculate the current date]", current_date)
            
            # Also replace any remaining date placeholders
            response = re.sub(r'\[.*?date.*?\]', current_date, response, flags=re.IGNORECASE)
            
            # Calculate all days of the week
            tomorrow = today + timedelta(days=1)
            
            # Calculate current week's Monday-Friday for business hours context
            days_since_monday = today.weekday()
            current_week_monday = today - timedelta(days=days_since_monday)
            current_week_friday = current_week_monday + timedelta(days=4)
            
            # Calculate next Monday for specific bookings
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:  # If today is Monday, get next Monday
                days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            
            days_until_tuesday = (1 - today.weekday()) % 7
            if days_until_tuesday == 0:  # If today is Tuesday, get next Tuesday
                days_until_tuesday = 7
            next_tuesday = today + timedelta(days=days_until_tuesday)
            
            days_until_wednesday = (2 - today.weekday()) % 7
            if days_until_wednesday == 0:  # If today is Wednesday, get next Wednesday
                days_until_wednesday = 7
            next_wednesday = today + timedelta(days=days_until_wednesday)
            
            days_until_thursday = (3 - today.weekday()) % 7
            if days_until_thursday == 0:  # If today is Thursday, get next Thursday
                days_until_thursday = 7
            next_thursday = today + timedelta(days=days_until_thursday)
            
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0:  # If today is Friday, get next Friday
                days_until_friday = 7
            next_friday = today + timedelta(days=days_until_friday)
            
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0:  # If today is Saturday, get next Saturday
                days_until_saturday = 7
            next_saturday = today + timedelta(days=days_until_saturday)
            
            days_until_sunday = (6 - today.weekday()) % 7
            if days_until_sunday == 0:  # If today is Sunday, get next Sunday
                days_until_sunday = 7
            next_sunday = today + timedelta(days=days_until_sunday)
            
            # Note: Day references are replaced later in the _force_exact_dates method to avoid double replacement
            
            # Apply comprehensive date replacement in one pass to avoid duplication
            response = self._apply_date_replacements(response, today, input_text)
            
            # Update session
            session.add_message(message, response)
            
            logger.info(f"Generated response for session {session.session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return self._get_error_response()
    
    def _format_context(self, context: Dict) -> str:
        """
        Format additional context for the prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            str: Formatted context string
        """
        parts = []
        if context.get("user_name"):
            parts.append(f"User's name: {context['user_name']}")
        if context.get("previous_appointments"):
            parts.append(f"Previous appointments: {context['previous_appointments']}")
        if context.get("notes"):
            parts.append(f"Notes: {context['notes']}")
        
        return "\n".join(parts) if parts else ""
    
    def _format_appointment_summary(self, response: str, today) -> str:
        """
        Format appointment summary with exact dates and times.
        
        Args:
            response: Original response from LLM
            today: Current datetime object
            
        Returns:
            str: Formatted response with exact dates
        """
        from datetime import timedelta
        import re
        
        # Calculate next days
        tomorrow = today + timedelta(days=1)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)
        
        days_until_wednesday = (2 - today.weekday()) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        next_wednesday = today + timedelta(days=days_until_wednesday)
        
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        next_thursday = today + timedelta(days=days_until_thursday)
        
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        next_friday = today + timedelta(days=days_until_friday)
        
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        next_saturday = today + timedelta(days=days_until_saturday)
        
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        # Create a comprehensive replacement map
        replacements = {
            'Monday': f"Monday, {next_monday.strftime('%B %d, %Y')}",
            'Tuesday': f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}",
            'Wednesday': f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}",
            'Thursday': f"Thursday, {next_thursday.strftime('%B %d, %Y')}",
            'Friday': f"Friday, {next_friday.strftime('%B %d, %Y')}",
            'Saturday': f"Saturday, {next_saturday.strftime('%B %d, %Y')}",
            'Sunday': f"Sunday, {next_sunday.strftime('%B %d, %Y')}",
            'tomorrow': f"tomorrow ({tomorrow.strftime('%A, %B %d, %Y')})"
        }
        
        # Apply replacements more aggressively for appointment summaries
        # Only replace day names that are NOT already followed by a date (to avoid double replacement)
        for day, replacement in replacements.items():
            # Match day name NOT followed by comma and date pattern
            pattern = r'\b' + day + r'\b(?!\s*,\s*\w+\s+\d{1,2},\s*\d{4})'
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Replace vague date phrases with exact dates
        vague_phrases = [
            (r'\bthis upcoming Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bnext Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthe following Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthis Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bnext Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthe following Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthis Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}")
        ]
        
        for pattern, replacement in vague_phrases:
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # If the response contains appointment booking language, add a summary
        if any(phrase in response.lower() for phrase in ['appointment', 'booking', 'scheduled', 'confirmed']):
            # Extract time if mentioned
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', response)
            if time_match:
                time_str = time_match.group(1)
                # Add a clear summary at the end with exact date
                # Find which day was mentioned and get its exact date
                mentioned_day = None
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                    if day in response:
                        mentioned_day = day
                        break
                
                if mentioned_day:
                    day_date = replacements.get(mentioned_day, f"{mentioned_day}")
                    response += f"\n\n📅 **Appointment Summary:** Your appointment is scheduled for {time_str} on {day_date}."
                else:
                    response += f"\n\n📅 **Appointment Summary:** Your appointment is scheduled for {time_str} on the date mentioned above."
        
        return response
    
    def _apply_date_replacements(self, response: str, today, input_text: str) -> str:
        """
        Apply all date replacements in one comprehensive pass to avoid duplication.
        
        Args:
            response: Original response from LLM
            today: Current datetime object
            
        Returns:
            str: Response with exact dates (no duplication)
        """
        from datetime import timedelta
        import re
        
        # Calculate all days of the week
        tomorrow = today + timedelta(days=1)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)
        
        days_until_wednesday = (2 - today.weekday()) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        next_wednesday = today + timedelta(days=days_until_wednesday)
        
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        next_thursday = today + timedelta(days=days_until_thursday)
        
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        next_friday = today + timedelta(days=days_until_friday)
        
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        next_saturday = today + timedelta(days=days_until_saturday)
        
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        # Create comprehensive replacement map
        replacements = {
            'Monday': f"Monday, {next_monday.strftime('%B %d, %Y')}",
            'Tuesday': f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}",
            'Wednesday': f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}",
            'Thursday': f"Thursday, {next_thursday.strftime('%B %d, %Y')}",
            'Friday': f"Friday, {next_friday.strftime('%B %d, %Y')}",
            'Saturday': f"Saturday, {next_saturday.strftime('%B %d, %Y')}",
            'Sunday': f"Sunday, {next_sunday.strftime('%B %d, %Y')}",
            'tomorrow': f"tomorrow ({tomorrow.strftime('%A, %B %d, %Y')})"
        }
        
        # Replace vague phrases first (these are more specific patterns)
        vague_phrases = [
            (r'\bthis upcoming Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bnext Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthe following Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthis Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bnext Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthe following Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthis Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Wednesday\b', f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}"),
            (r'\bnext Wednesday\b', f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}"),
            (r'\bthe following Wednesday\b', f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}"),
            (r'\bthis Wednesday\b', f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Wednesday\b', f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Thursday\b', f"Thursday, {next_thursday.strftime('%B %d, %Y')}"),
            (r'\bnext Thursday\b', f"Thursday, {next_thursday.strftime('%B %d, %Y')}"),
            (r'\bthe following Thursday\b', f"Thursday, {next_thursday.strftime('%B %d, %Y')}"),
            (r'\bthis Thursday\b', f"Thursday, {next_thursday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Thursday\b', f"Thursday, {next_thursday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Friday\b', f"Friday, {next_friday.strftime('%B %d, %Y')}"),
            (r'\bnext Friday\b', f"Friday, {next_friday.strftime('%B %d, %Y')}"),
            (r'\bthe following Friday\b', f"Friday, {next_friday.strftime('%B %d, %Y')}"),
            (r'\bthis Friday\b', f"Friday, {next_friday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Friday\b', f"Friday, {next_friday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Saturday\b', f"Saturday, {next_saturday.strftime('%B %d, %Y')}"),
            (r'\bnext Saturday\b', f"Saturday, {next_saturday.strftime('%B %d, %Y')}"),
            (r'\bthe following Saturday\b', f"Saturday, {next_saturday.strftime('%B %d, %Y')}"),
            (r'\bthis Saturday\b', f"Saturday, {next_saturday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Saturday\b', f"Saturday, {next_saturday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Sunday\b', f"Sunday, {next_sunday.strftime('%B %d, %Y')}"),
            (r'\bnext Sunday\b', f"Sunday, {next_sunday.strftime('%B %d, %Y')}"),
            (r'\bthe following Sunday\b', f"Sunday, {next_sunday.strftime('%B %d, %Y')}"),
            (r'\bthis Sunday\b', f"Sunday, {next_sunday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Sunday\b', f"Sunday, {next_sunday.strftime('%B %d, %Y')}")
        ]
        
        # Apply vague phrase replacements first
        for pattern, replacement in vague_phrases:
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Skip date replacement ONLY for pure business hours responses (not appointment scheduling)
        # Check if this response is ONLY about business hours (not appointment scheduling)
        business_hours_only_indicators = [
            'business hours', 'office hours', 'clinic hours', 'open hours',
            'what are your hours', 'when are you open', 'hours', 'operating hours'
        ]
        
        appointment_scheduling_indicators = [
            'schedule an appointment', 'book an appointment', 'appointment for',
            'when would you like to come in', 'preferred date', 'appointment on'
        ]
        
        is_business_hours_only = any(indicator in response.lower() for indicator in business_hours_only_indicators)
        is_appointment_scheduling = any(indicator in response.lower() for indicator in appointment_scheduling_indicators)
        
        # Apply date replacement for appointment scheduling, skip for business hours only
        if is_appointment_scheduling or not is_business_hours_only:
            # For appointment scheduling, use appropriate week's Monday-Friday dates
            if is_appointment_scheduling:
                # Calculate all possible dates for comprehensive coverage
                # Current week dates
                days_since_monday = today.weekday()
                current_week_monday = today - timedelta(days=days_since_monday)
                current_week_tuesday = current_week_monday + timedelta(days=1)
                current_week_wednesday = current_week_monday + timedelta(days=2)
                current_week_thursday = current_week_monday + timedelta(days=3)
                current_week_friday = current_week_monday + timedelta(days=4)
                current_week_saturday = current_week_monday + timedelta(days=5)
                current_week_sunday = current_week_monday + timedelta(days=6)
                
                # Next week dates
                days_until_next_monday = (7 - today.weekday()) % 7
                if days_until_next_monday == 0:
                    days_until_next_monday = 7
                next_week_monday = today + timedelta(days=days_until_next_monday)
                next_week_tuesday = next_week_monday + timedelta(days=1)
                next_week_wednesday = next_week_monday + timedelta(days=2)
                next_week_thursday = next_week_monday + timedelta(days=3)
                next_week_friday = next_week_monday + timedelta(days=4)
                next_week_saturday = next_week_monday + timedelta(days=5)
                next_week_sunday = next_week_monday + timedelta(days=6)
                
                # Create comprehensive replacements that handle both current and next week
                # For appointment scheduling, prioritize next week for Monday-Friday range
                # but allow current week for individual day bookings
                week_replacements = {
                    # For Monday-Friday range, use next week to avoid past dates
                    'Monday': f"Monday, {next_week_monday.strftime('%B %d, %Y')}",
                    'Tuesday': f"Tuesday, {next_week_tuesday.strftime('%B %d, %Y')}",
                    'Wednesday': f"Wednesday, {next_week_wednesday.strftime('%B %d, %Y')}",
                    'Thursday': f"Thursday, {next_week_thursday.strftime('%B %d, %Y')}",
                    'Friday': f"Friday, {next_week_friday.strftime('%B %d, %Y')}",
                    # For Saturday and Sunday, use next week for appointment scheduling to avoid past dates
                    'Saturday': f"Saturday, {next_week_saturday.strftime('%B %d, %Y')}",
                    'Sunday': f"Sunday, {next_week_sunday.strftime('%B %d, %Y')}",
                    'tomorrow': f"tomorrow ({tomorrow.strftime('%A, %B %d, %Y')})"
                }
                
                # Apply week replacements only if the response doesn't contain specific dates
                # Check if response contains specific dates (like "November 5" or "5th November" or "December 7, 2025")
                has_specific_dates = re.search(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?', response) or \
                                    re.search(r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)', response) or \
                                    re.search(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}', response)
                
                # Also check if user is asking about "next month" - don't apply date replacements in this case
                is_next_month_request = any(phrase in input_text.lower() for phrase in ['next month', 'following month', 'upcoming month'])
                
                
                if not has_specific_dates and not is_next_month_request:
                    for day, replacement in week_replacements.items():
                        pattern = r'\b' + day + r'\b(?!\s*,\s*\w+\s+\d{1,2},\s*\d{4})'
                        response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
                
                # Check for Sunday appointment requests and handle them appropriately
                # Extract just the user message part (after "User message:")
                user_message_start = input_text.find("User message:")
                if user_message_start != -1:
                    user_message = input_text[user_message_start + len("User message:"):].strip()
                    # Check if the user mentioned a specific date that falls on a Sunday
                    # Handle both formats: "December 14th" and "14th december" (case-insensitive)
                    user_date_match = re.search(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?', user_message, re.IGNORECASE) or \
                                     re.search(r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)', user_message, re.IGNORECASE)
                    if user_date_match:
                        try:
                            from datetime import datetime
                            date_str = user_date_match.group(0)
                            # Clean up the date string
                            date_str = re.sub(r'\b(\d{1,2})(?:st|nd|rd|th)\b', r'\1', date_str)
                            
                            # Parse the date - handle both "December 14" and "14 december" formats
                            if ',' in date_str:
                                user_date = datetime.strptime(date_str, "%B %d, %Y")
                            else:
                                try:
                                    # Try "December 14" format first
                                    user_date = datetime.strptime(date_str, "%B %d")
                                except ValueError:
                                    try:
                                        # Try "14 december" format
                                        user_date = datetime.strptime(date_str, "%d %B")
                                    except ValueError:
                                        # If both fail, skip this date
                                        user_date = None
                                
                                if user_date and user_date.year == 1900:
                                    user_date = user_date.replace(year=2025)
                            
                            # Check if it's a Sunday
                            if user_date:
                                if user_date.strftime("%A") == "Sunday":
                                    response = f"I'm sorry, but our clinic is closed on Sundays. {user_date.strftime('%A, %B %d, %Y')} is not available for appointments. We're open Monday through Friday from 8:00 AM to 6:00 PM, and Saturday from 9:00 AM to 2:00 PM. Would you like to choose a different day for your appointment?"
                        except ValueError:
                            # If date parsing fails, continue with normal processing
                            pass
                
                # Fix incorrect day-of-week calculations for specific dates
                # Check if response contains a specific date with a day of the week
                date_day_match = re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?', response)
                if date_day_match:
                    full_match = date_day_match.group(0)
                    # Extract the day of the week and date
                    day_match = re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', full_match)
                    date_match = re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?', full_match)
                    
                    if day_match and date_match:
                        mentioned_day = day_match.group(0)
                        date_str = date_match.group(0)
                        
                        # Parse the date to get the actual day of the week
                        try:
                            from datetime import datetime
                            # Handle different date formats
                            if ',' in date_str:
                                actual_date = datetime.strptime(date_str, "%B %d, %Y")
                            else:
                                actual_date = datetime.strptime(date_str, "%B %d")
                                # If no year, assume current year
                                if actual_date.year == 1900:
                                    actual_date = actual_date.replace(year=2025)
                            
                            actual_day = actual_date.strftime("%A")
                            
                            # If the mentioned day doesn't match the actual day, fix it
                            if mentioned_day != actual_day:
                                response = response.replace(f"{mentioned_day}, {date_str}", f"{actual_day}, {date_str}")
                                response = response.replace(f"{mentioned_day} {date_str}", f"{actual_day} {date_str}")
                            
                            # Check if the appointment is requested for a Sunday (clinic closed)
                            if actual_day == "Sunday":
                                # Replace the response to inform about Sunday closure
                                response = f"I'm sorry, but our clinic is closed on Sundays. {actual_day}, {date_str} is not available for appointments. We're open Monday through Friday from 8:00 AM to 6:00 PM, and Saturday from 9:00 AM to 2:00 PM. Would you like to choose a different day for your appointment?"
                        except ValueError:
                            # If date parsing fails, skip correction
                            pass
            else:
                # For other cases, use next week dates
                for day, replacement in replacements.items():
                    pattern = r'\b' + day + r'\b(?!\s*,\s*\w+\s+\d{1,2},\s*\d{4})'
                    response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Only add appointment summary if this looks like a confirmed booking with specific details
        # Check for indicators that this is a confirmed appointment, not just an inquiry
        is_confirmed_booking = (
            any(phrase in response.lower() for phrase in ['confirmed', 'scheduled', 'booked', 'finalized']) or
            ('appointment' in response.lower() and any(phrase in response.lower() for phrase in ['details', 'information', 'scheduled for', 'booked for']))
        )
        
        # Exclude cancellation, change, or reschedule requests from getting appointment summaries
        is_cancellation_or_change = (
            any(phrase in response.lower() for phrase in ['cancel', 'cancelled', 'cancellation', 'change', 'reschedule', 'modify', 'update']) or
            any(phrase in input_text.lower() for phrase in ['cancel', 'change', 'reschedule', 'modify', 'update', 'different time', 'different date'])
        )
        
        # Check if the response already contains an appointment summary to avoid duplication
        has_existing_summary = (
            '📅 **Appointment Summary:**' in response or
            '**Appointment Summary:**' in response or
            'appointment summary' in response.lower() or
            '**Patient Name:**' in response or
            '**Date & Time:**' in response or
            '**Appointment Type:**' in response
        )
        
        if is_confirmed_booking and not has_existing_summary and not is_cancellation_or_change:
            # Extract patient name from the response and input text
            name_patterns = [
                # Two-word names
                r'for\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',  # "for John Doe"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+for',  # "John Doe for"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+at',   # "John Doe at"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+on',   # "John Doe on"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+appointment',  # "John Doe appointment"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+),',       # "John Doe,"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\.',      # "John Doe."
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+you',   # "John Doe you"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+we',    # "John Doe we"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+your',  # "John Doe your"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+for\s+',  # "John Doe for "
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+at\s+',   # "John Doe at "
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+on\s+',   # "John Doe on "
                # Single names
                r'for\s+([A-Z][a-z]+)',  # "for John"
                r'([A-Z][a-z]+)\s+for',  # "John for"
                r'([A-Z][a-z]+)\s+at',   # "John at"
                r'([A-Z][a-z]+)\s+on',   # "John on"
                r'([A-Z][a-z]+)\s+appointment',  # "John appointment"
                r'([A-Z][a-z]+),',       # "John,"
                r'([A-Z][a-z]+)\.',      # "John."
                r'([A-Z][a-z]+)\s+you',   # "John you"
                r'([A-Z][a-z]+)\s+we',    # "John we"
                r'([A-Z][a-z]+)\s+your',  # "John your"
                r'([A-Z][a-z]+)\s+for\s+',  # "John for "
                r'([A-Z][a-z]+)\s+at\s+',   # "John at "
                r'([A-Z][a-z]+)\s+on\s+',   # "John on "
            ]
            
            # Also check input text for names mentioned by user
            input_name_patterns = [
                r'User message:\s*([A-Z][a-z]+)',  # Single name after "User message:"
                r'User message:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Two-word name after "User message:"
                r'([A-Z][a-z]+)\s*$',  # Single name at end of input
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*$',  # Two-word name at end of input
            ]
            
            patient_name = None
            # First try to extract from response
            for pattern in name_patterns:
                name_match = re.search(pattern, response)
                if name_match:
                    patient_name = name_match.group(1)
                    break
            
            # If no name found in response, try to extract from input text
            if not patient_name:
                for pattern in input_name_patterns:
                    name_match = re.search(pattern, input_text)
                    if name_match:
                        patient_name = name_match.group(1)
                        break
            
            # Extract time if mentioned
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', response)
            if time_match:
                time_str = time_match.group(1)
                # Find which day was mentioned and get its exact date
                mentioned_day = None
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                    if day in response:
                        mentioned_day = day
                        break
                
                if mentioned_day:
                    day_date = replacements.get(mentioned_day, f"{mentioned_day}")
                    # Create enhanced appointment summary with patient name
                    if patient_name:
                        response += f"\n\n📅 **Appointment Summary:**\n- **Patient Name:** {patient_name}\n- **Date & Time:** {day_date} at {time_str}\n\nTo confirm this appointment, please reply with 'CONFIRM' or let me know if you'd like to make any changes."
                    else:
                        response += f"\n\n📅 **Appointment Summary:** Your appointment is scheduled for {time_str} on {day_date}.\n\nTo confirm this appointment, please reply with 'CONFIRM' or let me know if you'd like to make any changes."
        
        return response

    def _force_exact_dates(self, response: str, today) -> str:
        """
        Force exact dates in any response containing day names.
        
        Args:
            response: Original response from LLM
            today: Current datetime object
            
        Returns:
            str: Response with exact dates
        """
        from datetime import timedelta
        import re
        
        # Calculate all days of the week
        tomorrow = today + timedelta(days=1)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)
        
        days_until_wednesday = (2 - today.weekday()) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        next_wednesday = today + timedelta(days=days_until_wednesday)
        
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        next_thursday = today + timedelta(days=days_until_thursday)
        
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        next_friday = today + timedelta(days=days_until_friday)
        
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        next_saturday = today + timedelta(days=days_until_saturday)
        
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        # Create comprehensive replacement map
        replacements = {
            'Monday': f"Monday, {next_monday.strftime('%B %d, %Y')}",
            'Tuesday': f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}",
            'Wednesday': f"Wednesday, {next_wednesday.strftime('%B %d, %Y')}",
            'Thursday': f"Thursday, {next_thursday.strftime('%B %d, %Y')}",
            'Friday': f"Friday, {next_friday.strftime('%B %d, %Y')}",
            'Saturday': f"Saturday, {next_saturday.strftime('%B %d, %Y')}",
            'Sunday': f"Sunday, {next_sunday.strftime('%B %d, %Y')}",
            'tomorrow': f"tomorrow ({tomorrow.strftime('%A, %B %d, %Y')})"
        }
        
        # Apply all replacements aggressively
        # Only replace day names that are NOT already followed by a date (to avoid double replacement)
        for day, replacement in replacements.items():
            # Match day name NOT followed by comma and date pattern
            pattern = r'\b' + day + r'\b(?!\s*,\s*\w+\s+\d{1,2},\s*\d{4})'
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Replace vague phrases
        vague_phrases = [
            (r'\bthis upcoming Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bnext Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthe following Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthis Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Tuesday\b', f"Tuesday, {next_tuesday.strftime('%B %d, %Y')}"),
            (r'\bthis upcoming Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bnext Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthe following Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bthis Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}"),
            (r'\bupcoming Monday\b', f"Monday, {next_monday.strftime('%B %d, %Y')}")
        ]
        
        for pattern, replacement in vague_phrases:
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _get_error_response(self) -> str:
        """
        Get a friendly error response.
        
        Returns:
            str: Error response message
        """
        return (
            "I apologize, but I'm having trouble processing your request right now. "
            "Please try again, or if this continues, feel free to call our office directly. "
            "Is there anything else I can help you with?"
        )
    
    def get_conversation_summary(self, session: ConversationSession) -> str:
        """
        Get a summary of the conversation.
        
        Args:
            session: Conversation session
            
        Returns:
            str: Conversation summary
        """
        history = session.get_history()
        
        if not history:
            return "No conversation history yet."
        
        # Simple summary - could be enhanced with LLM summarization
        message_count = len([m for m in history if isinstance(m, BaseMessage)])
        return f"Conversation with {message_count} messages"
    
    def extract_appointment_info(self, session: ConversationSession) -> Dict:
        """
        Extract appointment information from conversation.
        
        Args:
            session: Conversation session
            
        Returns:
            dict: Extracted appointment information
        """
        # This could be enhanced with LLM-based information extraction
        # For now, return a placeholder
        return {
            "has_appointment_request": False,
            "extracted_info": {}
        }


# Global chatbot instance
dental_chatbot = DentalChatbot()

