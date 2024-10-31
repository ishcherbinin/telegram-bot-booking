from datetime import datetime
from typing import Optional


async def validate_date(date: str) -> Optional[datetime]:
    try:
        chosen_date = datetime.strptime(date, "%d.%m")
    except ValueError:
        return None
    today = datetime.now().date()
    if chosen_date.date() < today:
        return None
    return chosen_date

async def validate_time(time: str) -> Optional[datetime]:
    try:
        chosen_time = datetime.strptime(time, "%H:%M")
    except ValueError:
        return None
    now = datetime.now()
    if chosen_time.time() < now.time():
        return None
    return chosen_time

async def validate_seats(seats: str) -> Optional[int]:
    if not seats.isdigit():
        return None
    return int(seats)