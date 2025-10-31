from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class AppointmentType(str, Enum):
    """Appointment types with their durations."""
    GENERAL_CONSULTATION = "general_consultation"  # 30 minutes
    FOLLOW_UP = "follow_up"  # 15 minutes
    PHYSICAL_EXAM = "physical_exam"  # 45 minutes
    SPECIALIST_CONSULTATION = "specialist_consultation"  # 60 minutes


APPOINTMENT_DURATIONS = {
    AppointmentType.GENERAL_CONSULTATION: 30,
    AppointmentType.FOLLOW_UP: 15,
    AppointmentType.PHYSICAL_EXAM: 45,
    AppointmentType.SPECIALIST_CONSULTATION: 60,
}


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[], description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant response")
    intent: str = Field(..., description="Detected intent: 'scheduling' or 'faq'")
    requires_confirmation: bool = Field(
        default=False, description="Whether response requires user confirmation"
    )


class TimeSlot(BaseModel):
    start_time: str = Field(..., description="ISO format start time")
    end_time: str = Field(..., description="ISO format end time")
    doctor_name: str = Field(..., description="Doctor name")
    available: bool = Field(default=True, description="Slot availability")


class AvailabilityRequest(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    doctor_name: Optional[str] = Field(default=None, description="Specific doctor name")
    appointment_type: Optional[AppointmentType] = Field(default=None, description="Appointment type for duration matching")


class AvailabilityResponse(BaseModel):
    date: str = Field(..., description="Requested date")
    slots: List[TimeSlot] = Field(..., description="Available time slots")


class BookingRequest(BaseModel):
    patient_name: str = Field(..., description="Patient name")
    patient_email: str = Field(..., description="Patient email")
    patient_phone: str = Field(..., description="Patient phone number")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    doctor_name: str = Field(..., description="Doctor name")
    appointment_type: AppointmentType = Field(default=AppointmentType.GENERAL_CONSULTATION, description="Appointment type")
    reason: Optional[str] = Field(default=None, description="Reason for visit")


class BookingResponse(BaseModel):
    success: bool = Field(..., description="Booking status")
    appointment_id: Optional[str] = Field(default=None, description="Appointment ID")
    message: str = Field(..., description="Booking confirmation message")
    appointment_details: Optional[dict] = Field(
        default=None, description="Appointment details"
    )


class RescheduleRequest(BaseModel):
    appointment_id: str = Field(..., description="Appointment ID to reschedule")
    new_date: str = Field(..., description="New date in YYYY-MM-DD format")
    new_start_time: str = Field(..., description="New start time in HH:MM format")


class RescheduleResponse(BaseModel):
    success: bool = Field(..., description="Rescheduling status")
    appointment_id: str = Field(..., description="Appointment ID")
    message: str = Field(..., description="Rescheduling message")
    old_appointment: Optional[dict] = Field(default=None, description="Old appointment details")
    new_appointment: Optional[dict] = Field(default=None, description="New appointment details")


class CancelRequest(BaseModel):
    appointment_id: str = Field(..., description="Appointment ID to cancel")
    patient_email: Optional[str] = Field(default=None, description="Patient email for verification")


class CancelResponse(BaseModel):
    success: bool = Field(..., description="Cancellation status")
    appointment_id: str = Field(..., description="Appointment ID")
    message: str = Field(..., description="Cancellation message")
    cancelled_appointment: Optional[dict] = Field(default=None, description="Cancelled appointment details")


class WaitlistRequest(BaseModel):
    patient_name: str = Field(..., description="Patient name")
    patient_email: str = Field(..., description="Patient email")
    patient_phone: str = Field(..., description="Patient phone number")
    preferred_date: str = Field(..., description="Preferred date in YYYY-MM-DD format")
    appointment_type: AppointmentType = Field(default=AppointmentType.GENERAL_CONSULTATION, description="Appointment type")
    doctor_name: Optional[str] = Field(default=None, description="Preferred doctor name")


class WaitlistResponse(BaseModel):
    success: bool = Field(..., description="Waitlist status")
    waitlist_id: str = Field(..., description="Waitlist entry ID")
    message: str = Field(..., description="Waitlist confirmation message")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")

