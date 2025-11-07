import sqlite3


with sqlite3.connect('mydatabase.db') as conn:
    cursor = conn.cursor()

    # Create a table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    ''')

    # Insert data
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", ('Alice', 'alice@example.com'))
    cursor.execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com')")

with sqlite3.connect('mydatabase.db') as conn:
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
