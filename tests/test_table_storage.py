from typing import List, Dict

import pytest

from restaurant_space import Table, TablesStorage


@pytest.fixture(scope="module")
def table() -> Table:
    return Table(table_id=1, capacity=4)

@pytest.fixture(scope="module")
def available_tables() -> List[Dict[str, str]]:
    return [{"table_number": "1", "capacity": "4"},
            {"table_number": "2", "capacity": "2"}]

@pytest.fixture(scope="module")
def tables_storage(available_tables: List[Dict[str, str]]) -> TablesStorage:
    return TablesStorage(available_tables)


def test_search_for_table(tables_storage: TablesStorage, table: Table):
    assert tables_storage.search_for_table(4) == table, "Table with capacity 4 should be found"
    assert tables_storage.search_for_table(5) is None, "Table with capacity 5 should not be found"
    assert tables_storage.search_for_table(2) in [Table(table_id=2, capacity=2), table], "Table with capacity 2 or 4 is suitable"

