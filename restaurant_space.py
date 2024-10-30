from dataclasses import dataclass
from typing import Dict, List, Optional


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

    def __init__(self, available_tables: List[Dict[str, str]]):
        self._tables: Dict[str, Table] = {
            table["table_number"]: Table(table_id=int(table["table_number"]), capacity=int(table["capacity"]))
            for table in available_tables
        }

    def search_for_table(self, capacity: int) -> Optional[Table]:
        for table in self._tables.values():
            if table.capacity >= capacity and not table.is_reserved:
                return table
        return None