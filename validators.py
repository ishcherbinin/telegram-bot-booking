import logging
from datetime import datetime
from typing import Optional

_logger = logging.getLogger(__name__)

async def validate_date(date: str) -> Optional[datetime]:
    try:
        chosen_date = datetime.strptime(date, "%d.%m")
    except ValueError:
        _logger.debug(f"Failed to parse date: {date}")
        return None
    _logger.info(f"Chosen date: {chosen_date}")
    today = datetime.now().date()
    _logger.info(f"Today: {today}")
    if chosen_date.date().day < today.day or chosen_date.date().month < today.month:
        return None
    return chosen_date

async def validate_time(time: str) -> Optional[datetime]:
    try:
        chosen_time = datetime.strptime(time, "%H:%M")
    except ValueError:
        _logger.debug(f"Failed to parse time: {time}")
        return None
    _logger.info(f"Chosen time: {chosen_time}")
    now = datetime.now()
    _logger.info(f"Now: {now}")
    if chosen_time.time().hour < now.time().hour or chosen_time.time().minute < now.time().minute:
        return None
    return chosen_time

async def validate_seats(seats: str) -> Optional[int]:
    if not seats.isdigit():
        _logger.debug(f"Seats should be digit. Got: {seats}")
        return None
    return int(seats)