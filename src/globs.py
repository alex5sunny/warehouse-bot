from pathlib import Path


TIMEOUT= 60


ADMINS: set[int] = {804930423}     # Дима 757787437    Ярослав 804930423


SRC_PATH = Path(__file__).parent
BASE_PATH = SRC_PATH.parent
DB_PATH = BASE_PATH / 'devices.db'
