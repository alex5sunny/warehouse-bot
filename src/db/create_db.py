import logging
import random
import sqlite3
from pathlib import Path
from sqlite3 import Cursor

from globs import BASE_PATH
from logger_config import setup_logger


logger = setup_logger(__file__, level=logging.DEBUG)


def create_db(db_path: Path, sql_path: Path):
    db_exists = db_path.exists()
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            _create_db(cursor, sql_path)
            if not db_exists:
                fill_db(cursor)
    except Exception:
        logger.exception('cannot create db')
        if db_path.exists():
            db_path.unlink()
        raise


def _create_db(cursor: Cursor, sql_path):
    with open(sql_path , 'r', encoding='utf-8') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)


def fill_db(cursor: Cursor):
    devices = []
    with open(BASE_PATH / 'notebooks.csv', 'r') as file:
        for line_raw in file:
            if line := line_raw.strip():
                devices.append(line.split(','))
    for dev in devices:
        cursor.execute(
            "INSERT INTO devices (name, inventory_n, user_name) VALUES (?, ?, ?)",
            (dev[0], dev[1], 'Житнюк Алексей')
        )
    for type_name in 'ноутбук коробка'.split():
        # logger.debug(f'type_name:{type_name}')
        cursor.execute(
            "INSERT INTO device_types (type_name) VALUES (?)",
            (type_name,)
        )

    cursor.execute(
        "INSERT INTO type_links (type_id, device_id)"
        "SELECT 1, id from devices WHERE devices.name <> 'коробка'"
    )
    cursor.execute(
        "INSERT INTO type_links (type_id, device_id)"
        "SELECT 2, id from devices WHERE devices.name = 'коробка'"
    )
