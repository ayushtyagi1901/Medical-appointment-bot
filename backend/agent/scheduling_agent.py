import os
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import google.generativeai as genai

from .prompts import SYSTEM_PROMPT, format_user_prompt_with_context
from ..tools.availability_tool import get_available_slots, format_slots_for_display
from ..tools.booking_tool import (
    book_appointment, BookingRequest,
    reschedule_appointment, cancel_appointment, add_to_waitlist,
    get_appointment
)
from ..rag.faq_rag import answer_faq_with_rag, retrieve_faq_context
from ..models.schemas import AppointmentType, RescheduleRequest, CancelRequest, WaitlistRequest

# Lazy initialization of Gemini client
_model = None

def get_model():
    """Get or create Gemini model instance."""
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        model_name = os.getenv("LLM_MODEL", "gemini-flash-latest")
        # Remove 'models/' prefix if present, Gemini API adds it automatically
        if model_name.startswith("models/"):
            model_name = model_name.replace("models/", "")
        _model = genai.GenerativeModel(model_name)
    return _model


class SchedulingAgent:
    """Main conversation agent that handles scheduling and FAQ answering."""
    
    def __init__(self):
        pass
    
    def get_client(self):
        """Get Gemini model (kept for backward compatibility)."""
        return get_model()
    
    def detect_intent(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """
        Detect user intent: 'scheduling' or 'faq'.
        
        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            'scheduling' or 'faq'
        """
        message_lower = user_message.lower()
        
        # Keywords for scheduling
        scheduling_keywords = [
            'appointment', 'schedule', 'book', 'available', 'slot', 'time',
            'doctor', 'visit', 'see', 'meet', 'consultation', 'when can i',
            'i need', 'i want to', 'make an appointment', 'show me', 'options',
            'show options', 'times available', 'available times'
        ]
        
        # Keywords for FAQ (enhanced - includes more patterns)
        faq_keywords = [
            'what are', 'how do', 'when are', 'where is', 'why', 'hours', 'open', 'closed',
            'insurance', 'accept', 'parking', 'cancel policy', 'cost',
            'price', 'fee', 'service', 'provide', 'do you accept', 'can i get',
            'what should i bring', 'what to bring', 'bring to', 'required', 'documents',
            'how do i cancel', 'how to cancel', 'how do i reschedule', 'how to reschedule',
            'cancel or reschedule', 'reschedule or cancel', 'cancellation', 'rescheduling',
            'what is the address', 'address', 'location', 'directions',
            'what time', 'what are your', 'tell me about', 'information about'
        ]
        
        scheduling_score = sum(1 for keyword in scheduling_keywords if keyword in message_lower)
        faq_score = sum(1 for keyword in faq_keywords if keyword in message_lower)
        
        # Check conversation history for context
        if conversation_history:
            recent_messages = " ".join([
                msg.get("content", "").lower()
                for msg in conversation_history[-3:]
            ])
            if any(kw in recent_messages for kw in scheduling_keywords):
                scheduling_score += 2
            if any(kw in recent_messages for kw in faq_keywords):
                faq_score += 2
        
        # Check for explicit scheduling keywords (strong indicators)
        if any(kw in message_lower for kw in ["show", "options", "available", "slots", "times"]):
            # If in scheduling context (conversation history), prioritize scheduling
            if conversation_history:
                recent_context = " ".join([msg.get("content", "").lower() for msg in conversation_history[-2:]])
                if any(kw in recent_context for kw in ["appointment", "book", "schedule", "date", "prefer"]):
                    return "scheduling"
        
        # Default to scheduling if ambiguous, but prioritize based on scores
        if faq_score > scheduling_score + 1:
            return "faq"
        elif "schedule" in message_lower or "appointment" in message_lower or "book" in message_lower:
            return "scheduling"
        else:
            return "faq" if faq_score >= scheduling_score else "scheduling"
    
    def extract_booking_info(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Extract booking information from user message and conversation history.
        Enhanced to remember user details throughout conversation.
        
        Returns:
            Dictionary with extracted information (date, time, doctor_name, patient_name, patient_email, patient_phone, appointment_type, reason)
        """
        info = {
            "date": None,
            "time": None,
            "doctor_name": None,
            "patient_name": None,
            "patient_email": None,
            "patient_phone": None,
            "appointment_type": None,
            "reason": None
        }
        
        # Combine current message with ALL conversation history for better context
        full_context = user_message
        if conversation_history:
            # Look through entire conversation history for user details
            all_messages = " ".join([msg.get("content", "") for msg in conversation_history])
            full_context = all_messages + " " + user_message
        
        # Extract date patterns (YYYY-MM-DD, MM/DD/YYYY, "tomorrow", "next week", etc.)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',   # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        for pattern in date_patterns:
            match = re.search(pattern, full_context)
            if match:
                info["date"] = match.group()
                break
        
        # Extract time patterns (HH:MM, "9am", "2pm", etc.)
        time_patterns = [
            r'\d{1,2}:\d{2}',       # HH:MM
            r'\d{1,2}\s*(am|pm)',   # 9am, 2pm
        ]
        for pattern in time_patterns:
            match = re.search(pattern, full_context, re.IGNORECASE)
            if match:
                info["time"] = match.group()
                break
        
        # Extract doctor name (look for "Dr." pattern)
        doctor_pattern = r'Dr\.\s+[\w\s]+'
        match = re.search(doctor_pattern, full_context, re.IGNORECASE)
        if match:
            info["doctor_name"] = match.group()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, full_context)
        if match:
            info["patient_email"] = match.group()
        
        # Extract phone number (improved patterns including international)
        phone_patterns = [
            r'\+?91[-.\s]?\d{10}',  # Indian format +91 9897761393
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Simple format
            r'\d{10}',  # 10 digits
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, full_context)
            if match:
                info["patient_phone"] = match.group().strip()
                break
        
        # Extract patient name (look for patterns like "My name is", "I'm", "name: John")
        name_patterns = [
            r'(?:my name is|i\'m|i am|name is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last format
        ]
        for pattern in name_patterns:
            match = re.search(pattern, full_context, re.IGNORECASE)
            if match and not info.get("patient_name"):
                # Check if it's not a doctor name
                potential_name = match.group(1) if match.groups() else match.group(0)
                if "dr." not in potential_name.lower() and "doctor" not in potential_name.lower():
                    info["patient_name"] = potential_name
                    break
        
        # Extract appointment type keywords (improved - handle mid-flow changes)
        context_lower = full_context.lower()
        
        # Check for explicit type changes ("actually", "make it", "change to")
        if any(kw in context_lower for kw in ["actually", "make it", "change to", "switch to", "instead"]):
            # Look for new type after change indicator
            change_idx = max(
                context_lower.find("actually"),
                context_lower.find("make it"),
                context_lower.find("change to"),
                context_lower.find("switch to"),
                context_lower.find("instead")
            )
            if change_idx >= 0:
                after_change = context_lower[change_idx:]
                if any(kw in after_change for kw in ["follow-up", "followup", "follow up"]):
                    info["appointment_type"] = "follow_up"
                elif any(kw in after_change for kw in ["physical", "physical exam", "exam"]):
                    info["appointment_type"] = "physical_exam"
                elif any(kw in after_change for kw in ["specialist", "specialist consultation"]):
                    info["appointment_type"] = "specialist_consultation"
                elif any(kw in after_change for kw in ["consultation", "checkup", "general"]):
                    info["appointment_type"] = "general_consultation"
        
        # Default type detection
        if not info.get("appointment_type"):
            if any(kw in context_lower for kw in ["follow-up", "followup", "follow up"]):
                info["appointment_type"] = "follow_up"
            elif any(kw in context_lower for kw in ["physical", "physical exam", "exam"]):
                info["appointment_type"] = "physical_exam"
            elif any(kw in context_lower for kw in ["specialist", "specialist consultation"]):
                info["appointment_type"] = "specialist_consultation"
            elif any(kw in context_lower for kw in ["consultation", "checkup", "check-up", "routine", "appointment"]):
                info["appointment_type"] = "general_consultation"
        
        # Extract reason keywords (enhanced)
        reason_keywords = {
            "headache": "headache",
            "pain": "pain",
            "checkup": "routine checkup",
            "exam": "physical examination",
            "symptoms": "symptoms",
            "follow-up": "follow-up visit",
            "routine": "routine checkup",
        }
        for keyword, reason_text in reason_keywords.items():
            if keyword in context_lower:
                info["reason"] = reason_text
                break
        
        return info
    
    def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict] = None
    ) -> Tuple[str, str, bool]:
        """
        Process user message and generate response.
        
        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            Tuple of (response, intent, requires_confirmation)
        """
        if conversation_history is None:
            conversation_history = []
        
        # Detect intent
        intent = self.detect_intent(user_message, conversation_history)
        
        if intent == "faq":
            # Answer FAQ using RAG
            response = answer_faq_with_rag(user_message, conversation_history)
            return response, "faq", False
        
        else:
            # Handle scheduling
            return self._handle_scheduling(user_message, conversation_history)
    
    def _handle_scheduling(
        self,
        user_message: str,
        conversation_history: List[Dict] = None
    ) -> Tuple[str, str, bool]:
        """
        Handle scheduling-related conversation.
        
        Returns:
            Tuple of (response, intent, requires_confirmation)
        """
        # Extract booking info
        booking_info = self.extract_booking_info(user_message, conversation_history)
        
        # Check if user is trying to confirm a booking
        confirmation_keywords = ["yes", "confirm", "book it", "that works", "sounds good"]
        is_confirmation = any(keyword in user_message.lower() for keyword in confirmation_keywords)
        
        # Enhanced confirmation flow with explicit prompts
        if is_confirmation and booking_info.get("date") and booking_info.get("time"):
            # Try to extract patient info from conversation
            patient_name = booking_info.get("patient_name")
            patient_email = booking_info.get("patient_email")
            patient_phone = booking_info.get("patient_phone")
            
            # If missing, ask explicitly for each missing field
            if not patient_name or not patient_email or not patient_phone:
                missing = []
                if not patient_name:
                    missing.append("your full name")
                if not patient_email:
                    missing.append("your email address")
                if not patient_phone:
                    missing.append("your phone number")
                
                return (
                    f"Before I can finalize your booking, I need to collect some information. Please provide {', '.join(missing)}.",
                    "scheduling",
                    False
                )
            
            # Explicit confirmation prompt with all details
            date_str = booking_info.get("date")
            time_str = booking_info.get("time")
            appointment_type = booking_info.get("appointment_type", "general consultation")
            
            confirmation_text = (
                f"Perfect! Before I confirm your booking, let me summarize the details:\n\n"
                f"• **Date**: {date_str}\n"
                f"• **Time**: {time_str}\n"
                f"• **Type**: {appointment_type.replace('_', ' ').title()}\n"
                f"• **Name**: {patient_name}\n"
                f"• **Email**: {patient_email}\n"
                f"• **Phone**: {patient_phone}\n\n"
                f"Please confirm if all details are correct, and I'll proceed with the booking."
            )
            
            return (confirmation_text, "scheduling", True)
            
            # Proceed with booking
            try:
                # Format date and time
                date = booking_info["date"]
                time_str = booking_info["time"]
                
                # Convert time format if needed (e.g., "9am" -> "09:00")
                if ":" not in time_str:
                    # Simple conversion for "9am" format
                    time_str = self._normalize_time(time_str)
                
                # Determine appointment type
                appointment_type_str = booking_info.get("appointment_type") or "general_consultation"
                try:
                    appointment_type = AppointmentType(appointment_type_str)
                except ValueError:
                    appointment_type = AppointmentType.GENERAL_CONSULTATION
                
                booking_request = BookingRequest(
                    patient_name=patient_name,
                    patient_email=patient_email,
                    patient_phone=booking_info.get("patient_phone"),
                    date=date,
                    start_time=time_str,
                    doctor_name=booking_info.get("doctor_name", "Dr. Sarah Johnson"),  # Default doctor
                    appointment_type=appointment_type,
                    reason=booking_info.get("reason")
                )
                
                booking_response = book_appointment(booking_request)
                
                if booking_response.success:
                    return (
                        booking_response.message,
                        "scheduling",
                        False
                    )
                else:
                    return (
                        booking_response.message + " Would you like to try a different time?",
                        "scheduling",
                        False
                    )
            except Exception as e:
                return (
                    f"I encountered an error while booking your appointment: {str(e)}. Please try again.",
                    "scheduling",
                    False
                )
        
        # Check for rescheduling/cancellation intent
        user_lower = user_message.lower()
        if any(kw in user_lower for kw in ["reschedule", "change appointment", "move appointment"]):
            return (
                "I can help you reschedule your appointment. Please provide your appointment ID and your preferred new date and time.",
                "scheduling",
                False
            )
        elif any(kw in user_lower for kw in ["cancel", "cancel appointment"]):
            return (
                "I can help you cancel your appointment. Please provide your appointment ID and your email address for verification.",
                "scheduling",
                False
            )
        
        # Check availability and suggest slots
        date = booking_info.get("date")
        doctor_name = booking_info.get("doctor_name")
        appointment_type_str = booking_info.get("appointment_type")
        
        # Determine appointment type
        appointment_type = None
        if appointment_type_str:
            try:
                appointment_type = AppointmentType(appointment_type_str)
            except ValueError:
                pass
        
        if not date:
            # Check if user is asking to see options (might have mentioned date earlier or want default)
            user_lower = user_message.lower()
            if any(kw in user_lower for kw in ["show", "options", "available", "slots", "times"]):
                # Try to find date from conversation history
                date_from_history = None
                if conversation_history:
                    # Look for dates in recent conversation
                    for msg in reversed(conversation_history[-5:]):
                        msg_content = msg.get("content", "").lower()
                        # Look for date patterns
                        import re
                        date_patterns = [
                            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                            r'\d{2}/\d{2}/\d{4}',   # MM/DD/YYYY
                            r'january|february|march|april|may|june|july|august|september|october|november|december',
                            r'tomorrow|today|next week|this week'
                        ]
                        for pattern in date_patterns:
                            if re.search(pattern, msg_content):
                                # Extract the date or use a default
                                if "tomorrow" in msg_content:
                                    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                                    date_from_history = tomorrow
                                elif "today" in msg_content:
                                    today = datetime.now().strftime("%Y-%m-%d")
                                    date_from_history = today
                                break
                        if date_from_history:
                            date = date_from_history
                            break
                
                # If no date found in history but user wants to see options, use tomorrow as default
                if not date:
                    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    date = tomorrow
            
            if not date:
                # Ask for date preference - use fallback if API unavailable
                try:
                    response = self._generate_response_with_llm(
                        user_message,
                        conversation_history,
                        available_slots=None
                    )
                except Exception:
                    # Fallback response when no date provided
                    response = "I'd be happy to help you find available appointments! Please let me know what date you prefer (e.g., 'January 15th' or 'tomorrow'), and I'll show you the available time slots."
                return response, "scheduling", False
        
        # Get available slots (limited to 3-5)
        slots = get_available_slots(date, doctor_name, appointment_type, max_slots=5)
        
        if not slots:
            # Offer waitlist
            waitlist_offer = "Would you like me to add you to our waitlist for this date? We'll notify you if a slot becomes available."
            return (
                f"I couldn't find any available slots for {date}. Would you like to try a different date? {waitlist_offer}",
                "scheduling",
                False
            )
        
        # Format slots for display (limit to 3-5, already done but ensure)
        slots_text = format_slots_for_display(slots[:5], appointment_type)
        
        # Generate response using LLM
        response = self._generate_response_with_llm(
            user_message,
            conversation_history,
            available_slots=slots_text
        )
        
        requires_confirmation = any(keyword in response.lower() for keyword in ["confirm", "book", "proceed"])
        
        return response, "scheduling", requires_confirmation
    
    def _generate_response_with_llm(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        available_slots: str = None
    ) -> str:
        """Generate response using Gemini."""
        user_prompt = format_user_prompt_with_context(
            user_message,
            conversation_history,
            available_slots
        )
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            model = get_model()
            
            # Convert messages format for Gemini
            # Gemini uses a different format - we'll combine system and user messages
            conversation_text = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    conversation_text += f"System: {content}\n\n"
                elif role == "user":
                    conversation_text += f"User: {content}\n\n"
                elif role == "assistant":
                    conversation_text += f"Assistant: {content}\n\n"
            
            # Generate response with Gemini
            response = model.generate_content(
                conversation_text,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
            )
            
            # Handle response - use parts accessor instead of text quick accessor
            # The text quick accessor only works for simple single-Part responses
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check for safety ratings (blocked content)
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason in ['SAFETY', 'RECITATION']:
                    # Safety filter blocked the response - use fallback
                    print(f"Warning: Gemini safety filter blocked response (reason: {candidate.finish_reason})")
                    raise Exception("Content was blocked by safety filters")
                
                # Extract text from parts (recommended way)
                if hasattr(candidate, 'content'):
                    content = candidate.content
                    # Check if content has parts attribute
                    if hasattr(content, 'parts'):
                        # Check if parts exist and is not empty
                        try:
                            # Try direct iteration (works with RepeatedComposite)
                            text_parts = []
                            for part in content.parts:
                                # Check if part has text attribute and it's not None/empty
                                if hasattr(part, 'text'):
                                    text_value = getattr(part, 'text', None)
                                    if text_value:
                                        text_parts.append(str(text_value))
                            if text_parts:
                                return ' '.join(text_parts).strip()
                        except Exception as parts_error:
                            print(f"Debug: Error iterating parts: {parts_error}")
                            # Try list conversion as fallback
                            try:
                                parts_list = list(content.parts)
                                if parts_list:
                                    text_parts = []
                                    for part in parts_list:
                                        if hasattr(part, 'text'):
                                            text_value = getattr(part, 'text', None)
                                            if text_value:
                                                text_parts.append(str(text_value))
                                    if text_parts:
                                        return ' '.join(text_parts).strip()
                            except Exception as list_error:
                                print(f"Debug: Error with list conversion: {list_error}")
                    
                    # Alternative: try direct text access on content
                    if hasattr(content, 'text'):
                        text_value = getattr(content, 'text', None)
                        if text_value:
                            return str(text_value).strip()
            
            # Try the text quick accessor as fallback (may fail for complex responses)
            try:
                if hasattr(response, 'text') and response.text:
                    return response.text.strip()
            except ValueError:
                # text quick accessor failed, continue to check other methods
                pass
            
            # If no text found, check prompt_feedback for issues
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, 'block_reason') and feedback.block_reason:
                    print(f"Warning: Prompt blocked (reason: {feedback.block_reason})")
                    raise Exception(f"Prompt was blocked: {feedback.block_reason}")
            
            # If no text found, use fallback
            print(f"Warning: Gemini API response structure: {type(response)}, candidates: {len(response.candidates) if hasattr(response, 'candidates') else 0}")
            raise Exception("Gemini API returned response without text content")
        except Exception as e:
            error_msg = str(e)
            # Check for quota/rate limit errors (Gemini-specific)
            if any(keyword in error_msg.lower() for keyword in ["quota", "rate limit", "429", "resource_exhausted", "permission_denied"]):
                # Fallback to rule-based response when API quota exceeded
                return self._fallback_response(user_message, conversation_history, available_slots)
            # Log other errors but still use fallback
            print(f"Gemini API Error: {type(e).__name__}: {error_msg}")
            import traceback
            traceback.print_exc()  # Print full traceback for debugging
            return self._fallback_response(user_message, conversation_history, available_slots)
    
    def _fallback_response(self, user_message: str, conversation_history: List[Dict] = None, available_slots: str = None) -> str:
        """Fallback response when Gemini API is unavailable."""
        message_lower = user_message.lower()
        
        # Handle "show options" or "show me options" requests
        if any(kw in message_lower for kw in ["show", "options", "available", "slots", "times"]) and available_slots:
            return f"I'd be happy to help you book an appointment! Here are the available slots:\n{available_slots}\n\nPlease let me know which date and time works for you, and I'll need your name, phone number, and email to complete the booking."
        
        # Handle scheduling requests
        if any(kw in message_lower for kw in ["book", "appointment", "schedule", "see doctor"]):
            if available_slots:
                return f"I'd be happy to help you book an appointment! Here are available slots:\n{available_slots}\n\nPlease let me know which date and time works for you, and I'll need your name, phone number, and email to complete the booking."
            else:
                return "I'd be happy to help you book an appointment! What date would you prefer? I'll check availability and show you options."
        
        # Handle FAQ requests
        if any(kw in message_lower for kw in ["hours", "open", "closed", "when"]):
            return "Our clinic hours are Monday through Friday from 9:00 AM to 5:00 PM, and Saturday from 10:00 AM to 2:00 PM. We are closed on Sundays. For more details, please call us at +91 9897761393."
        
        if any(kw in message_lower for kw in ["insurance", "accept"]):
            return "Yes, we accept most major insurance plans including Blue Cross Blue Shield, Aetna, Cigna, and UnitedHealthcare. Please bring your insurance card to your appointment. For more information, call us at +91 9897761393."
        
        # Default response
        return "I'm here to help you with appointment scheduling or answer questions about our clinic. How can I assist you today? You can also call us directly at +91 9897761393."
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time string to HH:MM format."""
        time_str = time_str.lower().strip()
        
        # Handle "9am", "2pm" format
        if "am" in time_str or "pm" in time_str:
            time_num = re.search(r'\d+', time_str)
            if time_num:
                hour = int(time_num.group())
                if "pm" in time_str and hour < 12:
                    hour += 12
                if "am" in time_str and hour == 12:
                    hour = 0
                return f"{hour:02d}:00"
        
        # Already in HH:MM format
        if ":" in time_str:
            return time_str
        
        return "09:00"  # Default

