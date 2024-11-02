import logging
from datetime import datetime, date
from typing import Optional, Tuple

_logger = logging.getLogger(__name__)

async def validate_date(target_date: str) -> Tuple[Optional[datetime], str]:
    try:
        current_year = datetime.now().year
        full_date_str = f"{target_date}.{current_year}"
        chosen_date = datetime.strptime(full_date_str, "%d.%m.%Y")
    except ValueError:
        _logger.debug(f"Failed to parse date: {target_date}")
        return None, "Invalid format for date. Please enter a valid date and time in the format DD.MM"
    if chosen_date.date() < datetime.now().date():
        return None, "You can't book a table in the past. Please enter date in the future"
    return chosen_date, ""

async def validate_time(time: str, target_date: date) -> Tuple[Optional[datetime], str]:
    final_time = f"{target_date.strftime('%d.%m.%Y')} {time}"
    try:
        chosen_time = datetime.strptime(final_time, "%d.%m.%Y %H:%M")
    except ValueError:
        _logger.debug(f"Failed to parse time: {time}")
        return None, "Invalid format for time. Please enter a valid date and time in the format HH:MM"
    if chosen_time < datetime.now():
        return None, "You can't book a table in the past. Please enter time in the future"
    return chosen_time, ""

async def validate_seats(seats: str) -> Optional[int]:
    if not seats.isdigit():
        _logger.debug(f"Seats should be digit. Got: {seats}")
        return None
    return int(seats)