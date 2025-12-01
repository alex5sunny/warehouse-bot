import sqlite3
from pathlib import Path
from sqlite3 import Cursor
from typing import Any


def _get_devices(cursor: Cursor):
    cursor.execute("""
    SELECT devices.id, name, type_name, serial, room, user_name
    FROM devices JOIN type_links ON devices.id = type_links.device_id
    JOIN device_types ON type_links.type_id = device_types.id
    """)
    rows = cursor.fetchall()

    return [
        {k: row[k] for k in row.keys()} for row in rows
    ]


def _get_device(cursor: Cursor, device_id: int) -> dict[str, Any]:
    cursor.execute("""
    SELECT devices.id, name, type_name, serial, room, user_name
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
