CREATE TABLE IF NOT EXISTS device_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    serial TEXT NOT NULL UNIQUE,
    room TEXT
);

CREATE TABLE IF NOT EXISTS type_links (
    type_id INTEGER REFERENCES device_types(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    PRIMARY KEY (type_id, device_id)
);

-- INSERT INTO type_links (type_id, device_id)
-- SELECT 1, id
-- FROM devices;