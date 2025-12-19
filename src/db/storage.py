import datetime
import logging
import sqlite3
from pathlib import Path
from sqlite3 import Cursor
from typing import Any

from logger_config import setup_logger


logger = setup_logger(__file__, level=logging.DEBUG)


def _get_devices(cursor: Cursor):
    cursor.execute("""
    SELECT devices.id, name, type_name, inventory_n, room, user_name
    FROM devices JOIN type_links ON devices.id = type_links.device_id
    JOIN device_types ON type_links.type_id = device_types.id
    """)
    rows = cursor.fetchall()

    return [
        {k: row[k] for k in row.keys()} for row in rows
    ]


def _get_device(cursor: Cursor, device_id: int) -> dict[str, Any]:
    cursor.execute("""
    SELECT devices.id, name, type_name, inventory_n, room, user_name
    FROM devices JOIN type_links ON devices.id = type_links.device_id
    JOIN device_types ON type_links.type_id = device_types.id
    WHERE devices.id = ?
    """, (device_id,))
    row = cursor.fetchone()

    return {k: row[k] for k in row.keys()}


def _set_location(cursor: Cursor, device_id: int, location: str, user_name: str):
    cursor.execute(
        "UPDATE devices SET room = ?, user_name = ? WHERE devices.id = ?",
        (location, user_name, device_id)
    )


def _set_device_name(cursor: Cursor, device_id: int, name: str):
    cursor.execute(
        "UPDATE devices SET name = ? WHERE devices.id = ?",
        (name, device_id)
    )


def _set_device_inventory_n(cursor: Cursor, device_id: int, inventory_n: str):
    cursor.execute(
        "UPDATE devices SET inventory_n = ? WHERE devices.id = ?",
        (inventory_n, device_id)
    )


def _create_device(
    cursor: Cursor,
    name: str,
    inventory_n: str,
    type_name: str,
    user_name: str
):
    cursor.execute(
        "INSERT INTO devices (name, inventory_n, user_name) VALUES (?, ?, ?)",
        (name, inventory_n, user_name)
    )
    device_id = cursor.lastrowid
    cursor.execute(
        "SELECT id FROM device_types WHERE type_name = ?", (type_name,)
    )
    type_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO type_links (type_id, device_id) VALUES (?, ?)",
        (type_id, device_id)
    )


def get_devices(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        devices = _get_devices(cursor)
    return devices


def get_device(db_path: Path, device_id: int) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        return _get_device(cursor, device_id)


def set_location(dp_path: Path, device_id: int, location: str, user_name: str):
    with sqlite3.connect(dp_path) as conn:
        cursor = conn.cursor()
        _set_location(cursor, device_id, location, user_name)


def set_device_name(dp_path: Path, device_id: int, name: str):
    with sqlite3.connect(dp_path) as conn:
        cursor = conn.cursor()
        _set_device_name(cursor, device_id, name)


def set_inventory_n(dp_path: Path, device_id: int, inventory_n: str):
    with sqlite3.connect(dp_path) as conn:
        cursor = conn.cursor()
        _set_device_inventory_n(cursor, device_id, inventory_n)


def create_device(
        dp_path: Path,
        name: str,
        inventory_n: str,
        type_name: str,
        user_name: str | None = None
):
    with sqlite3.connect(dp_path) as conn:
        cursor = conn.cursor()
        _create_device(cursor, name, inventory_n, type_name, user_name)


def get_device_types(db_path: Path) -> list[str]:
    """Получает список всех типов устройств"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT type_name FROM device_types ORDER BY type_name")
        rows = cursor.fetchall()
        return [row[0] for row in rows]


def remove_device(db_path, device_id: int):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
        "DELETE FROM devices WHERE id = ?", (device_id,)
        )
        cursor.execute(
        "DELETE FROM type_links WHERE device_id = ?", (device_id,)
        )


def _insert_history_record(cursor: Cursor, device_id: int):
    cursor.execute(
        "INSERT INTO device_history "
        "(device_id, room, user_name, date_time) "
        "SELECT id, room, user_name, datetime('now', 'localtime') "
        "FROM devices "
        "WHERE id = ?",
        (device_id,)
    )


def insert_history_record(
        dp_path: Path,
        device_id: int
):
    with sqlite3.connect(dp_path) as conn:
        cursor = conn.cursor()
        _insert_history_record(cursor, device_id)


def get_device_history(db_path: Path, device_id: int, limit: int = 10):
    """Получает историю устройства"""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT room, user_name, date_time
            FROM device_history
            WHERE device_id = ?
            ORDER BY date_time DESC
            LIMIT ?
            """,
            (device_id, limit)
        )
        return cursor.fetchall()

