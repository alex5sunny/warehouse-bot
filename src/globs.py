from pathlib import Path


TIMEOUT= 60


SRC_PATH = Path(__file__).parent
BASE_PATH = SRC_PATH.parent
DB_PATH = BASE_PATH / 'devices.db'
