import logging
import random
import sqlite3
from pathlib import Path
from sqlite3 import Cursor

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
    devices = [
        {"name": "Dell XPS 13", "inventory_n": "A1B2", "room": "Кабинет 101"},
        {"name": "MacBook Pro", "inventory_n": "C3D4", "room": "Кабинет 205"},
        {"name": "Lenovo ThinkPad", "inventory_n": "E5F6", "room": "Переговорная 3"},
        {"name": "HP EliteBook", "inventory_n": "G7H8", "room": "Кабинет 101"},
        {"name": "Asus ZenBook", "inventory_n": "I9J0", "room": "Кабинет 205"},
        {"name": "коробка", "inventory_n": "ЛИС1", "room": "подвал"},
        {"name": "коробка", "inventory_n": "ЛИС2", "room": "Луганск"},
        {"name": "коробка", "inventory_n": "ЛИС3", "room": "520л"},
        {"name": "коробка", "inventory_n": "ЛИС4", "room": "520р"}
    ]

    for dev in devices:
        cursor.execute(
            "INSERT INTO devices (name, inventory_n, room, user_name) VALUES (?, ?, ?, ?)",
            (dev['name'], dev['inventory_n'], dev['room'], random.choice('Дима ДимаР Ярослав Степан'.split()))
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
