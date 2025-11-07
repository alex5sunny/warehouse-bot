import sqlite3
from pathlib import Path
from sqlite3 import Cursor


def _get_devices(cursor: Cursor):
    cursor.execute("SELECT * FROM devices")
    rows = cursor.fetchall()

    return [
        {k: row[k] for k in row.keys()} for row in rows
    ]


def get_devices(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        devices = _get_devices(cursor)
    return devices

