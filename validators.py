import logging
from datetime import datetime
from typing import Optional

_logger = logging.getLogger(__name__)

# TODO add validation against past dates for time and date

async def validate_date(date: str) -> Optional[datetime]:
    try:
        chosen_date = datetime.strptime(date, "%d.%m")
    except ValueError:
        _logger.debug(f"Failed to parse date: {date}")
        return None
    return chosen_date

async def validate_time(time: str) -> Optional[datetime]:
    try:
        chosen_time = datetime.strptime(time, "%H:%M")
    except ValueError:
        _logger.debug(f"Failed to parse time: {time}")
        return None
    return chosen_time

async def validate_seats(seats: str) -> Optional[int]:
    if not seats.isdigit():
        _logger.debug(f"Seats should be digit. Got: {seats}")
        return None
    return int(seats)