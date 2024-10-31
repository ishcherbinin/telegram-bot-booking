from datetime import datetime
from typing import Optional


async def validate_date(date: str) -> Optional[datetime]:
    try:
        chosen_date = datetime.strptime(date, "%d.%m")
    except ValueError:
        return None
    return chosen_date