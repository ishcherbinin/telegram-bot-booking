import os
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Tuple

import pytest

from restaurant_space import Table, TablesStorage

COMMON_PATH =  Path(os.path.dirname(__file__))

@pytest.fixture(scope="module")
def table() -> Table:
    return Table(table_id=1, capacity=4)

@pytest.fixture(scope="module")
def available_tables() -> Tuple[Dict[str, str], ...]:
    return ({"table_number": "1", "capacity": "4"},
            {"table_number": "2", "capacity": "2"},)

@pytest.fixture(scope="module")
def tables_storage(available_tables: Tuple[Dict[str, str]]) -> TablesStorage:
    return TablesStorage(available_tables)

@pytest.fixture(scope="module")
def test_tables_csv_file() -> Path:
    return COMMON_PATH / Path("test_tables.csv")

@pytest.fixture(scope="module")
def backup_csv_file() -> Path:
    return COMMON_PATH / Path("backup_tables.csv")

def test_date_tables_creation(tables_storage: TablesStorage):
    tables = tables_storage.get_tables_for_date(date.today())
    assert len(tables) == 2, "There should be 2 tables for today"

def test_search_for_table(tables_storage: TablesStorage, table: Table):
    business_date = date.today() + timedelta(days=1)
    tables = tables_storage.get_tables_for_date(business_date)
    assert tables_storage.search_for_table(4, tables) == table, "Table with capacity 4 should be found"
    assert tables_storage.search_for_table(5, tables) is None, "Table with capacity 5 should not be found"
    assert tables_storage.search_for_table(2, tables) in [Table(table_id=2, capacity=2), table], "Table with capacity 2 or 4 is suitable"

def test_from_csv_file(test_tables_csv_file: str):
    tables_storage = TablesStorage.from_csv_file(test_tables_csv_file)
    business_date = date.today() + timedelta(days=1)
    tables = tables_storage.get_tables_for_date(business_date)
    four_table = Table(table_id=1, capacity=4)
    assert tables_storage.search_for_table(4, tables) == four_table, "Table with capacity 4 should be found"
    assert tables_storage.search_for_table(6, tables) == Table(table_id=8, capacity=6), "Table with capacity 6 should be found"

def test_save_to_file(test_tables_csv_file: str, backup_csv_file: str):
    tables_storage = TablesStorage.from_csv_file(test_tables_csv_file)
    business_date = date.today() + timedelta(days=1)
    tables = tables_storage.get_tables_for_date(business_date)
    tables_storage.search_for_table(4, tables).is_reserved = True
    tables_storage.backup_to_csv_file(backup_csv_file)
    tables_storage = TablesStorage.from_csv_file(test_tables_csv_file)
    tables_storage.upload_backup_file(backup_csv_file)
    tables = tables_storage.get_tables_for_date(business_date)
    assert next(filter(lambda t: t.capacity == 4, tables), None).is_reserved, "Table with capacity 4 should be reserved"
    assert not tables_storage.search_for_table(6, tables).is_reserved, "Table with capacity 6 should not be reserved"