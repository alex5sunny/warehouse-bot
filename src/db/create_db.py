import random
import sqlite3
from pathlib import Path
from sqlite3 import Cursor

from globs import SRC_PATH
from logger_config import setup_logger


logger = setup_logger(__file__)


def create_db(db_path: Path, sql_path: Path):
    if db_path.exists():
        return
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            _create_db(cursor, sql_path)
            fill_db(cursor)
    except Exception as ex:
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
        {"name": "Dell XPS 13", "serial": "A1B2", "room": "Кабинет 101"},
        {"name": "MacBook Pro", "serial": "C3D4", "room": "Кабинет 205"},
        {"name": "Lenovo ThinkPad", "serial": "E5F6", "room": "Переговорная 3"},
        {"name": "HP EliteBook", "serial": "G7H8", "room": "Кабинет 101"},
        {"name": "Asus ZenBook", "serial": "I9J0", "room": "Кабинет 205"},
        {"name": "коробка", "serial": "ЛИС1", "room": "подвал"},
        {"name": "коробка", "serial": "ЛИС2", "room": "Луганск"},
        {"name": "коробка", "serial": "ЛИС3", "room": "Сенеж"},
        {"name": "коробка", "serial": "ЛИС4", "room": "Алабино"}
    ]

    for dev in devices:
        cursor.execute(
            "INSERT INTO devices (name, serial, room, user_name) VALUES (?, ?, ?, ?)",
            (dev['name'], dev['serial'], dev['room'], random.choice('Дима ДимаР Ярослав Степан'.split()))
        )

    for type_name in 'ноутбук коробка':
        cursor.execute(
            "INSERT INTO device_types (type_name) VALUES (?)",
            (type_name,)
        )

    cursor.execute(
        "INSERT INTO type_links"
        "SELECT 1, id from DEVICES WHERE device.name <> 'коробка'"
    )

    cursor.execute(
        "INSERT INTO type_links"
        "SELECT 2, id from DEVICES WHERE device.name = 'коробка'"
    )
