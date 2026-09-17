import os, sqlite3

files = [f for f in os.listdir('.') if f.endswith(('.db', '.sqlite', '.sqlite3'))]
print('Found DB files:', files)

for f in files:
    print(f'\n--- {f} ---')
    try:
        conn = sqlite3.connect(f)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print('Tables:', tables)
    except Exception as e:
        print('Error:', e)
