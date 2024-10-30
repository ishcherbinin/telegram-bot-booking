import csv
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(repr=True)
class Table:
    table_id: int
    capacity: int
    is_reserved: bool = False
    user_name: str = None

    def __str__(self):
        return (f"Table {self.table_id} with capacity {self.capacity} "
                f"is reserved: {self.is_reserved} by {self.user_name}")


class TablesStorage:

    def __init__(self, available_tables: Tuple[Dict[str, str], ...]):
        self._tables: Dict[str, Table] = {
            table["table_number"]: Table(table_id=int(table["table_number"]), capacity=int(table["capacity"]))
            for table in available_tables
        }

    def search_for_table(self, capacity: int) -> Optional[Table]:
        """
        Search for a table with a given capacity which is not reserved
        :param capacity:
        :return:
        """
        for table in self._tables.values():
            if table.capacity >= capacity and not table.is_reserved:
                return table
        return None

    @classmethod
    def from_csv_file(cls, file_path: str) -> 'TablesStorage':
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            available_tables = tuple(row for row in reader)
        return cls(available_tables)

