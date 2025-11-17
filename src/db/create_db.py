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
        {"id": 1, "name": "Dell XPS 13", "serial": "A1B2", "room": "Кабинет 101"},
        {"id": 2, "name": "MacBook Pro", "serial": "C3D4", "room": "Кабинет 205"},
        {"id": 3, "name": "Lenovo ThinkPad", "serial": "E5F6", "room": "Переговорная 3"},
        {"id": 4, "name": "HP EliteBook", "serial": "G7H8", "room": "Кабинет 101"},
        {"id": 5, "name": "Asus ZenBook", "serial": "I9J0", "room": "Кабинет 205"}
    ]

    for dev in devices:
        cursor.execute(
            "INSERT INTO devices (name, serial, room) VALUES (?, ?, ?)",
            (dev['name'], dev['serial'], dev['room'])
        )
