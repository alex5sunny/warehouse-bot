from db.create_db import create_db
from globs import DB_PATH, SRC_PATH


create_db(DB_PATH, SRC_PATH / 'sql' / 'create_schema.sql')
