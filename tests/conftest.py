import os
from pathlib import Path
from typing import Tuple, Dict, Optional

import pytest

from restaurant_space import TablesStorage, Table

COMMON_PATH =  Path(os.path.dirname(__file__))

@pytest.fixture()
def table() -> Table:
    return Table(table_id=1, capacity=4)

@pytest.fixture()
def available_tables() -> Tuple[Dict[str, str], ...]:
    return ({"table_number": "1", "capacity": "4"},
            {"table_number": "2", "capacity": "2"},)

@pytest.fixture()
def tables_storage(available_tables: Tuple[Dict[str, str]]) -> TablesStorage:
    return TablesStorage(available_tables)

@pytest.fixture()
def tables_distribution_csv_file() -> Path:
    return COMMON_PATH / Path("test_tables.csv")

@pytest.fixture()
def backup_csv_file() -> Path:
    return COMMON_PATH / Path("backup_tables.csv")

@pytest.fixture()
def group_chat_id() -> Optional[int]:
    return int(os.getenv("GROUP_CHAT_ID"))

@pytest.fixture()
def personal_chat_id() -> Optional[int]:
    return int(os.getenv("TEST_CHAT_ID"))

@pytest.fixture()
def bot_token() -> str:
    return os.getenv("TELEGRAM_API_TOKEN")