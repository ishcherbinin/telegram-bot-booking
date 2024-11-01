import logging
from datetime import datetime
from typing import Optional, Tuple

_logger = logging.getLogger(__name__)

# TODO add validation against past dates for time and date

async def validate_date(date: str) -> Tuple[Optional[datetime], str]:
    try:
        chosen_date = datetime.strptime(date, "%d.%m")
    except ValueError:
        _logger.debug(f"Failed to parse date: {date}")
        return None, "Invalid format for date. Please enter a valid date and time in the format DD.MM"
    return chosen_date, ""

async def validate_time(time: str) -> Tuple[Optional[datetime], str]:
    try:
        chosen_time = datetime.strptime(time, "%H:%M")
    except ValueError:
        _logger.debug(f"Failed to parse time: {time}")
        return None, "Invalid format for time. Please enter a valid date and time in the format HH:MM"
    return chosen_time, ""

async def validate_seats(seats: str) -> Optional[int]:
    if not seats.isdigit():
        _logger.debug(f"Seats should be digit. Got: {seats}")
        return None
    return int(seats)