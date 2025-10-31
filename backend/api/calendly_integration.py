from fastapi import APIRouter, HTTPException
from typing import Optional

from ..models.schemas import (
    AvailabilityRequest, AvailabilityResponse,
    BookingRequest, BookingResponse,
    RescheduleRequest, RescheduleResponse,
    CancelRequest, CancelResponse,
    WaitlistRequest, WaitlistResponse,
    AppointmentType
)
from ..tools.availability_tool import get_available_slots
from ..tools.booking_tool import (
    book_appointment, reschedule_appointment,
    cancel_appointment, add_to_waitlist
)

router = APIRouter()


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    date: str,
    doctor_name: Optional[str] = None,
    appointment_type: Optional[str] = None
):
    """
    Mock Calendly API endpoint to get available appointment slots.
    
    Query Parameters:
        date: Date in YYYY-MM-DD format
        doctor_name: Optional doctor name filter
        appointment_type: Optional appointment type (general_consultation, follow_up, physical_exam, specialist_consultation)
    """
    try:
        apt_type = None
        if appointment_type:
            try:
                apt_type = AppointmentType(appointment_type)
            except ValueError:
                pass
        
        slots = get_available_slots(date, doctor_name, apt_type, max_slots=5)
        
        return AvailabilityResponse(
            date=date,
            slots=slots
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching availability: {str(e)}")


@router.post("/book", response_model=BookingResponse)
async def book_appointment_endpoint(booking_request: BookingRequest):
    """
    Mock Calendly API endpoint to book an appointment.
    """
    try:
        booking_response = book_appointment(booking_request)
        return booking_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error booking appointment: {str(e)}")


@router.post("/reschedule", response_model=RescheduleResponse)
async def reschedule_appointment_endpoint(reschedule_request: RescheduleRequest):
    """
    Reschedule an existing appointment.
    """
    try:
        response = reschedule_appointment(reschedule_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rescheduling appointment: {str(e)}")


@router.post("/cancel", response_model=CancelResponse)
async def cancel_appointment_endpoint(cancel_request: CancelRequest):
    """
    Cancel an existing appointment.
    """
    try:
        response = cancel_appointment(cancel_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling appointment: {str(e)}")


@router.post("/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist_endpoint(waitlist_request: WaitlistRequest):
    """
    Add a patient to the waitlist.
    """
    try:
        response = add_to_waitlist(waitlist_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to waitlist: {str(e)}")

