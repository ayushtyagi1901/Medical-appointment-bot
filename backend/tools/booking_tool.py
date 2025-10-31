import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

from ..models.schemas import (
    BookingRequest, BookingResponse, TimeSlot,
    RescheduleRequest, RescheduleResponse,
    CancelRequest, CancelResponse,
    WaitlistRequest, WaitlistResponse,
    AppointmentType, APPOINTMENT_DURATIONS
)
from .availability_tool import get_available_slots, load_schedule_data, calculate_end_time


# In-memory storage for booked appointments (in production, this would be a database)
_booked_appointments: Dict[str, Dict] = {}
_waitlist_entries: Dict[str, Dict] = {}


def book_appointment(booking_request: BookingRequest) -> BookingResponse:
    """
    Book an appointment using the mock Calendly API.
    
    Args:
        booking_request: BookingRequest with patient and appointment details
        
    Returns:
        BookingResponse with booking status and details
    """
    # Validate booking request
    try:
        # Validate date format
        datetime.strptime(booking_request.date, "%Y-%m-%d")
        # Validate time format
        datetime.strptime(booking_request.start_time, "%H:%M")
    except ValueError as e:
        return BookingResponse(
            success=False,
            message=f"Invalid date or time format: {str(e)}"
        )
    
    # Check if slot is still available
    available_slots = get_available_slots(
        booking_request.date,
        booking_request.doctor_name,
        booking_request.appointment_type
    )
    
    # Find matching slot
    matching_slot = None
    for slot in available_slots:
        slot_time = slot.start_time.split('T')[1][:5]  # Extract HH:MM
        if slot_time == booking_request.start_time and slot.doctor_name == booking_request.doctor_name:
            matching_slot = slot
            break
    
    if not matching_slot:
        return BookingResponse(
            success=False,
            message=f"The requested slot is no longer available. Please choose a different time."
        )
    
    # Check if already booked (simple check)
    appointment_key = f"{booking_request.date}_{booking_request.start_time}_{booking_request.doctor_name}"
    if appointment_key in _booked_appointments:
        return BookingResponse(
            success=False,
            message="This appointment slot has already been booked. Please select another time."
        )
    
    # Calculate end time based on appointment type
    duration = APPOINTMENT_DURATIONS.get(booking_request.appointment_type, 30)
    end_time_str = calculate_end_time(
        f"{booking_request.date}T{booking_request.start_time}:00",
        duration
    )
    end_time = end_time_str.split('T')[1][:5]
    
    # Create appointment
    appointment_id = str(uuid.uuid4())
    appointment = {
        "appointment_id": appointment_id,
        "patient_name": booking_request.patient_name,
        "patient_email": booking_request.patient_email,
        "patient_phone": booking_request.patient_phone,
        "doctor_name": booking_request.doctor_name,
        "date": booking_request.date,
        "start_time": booking_request.start_time,
        "end_time": end_time,
        "appointment_type": booking_request.appointment_type.value,
        "duration_minutes": duration,
        "reason": booking_request.reason,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    # Store appointment
    _booked_appointments[appointment_key] = appointment
    
    # Update schedule data to mark slot as booked
    _mark_slot_as_booked(
        booking_request.date,
        booking_request.start_time,
        booking_request.doctor_name
    )
    
    return BookingResponse(
        success=True,
        appointment_id=appointment_id,
        message=f"Appointment successfully booked! Your appointment ID is {appointment_id}.",
        appointment_details=appointment
    )


def _mark_slot_as_booked(date: str, start_time: str, doctor_name: str):
    """
    Mark a slot as booked in the schedule data.
    Note: In a real system, this would update a database.
    """
    # This is a simple in-memory update
    # In production, you would update a database
    schedule_data = load_schedule_data()
    
    for doctor in schedule_data.get("doctors", []):
        if doctor["name"] == doctor_name:
            for day_schedule in doctor.get("available_slots", []):
                if day_schedule["date"] == date:
                    for slot in day_schedule.get("time_slots", []):
                        if slot["start"] == start_time:
                            slot["available"] = False
                            break
                    break
            break


def get_appointment(appointment_id: str) -> Optional[Dict]:
    """Get appointment details by ID."""
    for appointment in _booked_appointments.values():
        if appointment.get("appointment_id") == appointment_id:
            return appointment
    return None


def get_all_appointments() -> Dict[str, Dict]:
    """Get all booked appointments (for testing/admin purposes)."""
    return _booked_appointments.copy()


def reschedule_appointment(reschedule_request: RescheduleRequest) -> RescheduleResponse:
    """
    Reschedule an existing appointment.
    
    Args:
        reschedule_request: RescheduleRequest with appointment ID and new time
        
    Returns:
        RescheduleResponse with rescheduling status and details
    """
    # Find the existing appointment
    old_appointment = None
    appointment_key = None
    
    for key, appointment in _booked_appointments.items():
        if appointment.get("appointment_id") == reschedule_request.appointment_id:
            old_appointment = appointment.copy()
            appointment_key = key
            break
    
    if not old_appointment:
        return RescheduleResponse(
            success=False,
            appointment_id=reschedule_request.appointment_id,
            message="Appointment not found. Please check your appointment ID."
        )
    
    # Validate new date and time
    try:
        datetime.strptime(reschedule_request.new_date, "%Y-%m-%d")
        datetime.strptime(reschedule_request.new_start_time, "%H:%M")
        
        # Check if new date is in the past
        new_date = datetime.strptime(reschedule_request.new_date, "%Y-%m-%d")
        if new_date.date() < datetime.now().date():
            return RescheduleResponse(
                success=False,
                appointment_id=reschedule_request.appointment_id,
                message="Cannot reschedule to a past date."
            )
    except ValueError as e:
        return RescheduleResponse(
            success=False,
            appointment_id=reschedule_request.appointment_id,
            message=f"Invalid date or time format: {str(e)}"
        )
    
    # Check if new slot is available
    appointment_type = AppointmentType(old_appointment.get("appointment_type", "general_consultation"))
    available_slots = get_available_slots(
        reschedule_request.new_date,
        old_appointment.get("doctor_name"),
        appointment_type
    )
    
    # Find matching slot
    matching_slot = None
    for slot in available_slots:
        slot_time = slot.start_time.split('T')[1][:5]
        if slot_time == reschedule_request.new_start_time:
            matching_slot = slot
            break
    
    if not matching_slot:
        return RescheduleResponse(
            success=False,
            appointment_id=reschedule_request.appointment_id,
            message=f"The requested slot is not available. Please choose a different time."
        )
    
    # Check if new slot is already booked
    new_appointment_key = f"{reschedule_request.new_date}_{reschedule_request.new_start_time}_{old_appointment.get('doctor_name')}"
    if new_appointment_key in _booked_appointments and new_appointment_key != appointment_key:
        return RescheduleResponse(
            success=False,
            appointment_id=reschedule_request.appointment_id,
            message="This appointment slot has already been booked. Please select another time."
        )
    
    # Free up the old slot
    old_date = old_appointment.get("date")
    old_time = old_appointment.get("start_time")
    _mark_slot_as_available(old_date, old_time, old_appointment.get("doctor_name"))
    
    # Create new appointment details
    duration = APPOINTMENT_DURATIONS.get(appointment_type, 30)
    end_time_str = calculate_end_time(
        f"{reschedule_request.new_date}T{reschedule_request.new_start_time}:00",
        duration
    )
    end_time = end_time_str.split('T')[1][:5]
    
    new_appointment = {
        **old_appointment,
        "date": reschedule_request.new_date,
        "start_time": reschedule_request.new_start_time,
        "end_time": end_time,
        "rescheduled_at": datetime.now().isoformat(),
        "previous_date": old_date,
        "previous_time": old_time
    }
    
    # Update appointments storage
    if appointment_key != new_appointment_key:
        del _booked_appointments[appointment_key]
    _booked_appointments[new_appointment_key] = new_appointment
    
    # Mark new slot as booked
    _mark_slot_as_booked(
        reschedule_request.new_date,
        reschedule_request.new_start_time,
        old_appointment.get("doctor_name")
    )
    
    return RescheduleResponse(
        success=True,
        appointment_id=reschedule_request.appointment_id,
        message=f"Appointment successfully rescheduled to {reschedule_request.new_date} at {reschedule_request.new_start_time}.",
        old_appointment={
            "date": old_date,
            "start_time": old_time,
            "end_time": old_appointment.get("end_time")
        },
        new_appointment={
            "date": reschedule_request.new_date,
            "start_time": reschedule_request.new_start_time,
            "end_time": end_time
        }
    )


def cancel_appointment(cancel_request: CancelRequest) -> CancelResponse:
    """
    Cancel an existing appointment.
    
    Args:
        cancel_request: CancelRequest with appointment ID
        
    Returns:
        CancelResponse with cancellation status and details
    """
    # Find the appointment
    appointment = None
    appointment_key = None
    
    for key, apt in _booked_appointments.items():
        if apt.get("appointment_id") == cancel_request.appointment_id:
            appointment = apt.copy()
            appointment_key = key
            break
    
    if not appointment:
        return CancelResponse(
            success=False,
            appointment_id=cancel_request.appointment_id,
            message="Appointment not found. Please check your appointment ID."
        )
    
    # Verify email if provided
    if cancel_request.patient_email and appointment.get("patient_email") != cancel_request.patient_email:
        return CancelResponse(
            success=False,
            appointment_id=cancel_request.appointment_id,
            message="Email verification failed. Please provide the correct email address."
        )
    
    # Free up the slot
    _mark_slot_as_available(
        appointment.get("date"),
        appointment.get("start_time"),
        appointment.get("doctor_name")
    )
    
    # Remove appointment
    del _booked_appointments[appointment_key]
    
    return CancelResponse(
        success=True,
        appointment_id=cancel_request.appointment_id,
        message=f"Appointment successfully cancelled. Your slot for {appointment.get('date')} at {appointment.get('start_time')} has been released.",
        cancelled_appointment=appointment
    )


def add_to_waitlist(waitlist_request: WaitlistRequest) -> WaitlistResponse:
    """
    Add a patient to the waitlist for a preferred date.
    
    Args:
        waitlist_request: WaitlistRequest with patient and preference details
        
    Returns:
        WaitlistResponse with waitlist status
    """
    waitlist_id = str(uuid.uuid4())
    waitlist_entry = {
        "waitlist_id": waitlist_id,
        "patient_name": waitlist_request.patient_name,
        "patient_email": waitlist_request.patient_email,
        "patient_phone": waitlist_request.patient_phone,
        "preferred_date": waitlist_request.preferred_date,
        "appointment_type": waitlist_request.appointment_type.value,
        "doctor_name": waitlist_request.doctor_name,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    
    _waitlist_entries[waitlist_id] = waitlist_entry
    
    return WaitlistResponse(
        success=True,
        waitlist_id=waitlist_id,
        message=f"You've been added to our waitlist for {waitlist_request.preferred_date}. We'll notify you at {waitlist_request.patient_email} if a slot becomes available."
    )


def get_waitlist_entries(date: Optional[str] = None, appointment_type: Optional[AppointmentType] = None) -> List[Dict]:
    """Get waitlist entries, optionally filtered by date and appointment type."""
    entries = list(_waitlist_entries.values())
    
    if date:
        entries = [e for e in entries if e.get("preferred_date") == date]
    
    if appointment_type:
        entries = [e for e in entries if e.get("appointment_type") == appointment_type.value]
    
    return entries


def _mark_slot_as_available(date: str, start_time: str, doctor_name: str):
    """Mark a slot as available (for rescheduling/cancellation)."""
    schedule_data = load_schedule_data()
    
    for doctor in schedule_data.get("doctors", []):
        if doctor["name"] == doctor_name:
            for day_schedule in doctor.get("available_slots", []):
                if day_schedule["date"] == date:
                    for slot in day_schedule.get("time_slots", []):
                        if slot["start"] == start_time:
                            slot["available"] = True
                            break
                    break
            break

