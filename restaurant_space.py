import csv
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass(repr=True)
class Table:
    table_id: int
    capacity: int
    is_reserved: bool = False
    booking_time: datetime = None
    user_name: str = None
    user_id: str = None

    def __str__(self):
        return (f"Table {self.table_id} with capacity {self.capacity} "
                f"is reserved: {self.is_reserved} by {self.user_name}")

    @property
    def readable_booking_time(self) -> str:
        return self.booking_time.strftime("%H:%M")

    @property
    def to_csv_row(self) -> Dict[str, str]:
        return {
            "table_id": str(self.table_id),
            "capacity": str(self.capacity),
            "is_reserved": str(self.is_reserved),
            "booking_time": self.readable_booking_time if self.booking_time else "",
            "user_name": self.user_name if self.user_name else ""
        }

@dataclass(repr=True)
class CalendarDate:
    business_date: date
    tables: Tuple[Table, ...] = tuple()

class TablesStorage:

    def __init__(self, available_tables: Tuple[Dict[str, str], ...]):
        self._tables: Dict[str, str] = {
            table["table_number"]: table["capacity"]
            for table in available_tables
        }
        self._calendar: Dict[date, CalendarDate] = {}
        
    def get_tables_for_date(self, business_date: date) -> Tuple[Table, ...]:
        """
        Get tables for a given business date adn return all of them
        :param business_date: 
        :return: 
        """
        if business_date not in self._calendar:
            # if it is first request for this date, all tables are available
            tables = tuple(Table(table_id=int(table_number), capacity=int(capacity))
                           for table_number, capacity in self._tables.items())
            self._calendar[business_date] = CalendarDate(business_date, tables)
        return self._calendar[business_date].tables

    @staticmethod
    def search_for_table(capacity: int, tables: Tuple[Table, ...]) -> Optional[Table]:
        """
        Search for a table with a given capacity which is not reserved
        :param tables: 
        :param capacity:
        :return:
        """
        # Filter tables that have at least the required capacity and are not reserved
        available_tables = [table for table in tables if table.capacity >= capacity and not table.is_reserved]

        # Sort tables by how closely their capacity matches the requested capacity
        if available_tables:
            best_table = min(available_tables, key=lambda t: t.capacity - capacity)
            return best_table
        return None

    @property
    def get_all_bookings(self) -> Dict[date, Tuple[Table, ...]]:
        return {date_info.business_date: date_info.tables for date_info in self._calendar.values()}

    @classmethod
    def from_csv_file(cls, file_path: str or Path) -> 'TablesStorage':
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            available_tables = tuple(row for row in reader)
        return cls(available_tables)


    def backup_to_csv_file(self, file_path: str or Path):
        with open(file_path, "w", encoding="utf-8") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=["date", "table_id", "capacity",
                                                "is_reserved", "booking_time", "user_name"])
            writer.writeheader()
            for date_info in self._calendar.values():
                for table in date_info.tables:
                    result = {"date": date_info.business_date.strftime("%d.%m.%Y"), **table.to_csv_row}
                    writer.writerow(result)

    def upload_backup_file(self, file: str or Path):
        with open(file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                business_date = datetime.strptime(row["date"], "%d.%m.%Y").date()
                if business_date not in self._calendar:
                    self._calendar[business_date] = CalendarDate(business_date)
                table = Table(table_id=int(row["table_id"]), capacity=int(row["capacity"]),
                              is_reserved=row["is_reserved"] == "True",
                              booking_time=datetime.strptime(row["booking_time"], "%H:%M") if row["booking_time"] else None,
                              user_name=row["user_name"])
                self._calendar[business_date].tables += (table,)