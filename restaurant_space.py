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

    def __str__(self):
        return (f"Table {self.table_id} with capacity {self.capacity} "
                f"is reserved: {self.is_reserved} by {self.user_name}")

    @property
    def readable_booking_time(self) -> str:
        return self.booking_time.strftime("%H:%M")

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

    @classmethod
    def from_csv_file(cls, file_path: str or Path) -> 'TablesStorage':
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            available_tables = tuple(row for row in reader)
        return cls(available_tables)

