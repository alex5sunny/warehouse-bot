import re
from pathlib import Path
import pandas as pd
from openpyxl import Workbook, load_workbook


def find_notebook_rows(input_dir="raw", output_file="out.xls"):
    """
    Читает все xls файлы из папки raw,
    ищет строки с 'ноутбук' в первом столбце,
    сохраняет их в out.xls
    """
    raw_dir = Path(input_dir)
    output_path = Path(output_file)

    # Регулярное выражение для поиска всех падежей слова "ноутбук"
    notebook_pattern = re.compile(r'ноутбук', re.IGNORECASE)

    # Список для хранения найденных строк
    found_rows = []

    # Перебираем все xls файлы в папке raw
    xls_files = list(raw_dir.glob("*.xls")) + list(raw_dir.glob("*.xlsx"))

    if not xls_files:
        print(f"Файлы .xls или .xlsx не найдены в папке {raw_dir}")
        return

    print(f"Найдено {len(xls_files)} файлов")

    for file_path in xls_files:
        print(f"Обработка файла: {file_path.name}")

        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, header=None)

            # Проверяем строки
            for idx, row in df.iterrows():
                if len(row) > 0 and pd.notna(row[0]):  # Проверяем первый столбец
                    first_cell = str(row[0])
                    if notebook_pattern.search(first_cell):
                        found_rows.append(row.tolist())

        except Exception as e:
            print(f"Ошибка при чтении файла {file_path.name}: {e}")
            continue

    if not found_rows:
        print("Строки с 'ноутбук' не найдены")
        return

    # Создаем новый Excel файл с найденными строками
    output_df = pd.DataFrame(found_rows)
    output_df.to_excel(output_path, index=False, header=False)

    print(f"\nГотово! Найдено {len(found_rows)} строк")
    print(f"Результат сохранен в {output_path.absolute()}")


if __name__ == "__main__":
    find_notebook_rows(input_dir='../raw', output_file='../out.xls')

