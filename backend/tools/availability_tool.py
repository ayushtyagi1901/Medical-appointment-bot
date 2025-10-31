import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
import pytz

from ..models.schemas import TimeSlot, AppointmentType, APPOINTMENT_DURATIONS


def load_schedule_data() -> Dict:
    """Load doctor schedule data from JSON file."""
    data_path = os.getenv("SCHEDULE_DATA_PATH", "./data/doctor_schedule.json")
    
    # Resolve path relative to project root
    if not os.path.isabs(data_path):
        # Try relative to current directory first
        if os.path.exists(data_path):
            resolved_path = data_path
        else:
            # Try relative to backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            resolved_path = os.path.join(os.path.dirname(backend_dir), data_path.lstrip('./'))
            if not os.path.exists(resolved_path):
                # Try relative to project root
                project_root = os.path.dirname(backend_dir)
                resolved_path = os.path.join(project_root, data_path.lstrip('./'))
    else:
        resolved_path = data_path
    
    with open(resolved_path, 'r') as f:
        return json.load(f)


def get_timezone():
    """Get timezone from environment or default to India (Asia/Kolkata)."""
    tz_str = os.getenv("TIMEZONE", "Asia/Kolkata")
    try:
        return pytz.timezone(tz_str)
    except:
        return pytz.timezone("Asia/Kolkata")  # Default to India timezone


def calculate_end_time(start_time: str, duration_minutes: int) -> str:
    """Calculate end time given start time and duration."""
    start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    return end_dt.strftime("%Y-%m-%dT%H:%M:%S")


def slot_matches_duration(slot: dict, required_duration: int, buffer_minutes: int = 0) -> bool:
    """
    Check if a slot has enough time for the required duration.
    
    Note: Buffer time is handled separately when checking adjacent slots,
    not by requiring the slot itself to be longer.
    """
    start = datetime.strptime(slot['start'], "%H:%M")
    end = datetime.strptime(slot['end'], "%H:%M")
    slot_duration = (end - start).total_seconds() / 60  # Convert to minutes
    # Slot just needs to fit the appointment duration (buffer is handled separately)
    return slot_duration >= required_duration


def get_available_slots(
    date: str,
    doctor_name: Optional[str] = None,
    appointment_type: Optional[AppointmentType] = None,
    max_slots: int = 5,
    buffer_minutes: int = 15
) -> List[TimeSlot]:
    """
    Get available appointment slots for a given date.
    
    Args:
        date: Date in YYYY-MM-DD format
        doctor_name: Optional specific doctor name
        appointment_type: Optional appointment type for duration matching
        max_slots: Maximum number of slots to return (default 5, for 3-5 range)
        buffer_minutes: Buffer time to consider for travel/preparation (default 15 minutes)
        
    Returns:
        List of available TimeSlot objects (limited to max_slots)
    """
    schedule_data = load_schedule_data()
    available_slots = []
    
    # Validate date format
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        # Check if date is in the past
        if parsed_date.date() < datetime.now().date():
            return []
    except ValueError:
        return []
    
    # Get required duration if appointment type is specified
    required_duration = None
    if appointment_type:
        required_duration = APPOINTMENT_DURATIONS.get(appointment_type, 30)
    
    for doctor in schedule_data.get("doctors", []):
        # Filter by doctor name if specified
        if doctor_name and doctor_name.lower() not in doctor["name"].lower():
            continue
        
        # Find slots for the requested date
        for day_schedule in doctor.get("available_slots", []):
            if day_schedule["date"] == date:
                for slot in day_schedule.get("time_slots", []):
                    if not slot.get("available", False):
                        continue
                    
                    # Check if slot matches duration requirement
                    if required_duration and not slot_matches_duration(slot, required_duration, buffer_minutes):
                        continue
                    
                    # Calculate actual end time based on appointment type if specified
                    if appointment_type and required_duration:
                        end_time_str = calculate_end_time(
                            f"{date}T{slot['start']}:00",
                            required_duration
                        )
                    else:
                        end_time_str = f"{date}T{slot['end']}:00"
                    
                    time_slot = TimeSlot(
                        start_time=f"{date}T{slot['start']}:00",
                        end_time=end_time_str,
                        doctor_name=doctor["name"],
                        available=True
                    )
                    available_slots.append(time_slot)
                    
                    # Limit to max_slots (default 5, but can show 3-5)
                    if len(available_slots) >= max_slots:
                        break
            
            if len(available_slots) >= max_slots:
                break
        
        if len(available_slots) >= max_slots:
            break
    
    # Return top max_slots, prioritizing earlier times
    return sorted(available_slots, key=lambda x: x.start_time)[:max_slots]


def get_all_available_slots(start_date: str, end_date: Optional[str] = None, doctor_name: Optional[str] = None) -> Dict[str, List[TimeSlot]]:
    """
    Get all available slots for a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to 7 days from start_date)
        doctor_name: Optional specific doctor name
        
    Returns:
        Dictionary mapping dates to lists of TimeSlot objects
    """
    schedule_data = load_schedule_data()
    results = {}
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end = start + timedelta(days=7)
    
    # Iterate through date range
    current_date = start
    while current_date <= end:
        date_str = current_date.strftime("%Y-%m-%d")
        slots = get_available_slots(date_str, doctor_name)
        if slots:
            results[date_str] = slots
        current_date += timedelta(days=1)
    
    return results


def format_slots_for_display(slots: List[TimeSlot], appointment_type: Optional[AppointmentType] = None) -> str:
    """
    Format slots as a readable string for LLM.
    
    Args:
        slots: List of TimeSlot objects
        appointment_type: Optional appointment type for display
        
    Returns:
        Formatted string
    """
    if not slots:
        return "No available slots found for the requested date."
    
    # Get duration info if appointment type is specified
    duration_info = ""
    if appointment_type:
        duration = APPOINTMENT_DURATIONS.get(appointment_type, 30)
        type_name = appointment_type.value.replace("_", " ").title()
        duration_info = f" ({type_name}, {duration} minutes)"
    
    # Group by doctor
    by_doctor = {}
    for slot in slots:
        if slot.doctor_name not in by_doctor:
            by_doctor[slot.doctor_name] = []
        by_doctor[slot.doctor_name].append(slot)
    
    formatted = []
    for doctor, doctor_slots in by_doctor.items():
        formatted.append(f"\n{doctor}:")
        for slot in doctor_slots:
            start_time = slot.start_time.split('T')[1][:5]  # Extract HH:MM
            end_time = slot.end_time.split('T')[1][:5] if 'T' in slot.end_time else slot.end_time.split('T')[1][:5]
            formatted.append(f"  - {start_time} to {end_time}{duration_info}")
    
    return "\n".join(formatted)

